#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h5_natexp.py — 自然実験(不妊治療の2022/4保険適用 = Pショック)の図を生成する。

入力 : なし（数値はスクリプト内に直書き。出典は README_REPRODUCTION.md 参照）
出力 : h5_natexp.png / h5_natexp.pdf （スクリプトと同じディレクトリ）

2026-07 修復メモ:
  - Linux 固有のフォント絶対パス
    '/usr/share/fonts/opentype/noto/NotoSansCJK-{Regular,Bold}.ttc'
    への依存を廃止。repro_compat.jp_font_pair() が matplotlib の
    フォント一覧から日本語フォントを実行時に自動探索し、
    見つからない場合は警告のうえ英語ラベルにフォールバックする。
  - 出力をスクリプト位置基準の絶対パスに変更（カレントディレクトリ非依存）。
  - 数値・系列・乱数シードは一切変更していない（図の内容は同一）。
"""

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # 同梱の repro_compat.py を確実に読む
import repro_compat as rc

OUT_PNG = rc.pkg_path("..", "figures", "h5_natexp.png")
OUT_PDF = rc.pkg_path("..", "figures", "h5_natexp.pdf")

# --- 日本語フォント自動探索（無ければ英語ラベルにフォールバック） ---
fp, fpb = rc.jp_font_pair()
JP = fp is not None


def L(ja, en):
    """日本語フォントがあれば日本語、無ければ英語ラベルを返す。"""
    return ja if JP else en


# fontproperties=None は matplotlib のデフォルトフォントを意味する
FP = {'fontproperties': fp} if JP else {}
FPB = {'fontproperties': fpb} if JP else {}

plt.rcParams['axes.unicode_minus']=False

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(12.4,5.4),gridspec_kw={'width_ratios':[1.35,1]})

# --- Panel A: ART出生児(一貫系列) と 総治療周期 ---
yr=np.array([2018,2019,2020,2021,2022,2023])
births=np.array([56979,60598,60381,69797,77206,85048])  # ART出生児; 2018-20は厚労省/日産婦概数, 2021-23は確報
solid=np.array([0,0,0,1,1,1],bool)
ax1.plot(yr,births,'-o',color='#993C1D',lw=2.4,ms=6,zorder=3)
# 概数区間を薄く
ax1.plot(yr[:3],births[:3],'o',color='white',ms=6,markeredgecolor='#993C1D',zorder=4)
ax1.axvspan(2017.5,2020.6,color='#888',alpha=0.06)
ax1.text(2019,52000,L("保険適用前\n（自由診療, P≈0）\n価格は分散・横ばい",
                      "Before coverage\n(free-priced, P$\\approx$0)\ndispersed & flat prices"),
         fontsize=9,color='#555',ha='center',**FP)
ax1.axvline(2022,color='#185FA5',lw=1.6,ls='--',zorder=2)
ax1.text(2022.05,58000,L("2022/4 保険適用\n（公定価格, P≈1）",
                         "Apr 2022 insurance coverage\n(administered price, P$\\approx$1)"),
         fontsize=9.5,color='#185FA5',ha='left',**FPB)
ax1.axvline(2021,color='#aaa',lw=1,ls=':',zorder=1)
ax1.text(2021.02,86500,L("2021 助成拡充","2021 subsidy expansion"),
         fontsize=8,color='#888',ha='left',**FP)
for x,y,s in zip(yr,births,solid):
    ax1.annotate(f"{y:,}",(x,y),fontsize=8,xytext=(0,8),
                 textcoords='offset points',ha='center',color='#993C1D' if s else '#999',**FP)
ax1.set_xlabel(L("年","Year"),fontsize=11,**FP)
ax1.set_ylabel(L("ART出生児数（人）","ART live births"),fontsize=11,**FP)
ax1.set_title(L("不妊治療(ART)：保険適用(Pショック)前後の需要",
                "ART: demand around the 2022 insurance-coverage (P) shock"),fontsize=12,**FPB)
ax1.set_ylim(48000,92000); ax1.grid(alpha=0.12)
if JP:
    for t in ax1.get_xticklabels()+ax1.get_yticklabels(): t.set_fontproperties(fp)
ax1.text(2018,90000,L("●確報(日産婦) ○概数","● final (JSOG)  ○ provisional"),
         fontsize=8,color='#777',**FP)

# --- Panel B: 価格分散 自由診療 vs 保険 (模式) ---
np.random.seed(3)
free=np.random.normal(45,12,60); free=np.clip(free,20,80)   # 自由診療: 20-80万/回, 分散大
ins=np.random.normal(15,0.4,60)                              # 保険(3割負担+公定): ほぼ一点
ax2.scatter(np.random.uniform(0.7,1.3,60),free,s=14,color='#D85A30',alpha=0.6,
            label=L('自由診療(〜2022/3)','free-priced (–2022/3)'))
ax2.scatter(np.random.uniform(1.7,2.3,60),ins,s=14,color='#185FA5',alpha=0.7,
            label=L('保険診療(2022/4〜)','insured (2022/4–)'))
ax2.set_xticks([1,2])
ax2.set_xticklabels(L(["自由診療\nP≈0","保険診療\nP≈1"],
                      ["free-priced\nP$\\approx$0","insured\nP$\\approx$1"]),fontsize=10,**FP)
ax2.set_ylabel(L("体外受精 1周期あたり費用（万円, 模式）",
                 "IVF cost per cycle (10k JPY, schematic)"),fontsize=10,**FP)
ax2.set_title(L("価格分散の消滅（公定価格化）",
                "Collapse of price dispersion (administered pricing)"),fontsize=12,**FPB)
ax2.set_ylim(0,85); ax2.grid(alpha=0.12,axis='y')
ax2.annotate(L("分散大\n(CV高)","high dispersion\n(high CV)"),(1,68),
             fontsize=9,color='#993C1D',ha='center',**FP)
ax2.annotate(L("ほぼ一点\n(CV≈0)","near-degenerate\n(CV$\\approx$0)"),(2,26),
             fontsize=9,color='#185FA5',ha='center',**FP)
if JP:
    for t in ax2.get_yticklabels(): t.set_fontproperties(fp)
plt.tight_layout(); plt.savefig(OUT_PNG,dpi=160); plt.savefig(OUT_PDF)
print(f"saved {OUT_PNG.name}/{OUT_PDF.name}")
print("births 2020->2023: %d -> %d (+%.0f%%)"%(births[2],births[5],100*(births[5]/births[2]-1)))
