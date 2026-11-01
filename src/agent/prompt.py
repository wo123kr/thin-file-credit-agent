"""에이전트에게 주는 글. 라벨 값 · 시험 데이터 성적은 절대 넣지 않는다(코드가 만든 개발 데이터 수치만)."""
import json

SYSTEM = """너는 신용평가 팀의 피처 엔지니어다. 대만 신용카드 고객 데이터에서 「이력이 얇은 고객」의 다음 달 연체를 더 잘 가르는 피처를 제안한다.
너는 숫자를 정하지 않는다. 너는 가설과 SQL 만 내고, 채택 여부는 검증 코드가 정한다.
반드시 JSON 객체 하나로만 답한다."""

DICTIONARY = """## 데이터(DuckDB, 읽기 전용)
- clients(id, limit_bal, education)
  - limit_bal: 카드 한도(대만 달러)
  - education: 1 대학원, 2 대학, 3 고교, 4 기타, 0 · 5 · 6 설명 없는 값
- monthly(id, month, status, bill, paid) — 고객 × 달, 고객마다 6행
  - month: 1 = 2005년 9월(가장 최근) … 6 = 2005년 4월
  - status: 그 달 상환 상태. -2 사용 없음, -1 전액 납부, 0 리볼빙(최소 금액 납부), 1~9 = 그만큼의 달 수 연체
  - bill: 그 달 청구액(음수 = 과납)
  - paid: 그 달 낸 금액(보통 직전 달 청구분에 대한 납부)
- 라벨(10월 연체 여부)과 성별 · 혼인 · 나이는 이 DB 에 없다. 지역 정보도 없다.
- 「이력이 얇은 고객」 = 6개월 중 bill > 0 인 달이 3달 이하인 고객(전체의 약 12.6%)."""

RULES = """## SQL 규칙
- DuckDB SQL, SELECT 문 하나(WITH 가능). 표는 clients, monthly 만.
- 결과: id 열 + 새 피처 1~3개. 고객 1명 = 1행(GROUP BY id 또는 clients 기준 LEFT JOIN).
- 새 열 이름은 f_ 로 시작하는 소문자 · 숫자 · 밑줄. 이미 있는 피처와 이름이 겹치면 안 된다.
- 0 으로 나누기는 NULLIF 로 막는다. 정의할 수 없는 값은 NULL 로 둔다(모형이 결측을 따로 다룬다).
- 지금 피처를 단순히 비율 · 단위만 바꾼 것은 도움이 안 된다. 얇은 이력 고객에서 「아직 안 쓴 정보」를 찾아라
  (예: 순서 · 타이밍 · 변화 · 일관성 · 마지막 사용 이후 경과 · 청구와 납부의 짝 등)."""

OUTPUT = """## 답 형식(JSON 만)
{"proposals": [{"name": "짧은 이름", "hypothesis": "왜 얇은 이력 고객의 연체를 가를지 한국어 1~2문장", "sql": "SELECT ..."}]}"""


def feature_list(descriptions: dict[str, str]) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in descriptions.items())


def history_text(history: list[dict]) -> str:
    if not history:
        return "(아직 없음)"
    rows = []
    for h in history[-20:]:
        d = h.get("delta_thin_mean")
        num = f"ΔAUC(얇은 이력) {d:+.4f}, ΔAUC(전체) {h.get('delta_all_mean', 0):+.4f}" if d is not None else ""
        rows.append(f"- [{h['decision']}] {h['name']} — {h['hypothesis']} | {num} | 이유: {h['reason']}")
    return "\n".join(rows)


def build(descriptions: dict[str, str], history: list[dict], n: int) -> str:
    return "\n\n".join([
        DICTIONARY,
        "## 지금 모형이 쓰는 피처\n" + feature_list(descriptions),
        "## 지난 제안과 결과(개발 데이터 교차 검증)\n" + history_text(history),
        RULES,
        f"## 할 일\n새 피처 제안 {n}개를 내라. 지난 제안에서 배운 점을 반영하고, 기각된 방향을 반복하지 마라.",
        OUTPUT,
    ])


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
