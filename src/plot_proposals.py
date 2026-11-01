"""에이전트 제안 32개의 개발 데이터 결과 그림 — reports/agent_proposals.png. 시험 데이터는 쓰지 않는다.

uv run python src/plot_proposals.py
"""
import json

import matplotlib

from data import ROOT

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from agent.evaluate import MIN_DELTA_THIN  # noqa: E402

REPORTS = ROOT / "reports"


def load(base: str) -> list[dict]:
    path = REPORTS / f"agent_proposals_from_{base}.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> None:
    plt.rcParams["font.family"] = ["AppleGothic", "DejaVu Sans"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.9), sharey=True)
    for ax, base, title in ((axes[0], "b", "사람 피처 위에서 시작 (16개 중 채택 0)"),
                            (axes[1], "a", "지금 정보만 보고 시작 (16개 중 채택 2)")):
        recs = [r for r in load(base) if r.get("delta_thin_mean") is not None]
        xs = list(range(1, len(recs) + 1))
        ys = [r["delta_thin_mean"] * 1000 for r in recs]
        colors = ["#2f6fdb" if r["decision"] == "채택" else "#b8bfc9" for r in recs]
        ax.bar(xs, ys, color=colors)
        ax.axhline(MIN_DELTA_THIN * 1000, color="#d9480f", lw=1.2, ls="--")
        ax.axhline(0, color="#555", lw=0.8)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("제안 순서(라운드 1 → 4)")
        ax.set_xticks(xs)
        ax.tick_params(axis="x", labelsize=7)
    axes[0].set_ylabel("이력이 얇은 고객 AUC 변화 (×1/1000)")
    axes[1].text(0.98, 0.95, "파랑 = 채택, 회색 = 기각\n점선 = 평균 기준 +2\n(점선을 넘어도 15쌍 중 70% 미만에서 오르면 기각)",
                 transform=axes[1].transAxes, ha="right", va="top", fontsize=8.5, color="#333")
    fig.suptitle("LLM 이 낸 피처 제안과 검증 결과 (개발 데이터, 5겹 × 3번 교차 검증 평균)", fontsize=12)
    fig.tight_layout()
    fig.savefig(REPORTS / "agent_proposals.png", dpi=140)
    print("saved reports/agent_proposals.png", [len(load(b)) for b in "ba"])


if __name__ == "__main__":
    main()
