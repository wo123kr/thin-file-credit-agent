"""에이전트 기록(agent_runs/*/proposals.jsonl) → reports/agent_log_from_<a|b>.md 표 + 같은 내용 jsonl 사본.

uv run python src/report_agent.py
"""
import json
import shutil

from data import ROOT

RUNS = ROOT / "agent_runs"
REPORTS = ROOT / "reports"


def latest(base: str):
    runs = sorted(RUNS.glob(f"*-from-{base}"))
    return runs[-1] if runs else None


def to_markdown(recs: list[dict], title: str) -> str:
    n_ok = sum(r["decision"] == "채택" for r in recs)
    lines = [f"# {title}", "", f"제안 {len(recs)}개 · 채택 {n_ok}개. 수치는 개발 데이터 5겹 × 3번 교차 검증의 평균 차이"
             "(표는 기록에 저장된 값 그대로, 이유 문장은 원값을 소수 4자리로 반올림).", "",
             "| 라운드 | 이름 | 가설 | ΔAUC 얇은 이력 | ΔAUC 전체 | 오른 쌍 | 결정 | 이유 |", "|---|---|---|---|---|---|---|---|"]
    for r in recs:
        dt, da = r.get("delta_thin_mean"), r.get("delta_all_mean")
        fmt = (lambda v: f"{v:+.5f}" if isinstance(v, (int, float)) else "-")   # 저장값 그대로(다시 반올림하지 않음)
        hyp = str(r.get("hypothesis", "")).replace("|", "/").replace("\n", " ")
        lines.append(f"| {r.get('round', '')} | {r['name']} | {hyp} | {fmt(dt)} | {fmt(da)} | "
                     f"{r.get('pos_share', '-')} | {r['decision']} | {str(r['reason']).replace('|', '/')} |")
    lines += ["", "## SQL", ""]
    for r in recs:
        lines += [f"### {r['name']} ({r['decision']})", "", "```sql", r.get("sql", "").strip(), "```", ""]
    return "\n".join(lines)


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    for base, title in (("b", "실험 1 — 사람 피처(B) 위에서 시작한 에이전트"), ("a", "실험 2 — A 만 보고 시작한 에이전트")):
        run = latest(base)
        if not run:
            continue
        src = run / "proposals.jsonl"
        recs = [json.loads(line) for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
        (REPORTS / f"agent_log_from_{base}.md").write_text(to_markdown(recs, title), encoding="utf-8")
        shutil.copy(src, REPORTS / f"agent_proposals_from_{base}.jsonl")
        print(base, run.name, len(recs))


if __name__ == "__main__":
    main()
