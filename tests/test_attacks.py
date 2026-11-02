"""샌드박스 공격 문장 모음 — 새 눈 검토(2026-11-02) 때 손으로 넣어 본 문장을 시험으로 옮긴 것.

라벨 파일 · 다른 파일 · 네트워크 · 시스템 표 · 설정 변경 · 쓰기를 노리는 문장이 모두 막히는지 본다.
두 겹을 따로 확인한다: (1) 문장 검사 + 실행(Sandbox.run) (2) 문장 검사를 건너뛴 연결 자체.
해가 없는 문장(VALUES · 재귀 CTE · 두 표 조회)은 여기 넣지 않는다 — 통과해도 라벨에 닿지 않는다.
알려진 틈(검토 2026-11-03): SHOW 문(SHOW ALL TABLES 등)과 카탈로그를 붙인 이름(analysis.main.clients)은
문장 검사를 통과하고, 스칼라 함수는 검사하지 않는다. 메타데이터 · 허용된 두 표만 보이고 라벨에는 닿지 않아
연결 겹이 막는 것으로 두었다 — README 「알려진 틈」.

uv run python -m unittest discover -s tests   (data/ 를 먼저 만들어야: uv run python src/data.py)
"""
import sys
import unittest
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data import DB  # noqa: E402
from sandbox import Sandbox, SqlRejected  # noqa: E402

L = "data/labels.parquet"
A = str(ROOT / L)

# 문장 검사(Sandbox.check)에서 막혀야 하는 것 — 실행 중 우연한 SQL 오류로 막힌 것은 넣지 않는다
RUN_LAYER = {
    # 파일을 표처럼 읽기(replacement scan) · 표 함수
    "replacement_scan": f"SELECT * FROM '{L}'",
    "replacement_scan_abs": f"SELECT * FROM '{A}'",
    "from_first": f"FROM '{L}'",
    "read_parquet": f"SELECT * FROM read_parquet('{L}')",
    "read_text": f"SELECT content FROM read_text('{L}')",
    "parquet_metadata": f"SELECT * FROM parquet_metadata('{L}')",
    "glob": "SELECT * FROM glob('*')",
    "query_tf": f"SELECT * FROM query('SELECT * FROM ''{L}''')",
    "query_table": "SELECT * FROM query_table('clients')",
    "pragma_func": "SELECT * FROM pragma_table_info('clients')",
    "duckdb_secrets": "SELECT * FROM duckdb_secrets()",
    "generate_series": "SELECT * FROM generate_series(1,3)",
    "http": "SELECT * FROM 'https://example.com/x.csv'",
    # 다른 자리에 숨기기
    "scalar_subquery": f"SELECT (SELECT count(*) FROM read_parquet('{L}')) AS x",
    "cte": f"WITH x AS (SELECT * FROM read_parquet('{L}')) SELECT * FROM x",
    "union": f"SELECT id FROM clients UNION ALL SELECT id FROM read_csv('{L}')",
    "lateral": f"SELECT c.id FROM clients c, LATERAL (SELECT * FROM '{L}') x",
    "exists": f"SELECT list(x) FROM (SELECT 1 AS x) WHERE EXISTS (FROM '{L}')",
    "in_subquery": f"SELECT id FROM clients WHERE id IN (SELECT 1 FROM read_parquet('{L}'))",
    # CTE 이름으로 진짜 파일 · 시스템 표 가리기
    "cte_name_then_real_file": f"SELECT * FROM (WITH q AS (SELECT 1 AS a) SELECT * FROM q) t, '{L}' AS q",
    "cte_shadow_outer_ref": f"SELECT * FROM '{L}' AS z, (WITH \"{L}\" AS (SELECT 1 AS a) SELECT * FROM \"{L}\") t",
    "cte_shadow_inner_then_file": f"SELECT * FROM (WITH \"{L}\" AS (SELECT 1 AS a) SELECT * FROM \"{L}\") t, '{L}' z",
    "cte_shadow_sys_inner": "SELECT * FROM (WITH duckdb_databases AS (SELECT 1 AS a) SELECT * FROM duckdb_databases) t, duckdb_databases z",
    "cte_shadow_sys_outer": "SELECT * FROM duckdb_databases z, (WITH duckdb_databases AS (SELECT 1 AS a) SELECT 1) t",
    "cte_shadow_settings": "SELECT * FROM duckdb_settings z, (WITH duckdb_settings AS (SELECT 1 AS a) SELECT 1) t",
    # 시스템 표 · 다른 카탈로그
    "duckdb_tables": "SELECT * FROM duckdb_tables",
    "duckdb_settings": "SELECT * FROM duckdb_settings",
    "information_schema": "SELECT * FROM information_schema.tables",
    "labels_table": "SELECT * FROM labels",
    # SELECT 가 아닌 문장
    "describe_file": f"DESCRIBE '{L}'",
    "summarize_file": f"SUMMARIZE '{L}'",
    "summarize_select_file": f"SUMMARIZE SELECT * FROM '{L}'",
    "summarize_sys": "SUMMARIZE duckdb_databases",
    "describe_sys": "DESCRIBE duckdb_settings",
    "pivot": "PIVOT monthly ON month USING sum(bill)",
    "explain": "EXPLAIN SELECT * FROM clients",
    "set": "SET enable_external_access=true",
    "attach": f"ATTACH '{L}'",
    "copy": "COPY (SELECT * FROM clients) TO '/tmp/x.csv'",
    "install": "INSTALL httpfs",
    "load": "LOAD httpfs",
    "drop": "DROP TABLE clients",
    "two_statements": "SELECT 1; SELECT 2",
}

# 문장 검사를 건너뛰고 연결에 바로 넣어도 막혀야 하는 것
CONNECTION_LAYER = {
    "read_parquet": f"SELECT * FROM read_parquet('{L}') LIMIT 1",
    "read_text": f"SELECT * FROM read_text('{L}')",
    "glob": "SELECT * FROM glob('*')",
    "http": "SELECT * FROM 'https://example.com/a.csv'",
    "set_external": "SET enable_external_access=true",
    "unlock": "SET lock_configuration=false",
    "allowed_dirs": "SET allowed_directories=['/']",
    "memory_limit": "SET memory_limit='1GB'",
    "pragma_threads": "PRAGMA threads=1",
    "create_table": "CREATE TABLE t AS SELECT 1",
    "insert": "INSERT INTO clients VALUES (1,1,1)",
    "copy": "COPY clients TO '/tmp/zz.csv'",
    "attach_file": f"ATTACH '{L}' AS x",
    "attach_memory": "ATTACH ':memory:' AS mm",
    "install": "INSTALL httpfs",
    "load": "LOAD httpfs",
}


class AttackCorpusTest(unittest.TestCase):
    def test_run_layer_rejects_every_attack(self):
        sb = Sandbox(DB)
        for name, q in RUN_LAYER.items():
            with self.subTest(name=name), self.assertRaises(SqlRejected):
                sb.check(q)          # 실행 전 문장 검사에서 막혀야 한다
            with self.subTest(name=name + ":run"), self.assertRaises(SqlRejected):
                sb.run(q, timeout_s=10)

    def test_connection_layer_blocks_without_statement_check(self):
        sb = Sandbox(DB)
        con = sb.connect()
        try:
            for name, q in CONNECTION_LAYER.items():
                with self.subTest(name=name), self.assertRaises(duckdb.Error):
                    con.execute(q).fetchall()
        finally:
            con.close()

    def test_corpus_size(self):
        # 포트폴리오 · README 의 「공격 문장 N개」가 이 숫자와 같아야 한다
        self.assertEqual(len(RUN_LAYER) + len(CONNECTION_LAYER), 59)


if __name__ == "__main__":
    unittest.main()
