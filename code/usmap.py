#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
usmap.py — 米BLS OOH 341職業に R/P を規則ベースで付与し、Φ(AI曝露)×Ψ(摩擦)で
           雇用量重み付き分解を行う。

入力 : us341_BLS_PhiPsi.csv （同梱・スクリプトと同じディレクトリ）
       ※ 元の実行時の入力は data.json（BLS OOH スクレイプ結果）だったが、
         そのファイルは本パッケージに同梱されていない。同梱の
         us341_BLS_PhiPsi.csv は本スクリプトの出力であり、入力に必要な列
         (title, category, exposure, jobs) をすべて含むため、再現用の
         入力としてそのまま利用できる。R/P/Phi/Psi は下の関数で再計算され、
         同梱値と一致するか自動検証される（--verify、既定で ON）。
出力 : us341_phipsi.csv （スクリプトと同じディレクトリ）

2026-07 修復メモ:
  - 入力の Linux 固定パス 絶対パスの data.json を廃止し、
    同梱 CSV をスクリプト位置基準で読むよう変更。
  - 出力の Linux 固定パス 絶対パスの出力CSV を
    スクリプト位置基準に変更。
  - pandas 非依存化（標準ライブラリ csv + numpy）。スコア規則・しきい値は不変。
"""

import re

import numpy as np

import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # 同梱の repro_compat.py を確実に読む
import repro_compat as rc

IN_CSV = rc.pkg_path("us341_BLS_PhiPsi.csv")
OUT_CSV = rc.pkg_path("us341_phipsi.csv")

_fields, rows = rc.read_table(IN_CSV)
for x in rows:
    x['jobs'] = float(x.get('jobs') or 0)
    x['exposure'] = float(x.get('exposure') or 0)
rows = [x for x in rows if x['jobs'] > 0]


def score_R(t,cat):
    t=t.lower()
    life=r'physician|surgeon|dentist|nurse|anesthesi|pharmacist|paramedic|emergency medical|physical therap|occupational therap|respiratory therap|psychiatr|psycholog|veterinar|optometr|podiatr|chiropract|midwi|physician assistant|nurse practitioner|dental hygien|radiat|nuclear medicine|perfusion'
    pilot=r'airline pilot|aircraft pilot|air traffic'
    safety=r'police|firefighter|fire fighter|detective|sheriff'
    lic3=r'lawyer|judge|magistrate|accountant|auditor|engineer|architect|actuar|appraiser|surveyor|dietitian|financial examiner|financial advisor|financial manager|loan officer'
    child=r'childcare|child care|preschool|kindergarten'
    teach=r'teacher|professor|instructor|education'
    socw=r'social worker|counselor|therapist|clergy'
    if re.search(life,t) or re.search(pilot,t) or re.search(safety,t): return 4
    if cat=='protective-service': return 4
    if re.search(child,t): return 3
    if re.search(lic3,t) or re.search(teach,t) or re.search(socw,t): return 3
    if cat in ('legal','business-and-financial','architecture-and-engineering','education-training-and-library','community-and-social-service'): return 3
    if cat in ('computer-and-information-technology','life-physical-and-social-science','management'): return 2
    if re.search(r'technician|inspector|paralegal|insurance|real estate|manager',t): return 2
    if cat in ('media-and-communication','arts-and-design','sales'): return 1
    return 0

def score_P(t,cat):
    t=t.lower()
    if cat=='healthcare': return 4
    if cat in ('education-training-and-library','protective-service','community-and-social-service'): return 4   # public/regulated funding
    if re.search(r'postal|transit|air traffic|airline pilot',t): return 4
    if cat=='legal': return 2          # US legal fees market-set but sticky
    if cat in ('business-and-financial',): return 2
    if cat in ('architecture-and-engineering','management'): return 2
    if cat in ('construction-and-extraction','installation-maintenance-and-repair','production',
               'transportation-and-material-moving','farming-fishing-and-forestry'): return 1
    if cat in ('sales','food-preparation-and-serving','personal-care-and-service','arts-and-design',
               'media-and-communication','building-and-grounds-cleaning','office-and-administrative-support',
               'computer-and-information-technology','math','entertainment-and-sports','life-physical-and-social-science'): return 1
    return 1

# --- 再計算前の同梱値（検証用に退避） ---
_shipped = [(x.get('R'), x.get('P'), x.get('Phi'), x.get('Psi')) for x in rows]

for x in rows:
    x['R']=score_R(x['title'],x['category']); x['P']=score_P(x['title'],x['category'])
    x['Phi']=x['exposure']/10.0
    x['Psi']=(x['R']/4.0)*(x['P']/4.0)

# --- 同梱の R/P/Phi/Psi と再計算値が一致するか検証（分析ロジック不変の確認） ---
_bad = [x['title'] for x, s in zip(rows, _shipped)
        if s[0] not in (None, '') and not (
            int(s[0]) == x['R'] and int(s[1]) == x['P']
            and abs(float(s[2]) - x['Phi']) < 1e-9 and abs(float(s[3]) - x['Psi']) < 1e-9)]
print(f"[verify] 同梱CSVの R/P/Phi/Psi と再計算値の不一致: {len(_bad)} 件"
      + (f" 例: {_bad[:5]}" if _bad else " (完全一致)"))

jobs = np.array([x['jobs'] for x in rows], dtype=float)
Phi = np.array([x['Phi'] for x in rows], dtype=float)
Psi = np.array([x['Psi'] for x in rows], dtype=float)
J = jobs.sum()
def share(mask): return jobs[mask].sum()/J*100
hiPhi=Phi>=0.7      # exposure>=7 (Karpathy's "high")
hiPsi=Psi>=0.40     # R,P both reasonably high (e.g. R3*P3=0.5625, R4*P2=0.5, R3*P2=0.375 borderline)
print("=== 雇用量重み付き Φ×Ψ 分解（米 143M jobs）===")
print(f"総雇用 {J/1e6:.0f}M")
print(f"  高Φ高Ψ（監督ボトルネック: reshaped-not-replaced）: {share(hiPhi&hiPsi):5.1f}%  {jobs[hiPhi&hiPsi].sum()/1e6:5.1f}M")
print(f"  高Φ低Ψ（置換・単価下落の圧力）              : {share(hiPhi&~hiPsi):5.1f}%  {jobs[hiPhi&~hiPsi].sum()/1e6:5.1f}M")
print(f"  低Φ高Ψ（人間中心で残存）                    : {share(~hiPhi&hiPsi):5.1f}%")
print(f"  低Φ低Ψ（変化小）                            : {share(~hiPhi&~hiPsi):5.1f}%")
hi_jobs = jobs[hiPhi]; hi_psi = Psi[hiPhi]
print(f"\n高Φ(exposure>=7)の雇用 {hi_jobs.sum()/1e6:.0f}M のうち:")
print(f"  高Ψ(摩擦で閉じ込め): {hi_jobs[hi_psi>=0.40].sum()/hi_jobs.sum()*100:4.1f}%")
print(f"  低Ψ(置換圧力)      : {hi_jobs[hi_psi<0.40].sum()/hi_jobs.sum()*100:4.1f}%")
print("\n高Φ高Ψ セルの代表職業(雇用順):")
top = sorted([x for x in rows if x['Phi'] >= 0.7 and x['Psi'] >= 0.40],
             key=lambda x: x['jobs'], reverse=True)[:10]
print(rc.to_string(["title", "exposure", "R", "P", "jobs"],
                   [[x['title'] for x in top],
                    [int(x['exposure']) for x in top],
                    [x['R'] for x in top],
                    [x['P'] for x in top],
                    [int(x['jobs']) for x in top]]))

out_fields = list(_fields)
out_rows = []
for x in rows:
    r = dict(x)
    r['jobs'] = int(x['jobs']) if float(x['jobs']).is_integer() else x['jobs']
    r['exposure'] = int(x['exposure']) if float(x['exposure']).is_integer() else x['exposure']
    out_rows.append(r)
rc.write_table(OUT_CSV, out_fields, out_rows)
print(f"\nsaved {OUT_CSV.name}")
