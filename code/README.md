> **リポジトリ構成に関する注記**: 公開版ではスクリプトを `code/`、データを `data/`、生成図を `figures/` に分離している。スクリプトは `code/` ディレクトリで実行し、入出力は `../data/` を基準に解決される（`repro_compat.PKG_DIR`）。

# 再現手順（README_REPRODUCTION）

「知能の民主化と労働市場再編：監督ボトルネック効果」working paper 付随データパッケージ

最終更新: 2026-07-25（再現性修復時に新規作成）

---

## 1. 動作確認済み環境

下記は **本パッケージの修復・検証を実施した実環境**（2026-07-25、Windows 11）で
実際に全スクリプトを完走させたときのバージョンである。

| 項目 | 動作確認済みバージョン |
|---|---|
| OS | Windows 11 (10.0.26200) |
| Python | 3.14.2 |
| numpy | 2.4.4 |
| scikit-learn | 1.8.0 |
| matplotlib | 3.10.8 |
| pandas | **未インストール（不要）** |

### 依存パッケージ（実際に import されているもの）

| パッケージ | 使用スクリプト | 必須か |
|---|---|---|
| numpy | combine.py, measured_p.py(間接), usmap.py, h5_natexp.py, validate_constructs.py, repro_compat.py | 必須 |
| scikit-learn (`sklearn.preprocessing.StandardScaler`, `sklearn.linear_model.LinearRegression`) | combine.py, validate_constructs.py | 必須 |
| matplotlib | h5_natexp.py | h5_natexp.py のみ必須 |
| 標準ライブラリ (`csv`, `json`, `re`, `math`, `pathlib`, `itertools`, `sys`, `warnings`) | 全体 | 必須 |

`requirements.txt` 相当（最小）:

```
numpy>=2.0
scikit-learn>=1.5
matplotlib>=3.8
```

> **pandas について**: 修復前の 5 本のスクリプトはすべて pandas に依存していたが、
> 検証環境に pandas が存在しなかったため、**pandas を使わない標準ライブラリ + numpy 実装に書き換えた**
> （共通処理は `repro_compat.py` に集約）。出力 CSV は修復前の同梱結果と**バイト単位で一致**することを
> 確認済み（§4 参照）。したがって pandas は**インストール不要**である。

### 日本語フォント

`h5_natexp.py` は日本語ラベル付きの図を生成する。修復前は 環境固有の絶対パス
（`/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`）を直接指定していたため
Windows/macOS では実行できなかった。現在は `repro_compat.find_japanese_font()` が
matplotlib のフォント一覧から日本語フォント（Noto Sans CJK JP / Noto Sans JP / IPAexGothic /
Yu Gothic / Meiryo / Hiragino Sans など、優先順で探索）を**実行時に自動検出**する。

- 見つかった場合: 日本語ラベルで描画（検証環境では `Noto Sans JP` を自動選択）。
- 見つからない場合: `RuntimeWarning` を出したうえで、**すべてのラベルを英語にフォールバック**して描画。
  図の数値・系列・レイアウトは同一。

---

## 2. 実行順序

スクリプトは相互に依存しない（すべて同梱 CSV を直接読む）。ただし論文の論理順序に沿った
推奨実行順は以下のとおり。**どのディレクトリから実行してもよい**（入出力パスは
`pathlib` でスクリプト自身の位置を基準に解決される）。

```bash
cd <このディレクトリ>

python validate_constructs.py       # 0) 構成概念妥当性の事前診断（go/no-go, 共線性, 因子構造）
python measured_p.py                # 1) 実測P（公定価格カバー率）の一覧生成と主観Pとの照合
python combine.py                   # 2) A・実測P を結合した統合コードCSVの生成と因子構造
python usmap.py                     # 3) 米BLS 341職業の Φ×Ψ 雇用量分解
python h5_natexp.py                 # 4) 自然実験（不妊治療2022保険適用）の図生成
```

`validate_constructs.py` は任意の CSV パスを引数に取れる:

```bash
python validate_constructs.py coded_full_A_measuredP_39職業.csv   # A列を含む4変数版の因子構造
```

---

## 3. 各スクリプトの入力・出力

| スクリプト | 入力 | 出力 | 内容 |
|---|---|---|---|
| `validate_constructs.py` | `coded_firstpass_39職業.csv`（引数で変更可） | 標準出力のみ | go/no-go 診断、R-P 共線性、因子構造（Kaiser）、外的妥当性、Krippendorff α 自己テスト |
| `measured_p.py` | `coded_firstpass_39職業.csv` | `measured_P.csv`（= 同梱 `measured_P_出典付き.csv`）+ 標準出力 | 実測P（公定価格カバー率 M1）一覧の生成、主観P との相関・平均絶対差 |
| `combine.py` | `coded_firstpass_39職業.csv` | `coded_with_A_measuredP.csv`（= 同梱 `coded_full_A_measuredP_39職業.csv`）+ 標準出力 | A（AI導入率代理）付与、実測Pでの置換、因子構造・主成分負荷 |
| `usmap.py` | `us341_BLS_PhiPsi.csv` | `us341_phipsi.csv`（= 入力と同一内容）+ 標準出力 | 規則ベースの R/P 採点、Φ×Ψ の雇用量重み付き分解 |
| `h5_natexp.py` | なし（数値はスクリプト内直書き） | `h5_natexp.png`, `h5_natexp.pdf` | ART出生児数の推移と価格分散の模式図（論文図: `図_自然実験_不妊治療保険適用2022.png`） |
| `repro_compat.py` | — | — | 共通ユーティリティ（CSV I/O、相関、表整形、パス解決、日本語フォント探索）。単体では実行しない |

### 同梱データファイル

| ファイル | 説明 |
|---|---|
| `coded_firstpass_39職業.csv` | 第一次コーディング結果（39職業 × occupation, B, R, P, offdiag） |
| `coded_full_A_measuredP_39職業.csv` | `combine.py` の出力（A, P_measured, P_used を追加） |
| `measured_P_出典付き.csv` | `measured_p.py` の出力（実測P と出典テキスト） |
| `coding_template.csv` | 第二コーダー用の空欄テンプレート（決定木の各設問列） |
| `us341_BLS_PhiPsi.csv` | 米BLS OOH 341職業 + Digital AI Exposure + 規則ベース R/P/Φ/Ψ |
| `codebook_v2.md` | R・P 操作的コードブック v2（決定木） |
| `図_*.png` | 論文掲載図（生成済み） |

---

## 4. 入力データの出典・取得日

> **注意**: 出典・取得日が原資料に記録されていないものは「**未記録（要確認）**」と明記している。
> 推測で埋めていない。

| データ | 変数 | 出典 | 取得日 |
|---|---|---|---|
| GPT職業曝露スコア（α） | `B`（39職業CSVの `B` 列） | Eloundou, T., Manning, S., Mishkin, P., Rock, D. (2023) "GPTs are GPTs", arXiv:2303.10130 および付随の公開GitHubリポジトリ値の近似（論文 §7.2 注記に「Table 1 および公開リポジトリ値の近似」とある） | **未記録（要確認）** |
| R（責任制約）スコア | `R` | 本研究による付与。`codebook_v2.md` の決定木（v2, 2026-07-11 Q4改訂）を単一著者が機械的に適用した第一次コーディング | コーディング実施日: 2026-07-10 前後（`coded_firstpass_39職業.csv` のファイル更新日 2026-07-10）。コードブック v2 改訂日 2026-07-11 |
| P（価格硬直性）スコア（主観） | `P` | 同上（`codebook_v2.md` の P 決定木 B） | 同上 |
| P（実測） | `P_measured`, `regulated_share` | `measured_p.py` 内に職業ごとに出典テキストを直書き（国民医療費、診療報酬・調剤報酬・介護報酬の公定性、旧弁護士報酬基準2004廃止、道路運送法の認可運賃、郵便料金の認可制、JTF 2017翻訳白書の価格帯分散、矢野経済研究所2024の美容医療市場6,310億円 等）。**個々の一次資料URLは原スクリプトに記録されていない** | **未記録（要確認）** |
| A（業種別生成AI導入率の代理） | `A` | `combine.py` 内コメント: JUAS 2025（社会インフラ 60.8%、金融保険 54.4%）、総務省『情報通信白書』、PwC 2025 等に基づく粗いマッピング。**個々の一次資料URL・版は記録されていない** | **未記録（要確認）** |
| 米BLS OOH 341職業（title, category, pay, jobs, outlook, education, url） | `us341_BLS_PhiPsi.csv` | 米労働統計局 Occupational Outlook Handbook（各行の `url` 列に BLS の該当ページURLが記録されている） | **未記録（要確認）** |
| Digital AI Exposure スコア（0–10） | `exposure`, `exposure_rationale` | Karpathy, A. (2025) *US Job Market Visualizer*, `github.com/karpathy/jobs`（BLS OOH 342職業へのDigital AI Exposure採点）。**元の実行時の入力ファイル `data.json` は本パッケージに同梱されていない**（§5 参照） | **未記録（要確認）** |
| ART出生児数 2018–2023（56,979 / 60,598 / 60,381 / 69,797 / 77,206 / 85,048） | `h5_natexp.py` 内直書き | 日本産科婦人科学会「2023年 ARTデータブック（体外受精・胚移植等の臨床実施成績）」<br>`https://www.jsog.or.jp/activity/art/2023_JSOG-ART.pdf`<br>2018–2020 は概数、2021–2023 は確報（`prep/trend/RESULTS.md` にて本スクリプトの値と一致を確認済み） | **2026-07-10**（分析リポジトリ `prep/trend/RESULTS.md` に記録） |
| 体外受精費用の分布（右パネル） | `h5_natexp.py` 内 `np.random.seed(3)` による**模式（シミュレーション）** | 実データではない。論文図キャプションでも「模式」と明記 | 該当なし |

---

## 5. 既知の制約

1. **`usmap.py` の元入力 `data.json` は同梱されていない。**
   修復前は 環境固有の絶対パスにある `data.json` を読んでいた。現在は
   同梱の `us341_BLS_PhiPsi.csv`（= 本スクリプトの出力であり、入力に必要な
   `title`, `category`, `exposure`, `jobs` をすべて含む）を入力として読む。
   スクリプト冒頭で、同梱 CSV の `R`/`P`/`Phi`/`Psi` と再計算値が一致するかを自動検証する
   （検証環境では 341 行すべて一致 = 不一致 0 件）。
   ただしこれは**採点規則の再現の検証**であって、BLS/Karpathy 生データからの完全な
   エンドツーエンド再現ではない。生データから始めたい場合は `github.com/karpathy/jobs` の
   `site/data.json` を取得し、`usmap.py` の `IN_CSV` 読み込み部を JSON 読み込みに戻す必要がある。

2. **`h5_natexp.py` の右パネルは実データではなく模式図**である（`np.random.seed(3)` 固定の
   正規乱数）。価格分散の縮小を視覚的に示すための概念図であり、実測価格分布ではない。

3. **R・P スコアは第一次・単一コーダーの暫定値**である。論文 §8 で述べられているとおり
   評価者間信頼性（Krippendorff α）の検証対象であり、`validate_constructs.py` の
   α 計算は現時点では合成データによる**実装の自己テスト**のみ（実コーダー間データは
   本パッケージに含まれない）。

4. **A の出典が粗い。** `combine.py` の `Amap` は業種別導入率の粗いマッピングであり、
   個別の一次資料への紐付けは記録されていない（§4 参照）。

5. **`validate_constructs.py` の外的妥当性パート**は、代理変数列
   （`license_liab`, `annex3`, `regulated_share` 等）が同梱 CSV に無いため、実行しても
   「代理列なし」のメッセージを出して終わる。`sklearn.linear_model` のコードパスは
   現状の同梱データでは通らない。

6. **`repro_compat.krippendorff_alpha` の ordinal メトリック**は原実装のまま
   「順位差の二乗」による近似であり、周辺度数を用いた厳密な ordinal メトリックではない
   （原スクリプトのコメントに明記されているとおり。修復では変更していない）。

7. **修復前のスクリプト（`*.py.bak`）は公開リポジトリには含めていない。**

---

## 6. 再現の検算（任意）

出力が同梱物と一致することを確認するには:

```bash
python combine.py    && cmp ../data/coded_with_A_measuredP.csv ../data/coded_full_A_measuredP_39職業.csv
python measured_p.py && cmp ../data/measured_P.csv ../data/measured_P_出典付き.csv
python usmap.py      && cmp ../data/us341_phipsi.csv ../data/us341_BLS_PhiPsi.csv
```

検証環境では 3 本ともバイト単位で一致した。
