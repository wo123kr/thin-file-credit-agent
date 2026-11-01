"""보조 지표(시험 데이터를 연 뒤 추가): 같은 승인율에서의 승인자 연체율 차이.

미리 정한 지표(같은 연체율에서의 승인율)가 얇은 이력 756명에서 크게 흔들려서(점 추정이 부트스트랩 구간 끝에 붙음)
더 매끄러운 쪽을 덧붙인다. 모형 · 피처 · 시드는 final.py 와 같고 바꾸지 않는다. 이 실행도 연 기록에 남긴다.
uv run python src/supplement.py
"""
import json
from datetime import datetime

import numpy as np

from final import GUARD, REPORTS, SHARES, git_head, test_risks
from metrics import bad_rate_at_share

PAIRS = [("A", "B"), ("A", "A+agent"), ("A+agent", "B")]


def diff_ci(y, rb, rn, share, n=1000, seed=0) -> dict:
    point = bad_rate_at_share(y, rn, share) - bad_rate_at_share(y, rb, share)
    rng, ds = np.random.default_rng(seed), []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        ds.append(bad_rate_at_share(y[i], rn[i], share) - bad_rate_at_share(y[i], rb[i], share))
    lo, hi = np.percentile(ds, [2.5, 97.5])
    return {"base_bad": round(bad_rate_at_share(y, rb, share), 4), "new_bad": round(bad_rate_at_share(y, rn, share), 4),
            "diff": round(float(point), 4), "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "share_lower": round(float(np.mean(np.asarray(ds) < 0)), 3)}


def main() -> None:
    meta, _, _, risks = test_risks()
    tm = meta[meta["part"] == "test"]
    y, thin = tm["is_default"].to_numpy(), tm["thin"].to_numpy()
    out = {"note": "시험 데이터를 연 뒤 추가한 보조 지표. 음수 = 새 모형이 같은 승인율에서 연체율이 낮음", "thin": {}}
    for b, n in [p for p in PAIRS if p[0] in risks and p[1] in risks]:
        for s in SHARES:
            out["thin"][f"{b}->{n}@{int(s * 100)}"] = diff_ci(y[thin], risks[b][thin], risks[n][thin], s)
    (REPORTS / "results_supplement.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    opened = json.loads(GUARD.read_text(encoding="utf-8"))
    opened.append({"opened_at": datetime.now().isoformat(timespec="seconds"), "commit": git_head(), "forced": False,
                   "purpose": "보조 지표 계산(같은 승인율의 연체율). 모형 · 피처 변경 없음"})
    GUARD.write_text(json.dumps(opened, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
