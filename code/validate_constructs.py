#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R・P 構成概念妥当性 検証スクリプト（監督ボトルネック効果フレームワーク）
依存: numpy, scikit-learn（pandas は不要）

機能:
  1) gonogo(data)          : (B,R) 右上セルの充足を数える事前診断
  2) rp_correlation(data)  : R-P 共線性（横断分離の可否）
  3) krippendorff_alpha()  : 評価者間信頼性（順序尺度）— 自前実装
  4) external_validity(data): R/P を外部代理に回帰、既知群t検定
  5) factor_structure(data): A,B,R,P が一因子に潰れないかをPCAで確認

入力フォーマット:
  - ワイド: 列 occupation,A,B,R,P[,license,annex3,regulated_share,price_cv,...]
  - 評価者間用ロング: occupation,coder_id,R,P

使い方:
  python validate_constructs.py [CSVパス]
  （省略時は同梱の coded_firstpass_39職業.csv をスクリプト位置基準で読む）

2026-07 修復メモ:
  - 既定入力を同梱の実ファイル名 "coded_firstpass_39職業.csv" に修正
    （旧: "coded_firstpass.csv" は同梱されておらず実行不能だった）。
  - 既定入力をスクリプト位置基準で解決（カレントディレクトリ非依存）。
  - pandas 非依存化（DataFrame の代わりに {列名: numpy配列 / listのdict} を使う）。
    統計量・しきい値・出力メッセージは不変。
"""
import numpy as np
from itertools import combinations

import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent))  # 同梱の repro_compat.py を確実に読む
import repro_compat as rc

DEFAULT_INPUT = rc.pkg_path("coded_firstpass_39職業.csv")


# ---------- 入力ローダ ----------
def load(path):
    """CSV を {列名: 配列} の dict にして返す（数値列は float、他は文字列 list）。"""
    fields, rows = rc.read_table(path)
    data = {}
    for f in fields:
        vals = [r[f] for r in rows]
        try:
            data[f] = np.array([np.nan if v == "" else float(v) for v in vals], dtype=float)
        except ValueError:
            data[f] = vals
    data["__n__"] = len(rows)
    return data


def _mask(data, m):
    """boolean マスクで行を絞った dict を返す。"""
    out = {}
    for k, v in data.items():
        if k == "__n__":
            continue
        out[k] = v[m] if isinstance(v, np.ndarray) else [x for x, keep in zip(v, m) if keep]
    out["__n__"] = int(np.sum(m))
    return out


# ---------- 3) Krippendorff's alpha (ordinal / nominal) ----------
def krippendorff_alpha(data, level="ordinal"):
    """
    data: dict {coder_id: {unit_id: value}} または 2D配列(行=coder,列=unit, 欠損=np.nan)
    level: 'ordinal' or 'nominal'
    返り値: alpha
    """
    if isinstance(data, dict):
        units = sorted(set().union(*[set(v) for v in data.values()]))
        coders = sorted(data)
        M = np.full((len(coders), len(units)), np.nan)
        for i,c in enumerate(coders):
            for j,u in enumerate(units):
                if u in data[c]: M[i,j]=data[c][u]
    else:
        M = np.asarray(data, float)
    vals = np.unique(M[~np.isnan(M)])
    vals = np.sort(vals)
    # distance metric
    def delta(a,b):
        if level=="nominal": return 0.0 if a==b else 1.0
        # ordinal: squared rank-interval distance
        ia, ib = np.where(vals==a)[0][0], np.where(vals==b)[0][0]
        lo,hi=min(ia,ib),max(ia,ib)
        # ordinal metric: (sum of marginal counts between)^2 — needs n_g; approximate with index gap^2
        return (ia-ib)**2
    # pairable units (>=2 coders)
    cols=[M[:,j][~np.isnan(M[:,j])] for j in range(M.shape[1])]
    cols=[c for c in cols if len(c)>=2]
    if not cols: return float("nan")
    # observed disagreement Do
    num_o=0.0; den_o=0.0
    for c in cols:
        m=len(c)
        for a,b in combinations(range(m),2):
            num_o+=delta(c[a],c[b]);
        den_o+=m*(m-1)/2
    Do=num_o/den_o
    # expected disagreement De (over all value pairs across all pairable values)
    allv=np.concatenate(cols)
    n=len(allv); num_e=0.0
    for a,b in combinations(range(n),2):
        num_e+=delta(allv[a],allv[b])
    De=num_e/(n*(n-1)/2)
    return 1.0 - Do/De if De>0 else 1.0

# ---------- 1) go/no-go ----------
def gonogo(df, b_hi=0.5, r_hi=3, need=8):
    corner=_mask(df,(df["B"]>=b_hi)&(df["R"]>=r_hi))
    n=corner["__n__"]
    print(f"[GO/NO-GO] 高B(>={b_hi}) x 高R(>={r_hi}) セル: {n} 職業 "
          f"-> {'GO' if n>=need else 'NO-GO/縮小再設計'} (目安>={need})")
    for c in ['occupation','B','R','P']:
        if c not in df: print("  (列不足)"); break
    else:
        print(rc.to_string(['occupation','B','R','P'],
                           [corner['occupation'],
                            [f"{v:.2f}" for v in corner['B']],
                            [int(v) for v in corner['R']],
                            [int(v) for v in corner['P']]]))
    return n

# ---------- 2) R-P correlation ----------
def rp_correlation(df):
    r=rc.corr(df["R"],df["P"])
    print(f"[R-P 共線性] r = {r:.2f}  "
          f"-> {'横断分離は困難。職業内P変動で識別せよ' if abs(r)>=0.6 else '横断分離おおむね可'}")
    # off-diagonal cell占有
    hi_lo=int(np.sum((df["R"]>=3)&(df["P"]<=1))); lo_hi=int(np.sum((df["R"]<=1)&(df["P"]>=3)))
    print(f"  高R低P: {hi_lo} 職業 / 低R高P: {lo_hi} 職業（非対角が空だと相関は過大評価）")
    return r

# ---------- 4) external validity ----------
def external_validity(df):
    from sklearn.linear_model import LinearRegression
    R_proxies=[c for c in ['license_liab','annex3','signature','malpractice'] if c in df]
    P_proxies=[c for c in ['regulated_share','price_cv_inv','longterm_share'] if c in df]
    if R_proxies:
        X=np.column_stack([df[c] for c in R_proxies]); y=df["R"]
        m=LinearRegression().fit(X,y); print(f"[外的妥当性 R] R^2={m.score(X,y):.2f} coefs={dict(zip(R_proxies,np.round(m.coef_,2)))}")
    else: print("[外的妥当性 R] R代理列なし（license_liab,annex3,... を付与して実行）")
    if P_proxies:
        X=np.column_stack([df[c] for c in P_proxies]); y=df["P"]
        m=LinearRegression().fit(X,y); print(f"[外的妥当性 P] R^2={m.score(X,y):.2f} coefs={dict(zip(P_proxies,np.round(m.coef_,2)))}")
    else: print("[外的妥当性 P] P代理列なし（regulated_share,... 推奨。実測Pでコード置換が最強）")
    # known-groups: licensed vs not
    if 'license_liab' in df:
        a=df["R"][df['license_liab']==1]; b=df["R"][df['license_liab']==0]
        print(f"  既知群: 有資格R平均={a.mean():.2f} vs 非資格={b.mean():.2f}")

# ---------- 5) factor structure ----------
def factor_structure(df):
    from sklearn.preprocessing import StandardScaler
    cols=[c for c in ['A','B','R','P'] if c in df]
    if len(cols)<3:
        print(f"[因子構造] 列不足（{cols}）。A,B,R,P を揃えて実行。"); return
    Z=StandardScaler().fit_transform(np.column_stack([df[c] for c in cols]))
    C=np.corrcoef(Z.T); ev=np.sort(np.linalg.eigvalsh(C))[::-1]
    nfac=int((ev>1).sum())  # Kaiser
    print(f"[因子構造] 相関行列固有値={np.round(ev,2)}  Kaiser因子数={nfac} "
          f"-> {'OK（多次元・AI曝露の言い換えではない）' if nfac>=2 else '警告: 一因子化（枠組み再設計）'}")
    print(f"  相関行列:\n{rc.matrix_to_string(cols,np.round(C,2))}")

if __name__=="__main__":
    import sys
    path=sys.argv[1] if len(sys.argv)>1 else DEFAULT_INPUT
    df=load(path)
    print(f"=== 入力: {path}  (n={df['__n__']}) ===\n")
    gonogo(df); print(); rp_correlation(df); print()
    # A列が無ければ因子構造デモ用に擬似A（業務統合度の仮値）を付さず、B,R,Pで実行
    factor_structure(df); print()
    external_validity(df); print()
    # --- Krippendorff 自己テスト（2コーダーの合成データで実装の動作確認） ---
    print("=== Krippendorff α 自己テスト（合成2コーダー） ===")
    demo={'c1':{1:4,2:3,3:1,4:4,5:0,6:2},'c2':{1:4,2:3,3:1,4:3,5:0,6:2}}  # ほぼ一致
    print(f"  ほぼ一致ケース α(ordinal)={krippendorff_alpha(demo):.2f}")
    demo2={'c1':{1:4,2:0,3:1,4:4,5:0,6:2},'c2':{1:0,2:4,3:3,4:1,5:2,6:0}} # 不一致
    print(f"  不一致ケース   α(ordinal)={krippendorff_alpha(demo2):.2f}")
    print("\n(実運用: 30-40職業を2-3名がブラインド採点したロングCSVで R,P それぞれ α を算出。目標 α>=0.80)")
