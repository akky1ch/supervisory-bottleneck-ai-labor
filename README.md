# 知能の民主化と労働市場再編 — 監督ボトルネックが成立する条件

**The Democratization of Intelligence and Labor-Market Restructuring: Conditions for a Supervisory Bottleneck**

> 有限の監督供給の下でAI普及が労働負荷へ転嫁される制度条件  
> Working Paper, v12 (2026). 未定稿。引用・配布の際はその旨を明記してください。コメント・Issue を歓迎します。

📄 **論文 PDF:** [`paper/main.pdf`](paper/main.pdf)

## 要旨 (Abstract)

AI利用と労働時間の関係について、既存の実証研究は割れている。米国の生活時間日誌を用いた研究はAI曝露が高い職業ほど労働時間が長いと報告し（Jiang et al., 2025）、デンマークの行政記録を用いた研究は賃金・労働時間のいずれにも精密なゼロを報告する（Humlum and Vestergaard, 2025）。本稿は、この対立が*制度条件の違い*として整合的に説明できることを示す。すなわち、AI普及が専門職の労働負荷へ転嫁される*条件*を理論的に定式化する。中核は一本の式である：一人当たり監督時間の弾力性は、需要拡大が有資格者数の調整を上回る力 $\delta(P)=\alpha-\varepsilon_N(P)$ と、AIが一件あたり人間監督時間を削る速さ $\eta(x;R)$ との差で決まる。責任制約 $R$ は一件あたり監督時間の*床* $s_{\min}(R)>0$ として、価格硬直性 $P$ は有資格者数の非弾力性 $\varepsilon_N(P)$ として入る。監督ボトルネックが成立するには、有資格者数が制度的に制限され、かつ一人当たり時間に上限 $\bar T$ が存在することが不可欠であり、監督労働を任意量調達できる定式化では当該現象はそもそも生じない。本稿の主要な貢献は、この条件を明示することで、*監督負荷の増加が五つの調整マージン（単価低下・頭数増・時間増・賃金上昇・待ち行列と品質低下）のうち一つに過ぎず、複数の制度条件が同時に満たされる場合に限られる*ことを示した点にある。この境界条件は、価格と労働時間が柔軟な環境を対象とした無作為化実験がAI利用による労働時間の減少を報告していることと整合的である。逆に、単価が公定され有資格供給が非弾力的な環境（米国外来医療）では、環境AI記録の導入により一件あたり記録時間が約10%減少したにもかかわらず、勤務時間外労働は変わらず*外来件数が増加*している（Rotenstein et al., 2026）。同一の技術が制度条件に応じて異なるマージンへ吸収されるという本稿の主張と整合する。実証部は日本の専門職統計・GPT曝露スコア・公開データによる*記述的・探索的*分析に留まり、中心命題の検証ではない。公開集計による予備的な系列分析では、生成AI普及に固有のトレンド変化は検出できなかった。他方、AI利用の職業別公開集計（Anthropic Economic Index）を用いた較正からは、閾値的な結果が得られた：AI適用率が低い段階（タスクの4分の1程度）では、一人当たり負荷を維持するのに必要な需要拡大は日本で観測された成長（1.2–1.4倍）と同水準だが、*適用率が半分を超えると必要倍率は1.7–1.8倍となり観測実績を明確に上回る*。すなわちAIの適用範囲が拡大するほど、必要な需要成長は非線形に増大し現実から乖離する。ただしこれは技術側パラメータの較正であって、価格チャネルにも一人当たり労働時間にも触れていない。本稿はこれらを隠さず報告し、必要な識別戦略と直接測定の設計を第8節に示す。

**キーワード:** 生成AI、労働市場、知能の民主化、責任制約、価格硬直性、専門職、Baumolのコスト病、監督ボトルネック効果  
**JEL:** J23, J24, O33, K00, I11

英語要旨は論文冒頭（`paper/main.pdf`）を参照してください。

## リポジトリ構成 (Repository structure)

```
.
├── paper/
│   ├── main.tex          # 論文本体（XeLaTeX）
│   ├── main.pdf          # 組版済み PDF（45 ページ）
│   ├── main.docx         # Word 版
│   └── figures/          # 論文掲載図（6 点）
├── data/
│   ├── codebook_v2.md                      # R・P コーディングの決定木
│   ├── coded_firstpass_39職業.csv           # 第一次コーディング（39 職業 × B, R, P）
│   ├── coded_full_A_measuredP_39職業.csv    # A・実測 P を結合した統合データ
│   ├── measured_P_出典付き.csv              # 実測 P（公定価格カバー率）と出典
│   ├── coding_template.csv                 # 第二コーダー用テンプレート
│   └── us341_BLS_PhiPsi.csv                # 米 BLS OOH 341 職業 + AI 曝露 + R/P/Φ/Ψ
├── code/
│   ├── README.md                 # 再現手順の詳細・データ出典・既知の制約
│   ├── repro_compat.py           # 共通ユーティリティ
│   ├── validate_constructs.py    # 構成概念妥当性の診断
│   ├── measured_p.py             # 実測 P の算出
│   ├── combine.py                # A・実測 P の結合と因子構造
│   ├── usmap.py                  # 米労働市場の Φ×Ψ 雇用量分解
│   └── h5_natexp.py              # 自然実験（不妊治療 2022 保険適用）の図
├── figures/                      # 再現パッケージの生成図
├── LICENSE                       # コード: MIT
└── LICENSE-paper                 # 論文・図・データ: CC BY 4.0
```

## 再現方法 (Reproduction)

Python 3.10+ を想定しています。

```bash
pip install numpy scikit-learn matplotlib
cd code
python validate_constructs.py   # 0) 構成概念妥当性の事前診断
python measured_p.py            # 1) 実測 P の一覧生成
python combine.py               # 2) A・実測 P の結合と因子構造
python usmap.py                 # 3) 米 BLS 341 職業の Φ×Ψ 分解
python h5_natexp.py             # 4) 自然実験の図生成 → figures/
```

出力が同梱データとバイト単位で一致することの確認:

```bash
cmp ../data/coded_with_A_measuredP.csv ../data/coded_full_A_measuredP_39職業.csv
cmp ../data/measured_P.csv             ../data/measured_P_出典付き.csv
cmp ../data/us341_phipsi.csv           ../data/us341_BLS_PhiPsi.csv
```

図に日本語ラベルを出すには日本語フォント（Noto Sans CJK JP など）が必要です。データ出典と既知の制約は [`code/README.md`](code/README.md) を参照してください。

論文のビルド: `cd paper && xelatex main.tex`（2 回実行）

## 引用 (Citation)

```bibtex
@techreport{democratization_labor_v12_2026,
  author      = {AUTHOR NAME},
  title       = {知能の民主化と労働市場再編：監督ボトルネックが成立する条件},
  institution = {Working Paper},
  year        = {2026},
  note        = {Version 12},
  url         = {https://github.com/USERNAME/REPO}
}
```

## ライセンス (License)

- 論文本文・図・データ: [CC BY 4.0](LICENSE-paper)
- コード（`code/`）: [MIT](LICENSE)

第三者データ（BLS OOH、Eloundou et al. 2024、Karpathy/jobs、Anthropic Economic Index 等）はそれぞれの提供元の条件に従います。
