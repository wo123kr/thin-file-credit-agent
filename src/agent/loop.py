"""에이전트 루프: 제안 받기 → 검증 → 채택이면 다음 기준에 더하기 → 기록.

uv run python src/agent/loop.py --rounds 4 --per-round 4
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import prompt  # noqa: E402
from agent.evaluate import Evaluator  # noqa: E402
from agent.llm import LLMError, claude_cli, parse_json  # noqa: E402
from data import ROOT  # noqa: E402
from features import frame  # noqa: E402

RUNS = ROOT / "agent_runs"
ACCEPTED = {"b": ROOT / "sql" / "agent_accepted.json", "a": ROOT / "sql" / "agent_accepted_from_a.json"}

BASE_DESC = {
    "limit_bal": "카드 한도", "education_grp": "학력(1~4)", "status_now": "9월 상환 상태", "bill_now": "9월 청구액",
    "paid_now": "9월 낸 금액", "util_now": "9월 청구액 ÷ 한도", "delinq_max_6m": "6개월 최장 연체(달)",
    "delinq_months_6m": "6개월 중 연체한 달 수", "delinq_months_3m": "최근 3개월 중 연체한 달 수",
    "idle_months_6m": "6개월 중 사용 없는(-2) 달 수", "billed_months_6m": "6개월 중 청구가 있던 달 수",
    "util_avg_6m": "6개월 평균 청구 ÷ 한도", "util_max_6m": "6개월 최고 청구 ÷ 한도",
    "bill_trend_6m": "(9월 청구 - 4월 청구) ÷ 한도", "paid_to_limit_6m": "6개월 평균 납부 ÷ 한도",
    "pay_ratio_avg_5m": "직전 청구 대비 납부 비율 평균(1 상한)", "zero_pay_months_5m": "청구가 있는데 0원 낸 달 수",
}


A_COLS = ["limit_bal", "education_grp", "status_now", "bill_now", "paid_now", "util_now"]


def run(rounds: int, per_round: int, llm=claude_cli, out_dir: Path | None = None, base: str = "b") -> list[dict]:
    """base = "b": 사람 피처(A+B) 위에서 시작(실험 1) · "a": A 만 보고 시작(실험 2)."""
    meta, feats = frame()
    if base == "a":
        feats = feats[A_COLS]
    ev = Evaluator(meta, feats)
    desc = {k: v for k, v in BASE_DESC.items() if k in feats.columns}
    history, accepted = [], []
    out_dir = out_dir or RUNS / datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    log = (out_dir / "proposals.jsonl").open("a", encoding="utf-8")
    for r in range(1, rounds + 1):
        try:
            reply = parse_json(llm(prompt.SYSTEM, prompt.build(desc, history, per_round)))
            proposals = reply.get("proposals", [])[:per_round]
        except LLMError as e:
            history.append({"round": r, "name": "(LLM 답 없음)", "hypothesis": "", "decision": "오류", "reason": str(e)})
            continue
        for p in proposals:
            t = time.time()
            rec, new = ev.evaluate(p if isinstance(p, dict) else {})
            rec.update(round=r, seconds=round(time.time() - t, 1))
            history.append(rec)
            log.write(prompt.dump(rec) + "\n")
            log.flush()
            print(f"[{r}] {rec['decision']} {rec['name']} — {rec['reason']}", flush=True)
            if new is not None:
                ev.accept(new)
                accepted.append({"name": rec["name"], "hypothesis": rec["hypothesis"], "sql": rec["sql"],
                                 "columns": rec["columns"]})
                for c in rec["columns"]:
                    desc[c] = f"(에이전트 채택) {rec['name']}"
    log.close()
    (out_dir / "accepted.json").write_text(json.dumps(accepted, ensure_ascii=False, indent=2), encoding="utf-8")
    return history


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--per-round", type=int, default=4)
    ap.add_argument("--base", choices=["a", "b"], default="b")
    a = ap.parse_args()
    out = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-from-{a.base}"
    history = run(a.rounds, a.per_round, out_dir=out, base=a.base)
    dest = ACCEPTED[a.base]
    dest.write_text((out / "accepted.json").read_text(encoding="utf-8"), encoding="utf-8")
    n_ok = sum(h["decision"] == "채택" for h in history)
    print(f"끝: 제안 {len(history)}개 중 채택 {n_ok}개 → {dest.relative_to(ROOT)} · 기록 {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
