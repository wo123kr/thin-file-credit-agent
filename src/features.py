"""피처 묶음 조립: 사람이 쓴 SQL(A · B)과 에이전트가 낸 SQL 결과를 고객 id 로 붙인다."""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from data import DB, LABELS, ROOT, SPLIT
from sandbox import Sandbox, SqlRejected

SQL_DIR = ROOT / "sql"
MAX_NEW_COLS = 3
NAME_RE = re.compile(r"^f_[a-z0-9_]{2,40}$")


def sandbox() -> Sandbox:
    return Sandbox(DB)


def tier(name: str) -> pd.DataFrame:
    df = sandbox().run((SQL_DIR / f"tier_{name}.sql").read_text(encoding="utf-8"))
    return df.set_index("id").sort_index()


def frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(나누기 + 라벨, A · B 피처). 둘 다 id 순서."""
    meta = pd.read_parquet(SPLIT).merge(pd.read_parquet(LABELS), on="id").set_index("id").sort_index()
    feats = tier("a").join(tier("b"), how="left")
    return meta, feats.loc[meta.index]


def validate_new(df: pd.DataFrame, ids: pd.Index, existing: list[str]) -> pd.DataFrame:
    """에이전트 SQL 결과 모양 검사 → 고객 id 순서로 맞춘 새 피처 열들. 어긋나면 SqlRejected."""
    if "id" not in df.columns:
        raise SqlRejected("결과에 id 열이 없습니다")
    if not pd.api.types.is_integer_dtype(df["id"]):
        raise SqlRejected("id 는 정수 고객 번호여야 합니다")
    if df["id"].duplicated().any():
        raise SqlRejected("고객 1명이 여러 행입니다(id 중복). GROUP BY id 로 한 행씩 내 주세요")
    cols = [c for c in df.columns if c != "id"]
    if not 1 <= len(cols) <= MAX_NEW_COLS:
        raise SqlRejected(f"새 피처 열은 1~{MAX_NEW_COLS}개여야 합니다(지금 {len(cols)}개)")
    for c in cols:
        if not NAME_RE.match(c):
            raise SqlRejected(f"열 이름 {c!r}: f_ 로 시작하는 소문자 · 숫자 · 밑줄만 쓸 수 있습니다")
        if c in existing:
            raise SqlRejected(f"이미 있는 피처 이름입니다: {c}")
    out = df.set_index("id")[cols].reindex(ids)
    try:
        out = out.astype(float)
    except (TypeError, ValueError) as e:
        raise SqlRejected("숫자가 아닌 열이 있습니다") from e
    return out.replace([np.inf, -np.inf], np.nan)
