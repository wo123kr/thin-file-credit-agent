"""시험 데이터를 한 번만 연다: A · B · B+에이전트를 개발 데이터 전체로 학습해 시험 데이터에서 비교.

uv run python src/final.py          # 두 번째부터는 막힌다(--force 는 기록이 남는다)
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime

import matplotlib
import numpy as np
import pandas as pd

from data import PROTECTED, ROOT
from features import frame, sandbox, tier, validate_new
from metrics import auc, bootstrap_uplift, ks_stat, uplift_at_anchor
from model import gbm

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPORTS = ROOT / "reports"
GUARD = REPORTS / "test_opened.json"
ACCEPTED = {"B+agent": ROOT / "sql" / "agent_accepted.json", "A+agent": ROOT / "sql" / "agent_accepted_from_a.json"}
SHARES = (0.5, 0.7, 0.9)
APPROVE_ALL = 0.8


def agent_features(meta: pd.DataFrame, feats: pd.DataFrame, path) -> tuple[pd.DataFrame, list[str]]:
    cols = []
    if not path.exists():
        return feats, cols
    for a in json.loads(path.read_text(encoding="utf-8")):
        new = validate_new(sandbox().run(a["sql"]), meta.index, list(feats.columns))
        feats, cols = feats.join(new), cols + list(new.columns)
    return feats, cols


def predict(feats: pd.DataFrame, cols: list[str], meta: pd.DataFrame) -> np.ndarray:
    dev, test = meta["part"] == "dev", meta["part"] == "test"
    m = gbm().fit(feats.loc[dev, cols], meta.loc[dev, "is_default"])
    return m.predict_proba(feats.loc[test, cols])[:, 1]


def scores(y, thin, risk) -> dict:
    return {"all": {"auc": round(auc(y, risk), 4), "ks": round(ks_stat(y, risk), 4)},
            "thin": {"auc": round(auc(y[thin], risk[thin]), 4), "ks": round(ks_stat(y[thin], risk[thin]), 4)}}


PAIRS = [("A", "B"), ("A", "B+agent"), ("B", "B+agent"), ("A", "A+agent"), ("A+agent", "B")]


def uplifts(y, risks: dict) -> dict:
    out = {}
    for base, new in [p for p in PAIRS if p[0] in risks and p[1] in risks]:
        for s in SHARES:
            u = uplift_at_anchor(y, risks[base], risks[new], s)
            b = bootstrap_uplift(y, risks[base], risks[new], s)
            out[f"{base}->{new}@{int(s * 100)}"] = {k: round(v, 4) for k, v in u.items()} | b
    return out


def fairness(test_meta: pd.DataFrame, risk: np.ndarray) -> dict:
    prot = pd.read_parquet(PROTECTED).set_index("id").loc[test_meta.index]
    df = test_meta.assign(ok=risk <= np.quantile(risk, APPROVE_ALL), sex=prot["sex"].map({1: "남", 2: "여"}),
                          age=pd.cut(prot["age"], [0, 29, 44, 200], labels=["~29", "30~44", "45~"]))
    return {col: {str(k): {"n": int(len(g)), "approve_rate": round(float(g["ok"].mean()), 4),
                           "bad_rate_approved": round(float(g.loc[g["ok"], "is_default"].mean()), 4)}
                  for k, g in df.groupby(col, observed=True)} for col in ("sex", "age")}


def plot(y, thin, risks: dict) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for name, r in risks.items():
        yt, rt = y[thin], r[thin]
        order = np.argsort(rt, kind="mergesort")
        k = np.arange(1, len(yt) + 1)
        ax.plot(k / len(yt) * 100, np.cumsum(yt[order]) / k * 100, label=name)
    ax.set_xlabel("승인율(%) — 위험 낮은 순"), ax.set_ylabel("승인자 연체율(%)")
    ax.set_title("이력이 얇은 고객(시험 데이터): 승인율 vs 연체율"), ax.set_xlim(20, 100), ax.legend()
    fig.tight_layout(), fig.savefig(REPORTS / "thin_approval_curve.png", dpi=130)


def test_risks():
    """(meta, 피처 묶음, 에이전트 열, 묶음별 시험 데이터 위험도). 결정적이라 다시 불러도 같은 값."""
    meta, feats = frame()
    a_cols, b_cols = list(tier("a").columns), list(feats.columns)
    sets, agent_cols = {"A": a_cols, "B": b_cols}, {}
    for name, start in (("B+agent", b_cols), ("A+agent", a_cols)):
        feats, cols = agent_features(meta, feats, ACCEPTED[name])
        agent_cols[name] = cols
        if cols:                              # 채택이 0개면 그 묶음은 앞의 것과 같으므로 빼고 기록만
            sets[name] = start + cols
    return meta, sets, agent_cols, {k: predict(feats, cols, meta) for k, cols in sets.items()}


def git_head() -> str:
    """지금 커밋. 추적 파일에 커밋하지 않은 변경이 있으면 -dirty 를 붙인다(기록된 커밋 = 실제로 돈 코드가 되게)."""
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True)
    return (r.stdout.strip() or "(커밋 전)") + ("-dirty" if d.stdout.strip() else "")


def log_open(purpose: str, force: bool = False) -> None:
    """시험 데이터를 열기 「전에」 기록한다. 계산 중에 죽어도 연 사실은 남는다."""
    opened = json.loads(GUARD.read_text(encoding="utf-8")) if GUARD.exists() else []   # 지우지 않고 쌓는다
    opened.append({"opened_at": datetime.now().isoformat(timespec="seconds"), "commit": git_head(),
                   "forced": force, "purpose": purpose})
    REPORTS.mkdir(exist_ok=True)
    GUARD.write_text(json.dumps(opened, ensure_ascii=False, indent=2), encoding="utf-8")


def main(force: bool) -> None:
    if GUARD.exists() and not force:
        sys.exit(f"시험 데이터는 이미 열었습니다: {GUARD.read_text(encoding='utf-8')}")
    plt.rcParams["font.family"] = ["AppleGothic", "DejaVu Sans"]
    log_open("최종 평가(final.py)", force)
    meta, sets, agent_cols, risks = test_risks()
    tm = meta[meta["part"] == "test"]
    y, thin = tm["is_default"].to_numpy(), tm["thin"].to_numpy()
    results = {
        "opened_at": datetime.now().isoformat(timespec="seconds"), "commit": git_head(),
        "accepted_sha1": {k: hashlib.sha1(p.read_bytes()).hexdigest()[:10] for k, p in ACCEPTED.items() if p.exists()},
        "test": {"n": int(len(y)), "thin_n": int(thin.sum()), "thin_bad": int(y[thin].sum())},
        "features": {k: len(v) for k, v in sets.items()}, "agent_columns": agent_cols,
        "scores": {k: scores(y, thin, r) for k, r in risks.items()},
        "thin_uplift": uplifts(y[thin], {k: r[thin] for k, r in risks.items()}),
        "fairness_approve80": {k: fairness(tm, risks[k]) for k in risks if k != "A"},
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    plot(y, thin, risks)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    main(ap.parse_args().force)
