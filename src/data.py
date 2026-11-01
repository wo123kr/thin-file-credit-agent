"""원본 엑셀 → 분석용 DuckDB(라벨 · 보호 속성 없음) + 라벨 · 보호 속성 · 나누기 파일.

uv run python src/data.py   # 한 번만. 다시 돌려도 같은 결과(고정 시드)
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
RAW_XLS = ROOT / "data" / "raw" / "default of credit card clients.xls"
DB = ROOT / "data" / "analysis.duckdb"
LABELS = ROOT / "data" / "labels.parquet"
PROTECTED = ROOT / "data" / "protected.parquet"
SPLIT = ROOT / "data" / "split.parquet"
SEED = 42
TEST_SHARE = 0.2
THIN_MAX_BILLED_MONTHS = 3     # 6개월 중 청구가 있던 달이 이 수 이하면 「얇은 이력」

STATUS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]   # 원본의 9월 상환 상태 이름이 PAY_0


def load_raw(path: Path = RAW_XLS) -> pd.DataFrame:
    df = pd.read_excel(path, header=1).rename(columns={"default payment next month": "is_default", "ID": "id"})
    if len(df) != 30000 or df["id"].duplicated().any():
        raise ValueError(f"원본 행 수가 예상과 다름: {len(df)}")
    return df


def to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """넓은 표 → 고객 × 달. month 1 = 9월(최근) … 6 = 4월."""
    parts = []
    for m in range(1, 7):
        parts.append(pd.DataFrame({"id": df["id"], "month": m, "status": df[STATUS[m - 1]],
                                   "bill": df[f"BILL_AMT{m}"].astype(float), "paid": df[f"PAY_AMT{m}"].astype(float)}))
    return pd.concat(parts, ignore_index=True).sort_values(["id", "month"]).reset_index(drop=True)


def thin_mask(monthly: pd.DataFrame) -> pd.Series:
    billed = monthly.assign(b=monthly["bill"] > 0).groupby("id")["b"].sum()
    return (billed <= THIN_MAX_BILLED_MONTHS).rename("thin")


def write_db(df: pd.DataFrame, monthly: pd.DataFrame, path: Path = DB) -> None:
    path.unlink(missing_ok=True)
    con = duckdb.connect(str(path))
    con.register("c", df[["id", "LIMIT_BAL", "EDUCATION"]].rename(columns=str.lower))
    con.register("m", monthly)
    con.execute("CREATE TABLE clients AS SELECT id, limit_bal::DOUBLE AS limit_bal, education FROM c")
    con.execute("CREATE TABLE monthly AS SELECT * FROM m")
    con.close()


def build() -> None:
    df = load_raw()
    monthly = to_monthly(df)
    write_db(df, monthly)
    df[["id", "is_default"]].to_parquet(LABELS, index=False)
    df[["id", "SEX", "MARRIAGE", "AGE"]].rename(columns=str.lower).to_parquet(PROTECTED, index=False)
    dev, test = train_test_split(df["id"], test_size=TEST_SHARE, stratify=df["is_default"], random_state=SEED)
    split = pd.DataFrame({"id": np.r_[dev, test], "part": ["dev"] * len(dev) + ["test"] * len(test)})
    split = split.merge(thin_mask(monthly).reset_index(), on="id").sort_values("id")
    split.to_parquet(SPLIT, index=False)
    print(split.groupby(["part", "thin"]).size().to_string())


if __name__ == "__main__":
    build()
