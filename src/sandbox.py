"""SQL 을 안전하게 돌리는 곳. 사람이 쓴 SQL 도, 에이전트가 낸 SQL 도 여기서만 돈다.

겹겹이 막는다:
1. 문장 검사: DuckDB 의 json_serialize_sql 은 SELECT 문 하나만 직렬화한다 → 그 밖의 문장은 여기서 걸린다.
   직렬화된 구문 나무에서 읽는 표는 clients · monthly 뿐이어야 하고, 표 함수(read_csv 등)는 쓸 수 없다.
2. 연결: DB 파일을 읽기 전용으로 열고, 외부 접근(파일 · 네트워크)을 끈 뒤 설정을 잠근다.
3. 시간: 제한을 넘기면 쿼리를 끊는다.
"""
import json
import threading
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

ALLOWED_TABLES = {"clients", "monthly"}
TIMEOUT_S = 30


class SqlRejected(Exception):
    """검사에서 막힌 SQL. 메시지는 에이전트에게 그대로 돌려준다."""


@dataclass
class Sandbox:
    db_path: Path

    def connect(self) -> duckdb.DuckDBPyConnection:
        con = duckdb.connect(str(self.db_path), read_only=True)
        con.execute("SET enable_external_access = false")
        con.execute("SET lock_configuration = true")
        return con

    def check(self, sql: str) -> None:
        if not isinstance(sql, str) or not sql.strip():
            raise SqlRejected("SQL 이 비었거나 문자열이 아닙니다")
        con = duckdb.connect()   # 문장 검사는 빈 메모리 DB 에서(표가 없어도 직렬화는 된다)
        try:
            raw = con.execute("SELECT json_serialize_sql(?::VARCHAR)", [sql]).fetchone()[0]
        finally:
            con.close()
        tree = json.loads(raw)
        if tree.get("error"):
            raise SqlRejected(f"SELECT 문 하나만 쓸 수 있습니다: {tree.get('error_message', '')[:200]}")
        if len(tree.get("statements", [])) != 1:
            raise SqlRejected("문장은 하나만 쓸 수 있습니다")
        tables, table_funcs = set(), []
        _walk(tree, tables, table_funcs, frozenset())
        if table_funcs:
            raise SqlRejected(f"표 함수는 쓸 수 없습니다: {table_funcs}")
        bad = tables - ALLOWED_TABLES
        if bad:
            raise SqlRejected(f"읽을 수 없는 표: {sorted(bad)} (쓸 수 있는 표: clients, monthly)")

    def run(self, sql: str, timeout_s: int = TIMEOUT_S) -> pd.DataFrame:
        self.check(sql)
        con = self.connect()
        timer = threading.Timer(timeout_s, con.interrupt)
        timer.start()
        try:
            return con.execute(sql).df()
        except duckdb.InterruptException as e:
            raise SqlRejected(f"{timeout_s}초 안에 끝나지 않았습니다") from e
        except duckdb.Error as e:
            raise SqlRejected(f"SQL 오류: {str(e)[:300]}") from e
        finally:
            timer.cancel()
            con.close()


def _walk(node, tables: set, table_funcs: list, scope: frozenset) -> None:
    """구문 나무에서 읽는 진짜 표 이름과 표 함수를 모은다.

    CTE 이름은 그 CTE 가 정의된 범위(그 아래 나무) 안에서만 표가 아닌 것으로 본다.
    다른 범위의 같은 이름 표를 가리지 않게(예: 바깥에서 진짜 표 x 를 읽고 안쪽 CTE 이름도 x).
    """
    if isinstance(node, dict):
        cte = node.get("cte_map", {}).get("map") if isinstance(node.get("cte_map"), dict) else None
        if cte:
            scope = scope | {str(item.get("key", "")).lower() for item in cte}
        if node.get("type") == "BASE_TABLE":
            name = str(node.get("table_name", "")).lower()
            if name not in scope or node.get("schema_name") or node.get("catalog_name"):
                tables.add(name)
        if node.get("type") == "TABLE_FUNCTION":
            table_funcs.append(str(node.get("function", {}).get("function_name", "?")))
        for v in node.values():
            _walk(v, tables, table_funcs, scope)
    elif isinstance(node, list):
        for v in node:
            _walk(v, tables, table_funcs, scope)
