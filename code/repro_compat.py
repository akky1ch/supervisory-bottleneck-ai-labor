#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repro_compat.py — 再現パッケージ用の共通ユーティリティ（2026-07 修復時に追加）

目的:
  - 実行環境に pandas が無い場合でも同じ分析結果を再現できるよう、
    本パッケージのスクリプトが使っていた pandas の機能のうち
    「CSV 入出力 / 相関 / 表の文字列整形」だけを標準ライブラリ + numpy で置き換える。
  - OS 依存パス（Linux 固定パス）を排除し、スクリプト位置基準の相対パス解決を提供する。
  - 日本語フォントを実行時に自動探索し、無ければ英語ラベルへフォールバックする仕組みを提供する。

注意: 分析ロジック（スコア定義・しきい値・計算式）は一切変更していない。
"""

from __future__ import annotations

import csv
import math
import sys
import warnings
from pathlib import Path

import numpy as np

# --- スクリプト位置基準のパス解決 -------------------------------------------

#: このファイル（= データパッケージ）が置かれているディレクトリ
PKG_DIR = Path(__file__).resolve().parent.parent / "data"  # リポジトリ構成: code/ と data/ を分離


def pkg_path(*parts) -> Path:
    """パッケージ同梱ファイルへの絶対パスを、スクリプト位置基準で返す。"""
    return PKG_DIR.joinpath(*parts)


# --- CSV 入出力（pandas.read_csv / to_csv の最小互換） ----------------------

def read_table(path):
    """CSV を読み、(列名リスト, 行=dict のリスト) を返す。値は文字列のまま。"""
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [dict(r) for r in reader]
        fields = list(reader.fieldnames or [])
    return fields, rows


def write_table(path, fields, rows):
    """
    pandas.to_csv(index=False) と同じ体裁（LF 改行 / 最小クォート / UTF-8）で書き出す。
    rows は dict のリストでも、値のリストのリストでもよい。
    """
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(fields)
        for r in rows:
            if isinstance(r, dict):
                w.writerow([r[f] for f in fields])
            else:
                w.writerow(list(r))


def fnum(x):
    """pandas が float 列を CSV に書くときの体裁（NaN は空欄、4 -> '4.0'）。"""
    if x is None:
        return ""
    x = float(x)
    if math.isnan(x):
        return ""
    return repr(x)


def col_float(rows, name):
    """列を float の numpy 配列として取り出す（空欄は NaN）。"""
    out = []
    for r in rows:
        v = r[name]
        out.append(np.nan if v is None or v == "" else float(v))
    return np.asarray(out, dtype=float)


def col_str(rows, name):
    return [r[name] for r in rows]


# --- 統計 -------------------------------------------------------------------

def corr(x, y):
    """pandas.Series.corr と同じ Pearson 相関（NaN ペアは除外）。"""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 2:
        return float("nan")
    return float(np.corrcoef(x[m], y[m])[0, 1])


# --- 表の文字列整形（pandas.DataFrame.to_string の最小互換） ----------------

def _adjoin(strcols):
    """列（文字列リスト）を 1 スペース区切りで連結する（pandas の adjoin(1) 相当）。"""
    nrow = max(len(c) for c in strcols)
    lines = []
    for i in range(nrow):
        lines.append(" ".join(c[i] for c in strcols))
    return "\n".join(line.rstrip() if False else line for line in lines)


def to_string(headers, columns, index=None):
    """
    headers : 列名のリスト
    columns : 各列の値（文字列）のリスト
    index   : 行ラベルのリスト（None なら pandas の index=False 相当）

    pandas は数値セルの前に 1 スペースを入れてから列幅で右詰めするため、
    ここでも同じ体裁（値に先頭スペース付与 -> 右詰め）にしている。
    """
    strcols = []
    if index is not None:
        w = max([len("")] + [len(str(v)) for v in index])
        strcols.append([" " * w] + [str(v).ljust(w) for v in index])
    for h, vals in zip(headers, columns):
        cells = [" " + str(v) for v in vals]
        w = max([len(h)] + [len(c) for c in cells])
        strcols.append([h.rjust(w)] + [c.rjust(w) for c in cells])
    return _adjoin(strcols)


def matrix_to_string(labels, mat, ndigits=2):
    """相関行列などの正方行列を pandas 風に文字列化する。"""
    cols = []
    for j in range(len(labels)):
        cols.append([f"{mat[i][j]:.{ndigits}f}" for i in range(len(labels))])
    return to_string(list(labels), cols, index=list(labels))


# --- 日本語フォントの自動探索（OS 非依存） ----------------------------------

#: 探索対象の日本語フォントファミリ名（優先順）
JP_FONT_CANDIDATES = [
    "Noto Sans CJK JP", "Noto Sans JP", "Noto Serif CJK JP",
    "Source Han Sans JP", "IPAexGothic", "IPAPGothic", "IPAGothic",
    "Yu Gothic", "YuGothic", "Meiryo", "MS Gothic", "MS PGothic",
    "Hiragino Sans", "Hiragino Kaku Gothic Pro", "Hiragino Maru Gothic Pro",
    "TakaoPGothic", "VL PGothic", "Migu 1P", "Osaka",
]


def find_japanese_font(verbose=True):
    """
    matplotlib が認識しているフォントから日本語フォントを探す。
    見つかれば FontProperties(family=...) を返し、見つからなければ
    警告を出して None を返す（呼び出し側は英語ラベルにフォールバックする）。
    """
    from matplotlib import font_manager as fm

    available = {f.name for f in fm.fontManager.ttflist}
    for name in JP_FONT_CANDIDATES:
        if name in available:
            if verbose:
                print(f"[font] 日本語フォントを使用: {name}", file=sys.stderr)
            return fm.FontProperties(family=name)

    # 名前一致で見つからない場合、CJK/Gothic/Mincho を含むファミリ名を総当たり
    for f in sorted(available):
        low = f.lower()
        if any(k in low for k in ("cjk", "gothic", "mincho", "meiryo", "hiragino")):
            if verbose:
                print(f"[font] 日本語フォント（推定一致）を使用: {f}", file=sys.stderr)
            return fm.FontProperties(family=f)

    warnings.warn(
        "日本語フォントが見つかりませんでした。図のラベルは英語にフォールバックします。"
        " 日本語表示が必要な場合は Noto Sans CJK JP / IPAexGothic 等をインストールしてください。",
        RuntimeWarning,
    )
    return None


def jp_font_pair(verbose=True):
    """(通常, 太字) の FontProperties を返す。日本語フォント不在時は (None, None)。"""
    fp = find_japanese_font(verbose=verbose)
    if fp is None:
        return None, None
    from matplotlib import font_manager as fm
    fpb = fm.FontProperties(family=fp.get_family()[0], weight="bold")
    return fp, fpb
