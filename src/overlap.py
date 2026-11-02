"""에이전트가 혼자 찾은 피처(실험 2)는 사람 피처를 다시 찾은 것인가 — 개발 데이터만, 라벨 없이.

채택된 열마다 사람 피처(B 의 이력 집계 11개)와의 순위 상관을 재고,
그 열을 사람 피처 전부로 설명할 때의 결정계수(순위로 바꾼 뒤 선형 회귀, R²)를 남긴다.
시험 데이터 · 라벨은 쓰지 않으므로 시험 데이터 연 기록 대상이 아니다.

uv run python src/overlap.py   → reports/overlap.json
"""
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from features import SQL_DIR, frame, sandbox, tier, validate_new
from data import ROOT

REPORTS = ROOT / "reports"


def agent_columns(ids: pd.Index, existing: list[str]) -> pd.DataFrame:
    accepted = json.loads((SQL_DIR / "agent_accepted_from_a.json").read_text(encoding="utf-8"))
    sb = sandbox()
    parts = [validate_new(sb.run(a["sql"]), ids, existing) for a in accepted]
    return pd.concat(parts, axis=1)


def overlap(agent: pd.DataFrame, human: pd.DataFrame) -> dict:
    ra, rh = agent.rank(), human.rank()
    out = {}
    for c in agent.columns:
        ok = ra[c].notna()
        corr = rh[ok].corrwith(ra.loc[ok, c]).dropna()
        top = corr.abs().sort_values(ascending=False).head(3)
        X = rh[ok].fillna(rh[ok].median())
        r2 = LinearRegression().fit(X, ra.loc[ok, c]).score(X, ra.loc[ok, c])
        out[c] = {"top_human": {k: round(float(corr[k]), 3) for k in top.index},
                  "r2_from_all_human": round(float(r2), 3), "n": int(ok.sum())}
    return out


def main() -> None:
    meta, feats = frame()
    a_cols = tier("a").columns.tolist()
    human = feats[[c for c in feats.columns if c not in a_cols]]
    agent = agent_columns(meta.index, feats.columns.tolist())
    dev = meta["part"] != "test"
    thin = dev & meta["thin"].astype(bool)
    out = {"note": "개발 데이터만 · 라벨 안 씀. 순위 상관(스피어만), R² = 사람 피처 11개(순위)로 그 열(순위)을 선형 회귀로 설명한 비율",
           "human_features": human.columns.tolist(),
           "dev_all": overlap(agent[dev], human[dev]),
           "dev_thin": overlap(agent[thin], human[thin])}
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "overlap.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
