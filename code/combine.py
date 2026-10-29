#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
combine.py — 第一次コード(B,R,P)に A(業種別生成AI導入率の代理)と実測Pを結合し、
             R-P共線性と因子構造(Kaiser基準)を確認して統合CSVを書き出す。

入力 : coded_firstpass_39職業.csv   （同梱・スクリプトと同じディレクトリ）
出力 : coded_with_A_measuredP.csv   （同梱の coded_full_A_measuredP_39職業.csv と同内容）

2026-07 修復メモ:
  - 入力ファイル名を同梱の実ファイル名 "coded_firstpass_39職業.csv" に修正
    （旧: "coded_firstpass.csv" は同梱されておらず実行不能だった）。
  - パスを pathlib で「スクリプトの位置」基準に解決（カレントディレクトリ非依存）。
  - pandas 非依存化（標準ライブラリ csv + numpy）。分析ロジック・数値は不変。
"""

import numpy as np
from sklearn.preprocessing import StandardScaler

import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # 同梱の repro_compat.py を確実に読む
import repro_compat as rc

IN_CSV = rc.pkg_path("coded_firstpass_39職業.csv")
OUT_CSV = rc.pkg_path("coded_with_A_measuredP.csv")

fields, rows = rc.read_table(IN_CSV)
occupation = rc.col_str(rows, "occupation")

# A: 業種別生成AI導入率の代理(0-4)。JUAS2025(社会インフラ60.8,金融保険54.4),情報通信白書,PwC2025等に基づく粗いマッピング。
Amap={"一般PG":4,"ジュニア開発":4,"サイバー監査":4,"金融コンプラ":4,"独立FP/投資助言":3,
 "一般翻訳者":4,"法務医療翻訳":3,"コピーライター":4,"データ入力":3,"文字起こし":3,"パラリーガル":3,"一般事務":2,
 "弁護士":3,"公認会計士(監査)":3,"税理士":3,"弁理士":3,
 "医師(内科)":2,"放射線科医":2,"外科医":1,"麻酔科医":1,"薬剤師":2,"看護師":2,
 "構造設計士":2,"小学校教員":2,"医療通訳":3,"獣医師":2,
 "介護職":1,"保育士":1,"救急救命士":1,"航空管制官":2,"公共料金事務":2,"郵便窓口":1,"美容師":1,
 "倉庫作業員":1,"清掃員":1,"飲食サービス":1,"警備員":1,"建設作業員":1,"配送ドライバー":1}
A_list = [Amap.get(o) for o in occupation]
_missing = [o for o, a in zip(occupation, A_list) if a is None]
assert not _missing, _missing

# 実測Pで置換(取得済み職業のみ)
Pmeas={"医師(内科)":4,"放射線科医":4,"薬剤師":4,"介護職":4,"保育士":4,"一般翻訳者":0,"データ入力":0,
 "弁護士":1,"公認会計士(監査)":2,"航空管制官":4,"郵便窓口":4}
P_measured = np.array([np.nan if Pmeas.get(o) is None else float(Pmeas[o])
                       for o in occupation], dtype=float)

A = np.array(A_list, dtype=float)
B = rc.col_float(rows, "B")
R = rc.col_float(rows, "R")
P = rc.col_float(rows, "P")
P_used = np.where(np.isnan(P_measured), P, P_measured)  # 実測あれば実測、無ければ主観

print("=== R-P 共線性: 主観P vs 実測P置換 ===")
print(f"  主観Pのみ          : r(R,P) = {rc.corr(R, P):.2f}")
print(f"  実測P置換(11職業)   : r(R,P_used) = {rc.corr(R, P_used):.2f}")
print("  → 弁護士・会計士のP低下で高R低Pセルが増え、共線性がさらに緩む")

DATA = {"A": A, "B": B, "R": R, "P": P, "P_used": P_used}


def kaiser(data, cols):
    Z = StandardScaler().fit_transform(np.column_stack([data[c] for c in cols]))
    C = np.corrcoef(Z.T); ev = np.sort(np.linalg.eigvalsh(C))[::-1]
    return ev, int((ev > 1).sum()), C


print("\n=== 因子構造: A を追加 ===")
for label, pcol in [("主観P", "P"), ("実測P置換", "P_used")]:
    cols = ["A", "B", "R", pcol]
    ev, nf, C = kaiser(DATA, cols)
    print(f"\n[{label}] 固有値={np.round(ev,2)}  Kaiser因子数={nf} "
          f"-> {'OK(多次元)' if nf>=2 else '一因子(警告)'}")
    print(rc.matrix_to_string(cols, np.round(C, 2)))

# 因子の中身(主成分負荷)を実測P版で
from numpy.linalg import eigh
cols = ["A", "B", "R", "P_used"]
Z = StandardScaler().fit_transform(np.column_stack([DATA[c] for c in cols]))
C = np.corrcoef(Z.T); w, v = eigh(C); idx = np.argsort(w)[::-1]
load = v[:, idx[:2]] * np.sqrt(w[idx[:2]])
print("\n主成分負荷(実測P版, 上位2因子):")
print(rc.to_string(["PC1", "PC2"],
                   [[f"{load[i][0]:.2f}" for i in range(len(cols))],
                    [f"{load[i][1]:.2f}" for i in range(len(cols))]],
                   index=cols))

out_fields = fields + ["A", "P_measured", "P_used"]
out_rows = []
for i, r in enumerate(rows):
    row = dict(r)
    row["A"] = A_list[i]
    row["P_measured"] = rc.fnum(P_measured[i])
    row["P_used"] = rc.fnum(P_used[i])
    out_rows.append(row)
rc.write_table(OUT_CSV, out_fields, out_rows)
print(f"\nsaved {OUT_CSV.name}")
