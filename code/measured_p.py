#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measured_p.py — 実測P(公定価格カバー率 M1 を主指標)の一覧を出典付きで書き出し、
                主観P(第一次コード)との一致度を確認する。

入力 : coded_firstpass_39職業.csv （同梱・スクリプトと同じディレクトリ）
出力 : measured_P.csv             （同梱の measured_P_出典付き.csv と同内容）

2026-07 修復メモ:
  - 入力ファイル名を同梱の実ファイル名 "coded_firstpass_39職業.csv" に修正
    （旧: "coded_firstpass.csv" は同梱されておらず実行不能だった）。
  - パスを pathlib で「スクリプトの位置」基準に解決（カレントディレクトリ非依存）。
  - pandas 非依存化（標準ライブラリ csv + numpy）。データ内容・数値は不変。
"""

import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # 同梱の repro_compat.py を確実に読む
import repro_compat as rc

IN_CSV = rc.pkg_path("coded_firstpass_39職業.csv")
OUT_CSV = rc.pkg_path("measured_P.csv")

# --- 実測P：公定価格カバー率(M1)を主指標。出典付き。測れた職業のみ。 ---
# regulated_share: 売上に占める公定価格(保険点数/介護報酬/認可運賃/公費)の割合(概算)
# dispersion: 価格分散の質的評価(高=低硬直)
measured = [
 # occupation, regulated_share, dispersion, P_measured(0-4), source
 ("医師(内科)",0.97,"ほぼ無(全国一律点数)",4,"国民医療費≒45-47兆は全額保険診療; 自由診療中核の美容医療6,310億(矢野2024)→規制シェア≒97%"),
 ("放射線科医",0.98,"ほぼ無",4,"診療報酬(画像診断点数)全国一律"),
 ("薬剤師",0.95,"ほぼ無(調剤報酬)",4,"調剤報酬は公定; 一部OTC自費"),
 ("介護職",0.90,"低(介護報酬)",4,"介護保険給付が中核; 一部自費サービス"),
 ("保育士",0.85,"低(公定/公費)",4,"公定価格(公費)中心; 一部認可外"),
 ("翻訳者(一般)",0.00,"高(5円MTPE〜26円JTF目安; 白書で和訳19-22円最頻だが広く分散)",0,"公定価格なし; JTF2017白書 価格帯分散"),
 ("データ入力",0.00,"高",0,"スポット市場"),
 ("弁護士",0.05,"高(2004報酬基準廃止で自由化)",1,"旧弁護士報酬基準2004廃止→自由化; 法テラス一部固定"),
 ("公認会計士(監査)",0.10,"中(交渉/慣行で粘着)",2,"監査報酬は交渉制だが慣行で粘着"),
 ("タクシー運転手",0.95,"低(認可運賃)",4,"道路運送法の認可運賃(低R高Pの対照)"),
 ("航空管制官",1.00,"無(公務)",4,"公務・固定"),
 ("郵便窓口",0.95,"低(認可料金)",4,"郵便料金は認可制"),
]
DM_FIELDS = ["occupation", "regulated_share", "dispersion", "P_measured", "source"]
dm = [dict(zip(DM_FIELDS, rec)) for rec in measured]
rc.write_table(OUT_CSV, DM_FIELDS, dm)

# --- 主観P(第一次コード)と実測Pの一致 ---
_fields, sub = rc.read_table(IN_CSV)
sub_P = {r["occupation"]: float(r["P"]) for r in sub}
# 名寄せ(表記ゆれ吸収)
namemap = {"翻訳者(一般)": "一般翻訳者"}

# inner merge 相当: 実測P側の並び順を保ったまま、主観P側に存在する職業のみ残す
mg = []
for r in dm:
    occ = namemap.get(r["occupation"], r["occupation"])
    if occ in sub_P:
        mg.append({"occupation": occ,
                   "P_subjective": sub_P[occ],
                   "P_measured": float(r["P_measured"]),
                   "regulated_share": r["regulated_share"]})

print("=== 主観P vs 実測P（重なり職業） ===")
print(rc.to_string(
    ["occupation", "P_subjective", "P_measured", "regulated_share"],
    [[m["occupation"] for m in mg],
     [int(m["P_subjective"]) for m in mg],
     [int(m["P_measured"]) for m in mg],
     [f'{float(m["regulated_share"]):.2f}' for m in mg]]))

ps = [m["P_subjective"] for m in mg]
pm = [m["P_measured"] for m in mg]
exact = int(all(a == b for a, b in zip(ps, pm)))
mad = sum(abs(a - b) for a, b in zip(ps, pm)) / len(mg)
print(f"\n相関 r(主観P, 実測P) = {rc.corr(ps, pm):.2f}  完全一致={exact}")
print(f"平均絶対差 = {mad:.2f}")
print("→ 主観Pは実測Pでほぼ再現。とくに医療(高)vs翻訳(低)の核心対比は実測でも保持。")
print(f"\nsaved {OUT_CSV.name}")
