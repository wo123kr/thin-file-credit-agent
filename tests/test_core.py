"""uv run python -m unittest discover -s tests   (data/ 를 먼저 만들어야: uv run python src/data.py)"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data import DB  # noqa: E402
from features import validate_new  # noqa: E402
from metrics import approval_at_bad_rate, bad_rate_at_share, ks_stat, uplift_at_anchor  # noqa: E402
from sandbox import Sandbox, SqlRejected  # noqa: E402


class SandboxTest(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox(DB)

    def test_rejects_non_select_and_file_access(self):
        bad = ["DROP TABLE clients", "SELECT 1; SELECT 2", "SELECT * FROM read_csv('/etc/hosts')",
               "SELECT * FROM '/etc/hosts'", "COPY clients TO '/tmp/x.csv'", "ATTACH 'x.db'",
               "SET enable_external_access=true", "SELECT * FROM labels",
               "SELECT id FROM clients WHERE id IN (SELECT 1 FROM read_parquet('data/labels.parquet'))"]
        for q in bad:
            with self.subTest(q=q), self.assertRaises(SqlRejected):
                self.sb.run(q)

    def test_cte_name_does_not_hide_real_table_in_other_scope(self):
        # 검토에서 찾은 우회: 다른 범위의 CTE 이름이 같은 이름의 진짜 표 읽기를 가렸다
        q = "SELECT * FROM duckdb_databases z, (WITH duckdb_databases AS (SELECT 1 AS a) SELECT 1) t"
        with self.assertRaises(SqlRejected):
            self.sb.check(q)
        self.sb.check("WITH t AS (SELECT id FROM clients) SELECT id, 1 AS f_ab FROM t")   # 제 범위의 CTE 는 그대로 됨

    def test_non_string_sql_is_rejected_not_crash(self):
        for q in (None, 123, "", "   "):
            with self.subTest(q=q), self.assertRaises(SqlRejected):
                self.sb.run(q)

    def test_connection_itself_blocks_files_even_without_check(self):
        # 문장 검사를 건너뛰어도 두 번째 겹(읽기 전용 + 외부 접근 끔)이 막는다
        con = self.sb.connect()
        with self.assertRaises(duckdb.Error):
            con.execute("SELECT * FROM read_csv('/etc/hosts')").fetchall()
        with self.assertRaises(duckdb.Error):
            con.execute("CREATE TABLE x AS SELECT 1")
        with self.assertRaises(duckdb.Error):
            con.execute("SET enable_external_access = true")
        con.close()

    def test_db_has_no_label_or_protected_columns(self):
        con = self.sb.connect()
        cols = {r[0] for t in ("clients", "monthly") for r in con.execute(f"DESCRIBE {t}").fetchall()}
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        con.close()
        self.assertEqual(tables, {"clients", "monthly"})
        self.assertFalse(cols & {"is_default", "sex", "marriage", "age"})

    def test_timeout(self):
        q = "SELECT count(*) AS n FROM monthly a, monthly b, monthly c"
        with self.assertRaises(SqlRejected):
            self.sb.run(q, timeout_s=1)


class ValidateTest(unittest.TestCase):
    ids = pd.Index([1, 2, 3], name="id")

    def test_shape_rules(self):
        ok = pd.DataFrame({"id": [1, 2], "f_ab": [0.5, 1.0]})      # 이름은 f_ 뒤 2자 이상
        out = validate_new(ok, self.ids, ["limit_bal"])
        self.assertTrue(np.isnan(out.loc[3, "f_ab"]))      # 없는 고객은 결측
        cases = [pd.DataFrame({"x": [1]}),                                # id 없음
                 pd.DataFrame({"id": [1, 1], "f_a": [1, 2]}),             # 중복
                 pd.DataFrame({"id": [1], "Bad": [1]}),                   # 이름 규칙
                 pd.DataFrame({"id": [1], "limit_bal": [1]}),             # 이미 있는 이름(규칙도 위반)
                 pd.DataFrame({"id": [1], **{f"f_{i}x": [1] for i in range(4)}}),  # 4개
                 pd.DataFrame({"id": [1], "f_t": ["a"]}),                 # 숫자 아님
                 pd.DataFrame({"id": [[1]], "f_ab": [1]})]                 # id 가 리스트(검토에서 루프가 죽던 것)
        for c in cases:
            with self.subTest(cols=list(c.columns)), self.assertRaises(SqlRejected):
                validate_new(c, self.ids, ["limit_bal", "f_dup"])


class MetricsTest(unittest.TestCase):
    def test_ks(self):
        y = np.array([1, 1, 0, 1, 0, 0]); r = np.array([.9, .8, .7, .6, .5, .4])
        self.assertAlmostEqual(ks_stat(y, r), 2 / 3)

    def test_approval_at_bad_rate_hand(self):
        # 위험 낮은 순: 0(.1) 0(.2) 1(.3) 0(.4) 1(.5) — 누적 연체율 0, 0, 1/3, 1/4, 2/5
        y = np.array([0, 0, 1, 0, 1]); r = np.array([.1, .2, .3, .4, .5])
        self.assertAlmostEqual(approval_at_bad_rate(y, r, 0.25), 4 / 5)   # 4명까지 1/4
        self.assertAlmostEqual(approval_at_bad_rate(y, r, 0.0), 2 / 5)
        self.assertAlmostEqual(bad_rate_at_share(y, r, 0.6), 1 / 3)

    def test_ties_cut_together(self):
        y = np.array([0, 1]); r = np.array([.5, .5])     # 같은 점수는 같이 승인되거나 같이 거절
        self.assertAlmostEqual(approval_at_bad_rate(y, r, 0.0), 0.0)

    def test_perfect_model_uplift_positive(self):
        rng = np.random.default_rng(0)
        y = (rng.uniform(size=4000) < 0.2).astype(int)
        noisy = y + rng.normal(0, 1.5, 4000); sharp = y + rng.normal(0, 0.3, 4000)
        u = uplift_at_anchor(y, noisy, sharp, 0.7)
        self.assertGreater(u["uplift"], 0.05)


class LoopTest(unittest.TestCase):
    def test_fake_llm_round_trip(self):
        from agent.llm import FakeLLM
        from agent.loop import run
        good = {"name": "마지막 연체 이후 경과", "hypothesis": "시험용",
                "sql": "SELECT id, min(month) FILTER (WHERE status >= 1) AS f_months_since_delinq FROM monthly GROUP BY id"}
        broken = {"name": "깨진 SQL", "hypothesis": "시험용", "sql": "SELECT FROM"}
        evil = {"name": "라벨 훔치기", "hypothesis": "시험용", "sql": "SELECT id, is_default AS f_y FROM labels"}
        dup = {"name": "같은 정보", "hypothesis": "시험용",
               "sql": "SELECT id, limit_bal * 2 AS f_limit2 FROM clients"}
        fake = FakeLLM([json.dumps({"proposals": [good, broken, evil, dup]})])
        with tempfile.TemporaryDirectory() as d:
            hist = run(1, 4, llm=fake, out_dir=Path(d))
            logged = (Path(d) / "proposals.jsonl").read_text(encoding="utf-8").strip().splitlines()
        by = {h["name"]: h for h in hist}
        self.assertEqual(len(logged), 4)
        self.assertEqual(by["깨진 SQL"]["decision"], "오류")
        self.assertEqual(by["라벨 훔치기"]["decision"], "오류")
        self.assertIn("같은 정보", by["같은 정보"]["reason"])
        self.assertIn(by["마지막 연체 이후 경과"]["decision"], {"채택", "기각"})
        self.assertIn("delta_thin_mean", by["마지막 연체 이후 경과"])
        self.assertNotIn("is_default", fake.prompts[0])   # 프롬프트에 라벨 열 이름이 새지 않음

    def test_odd_llm_replies_do_not_kill_loop(self):
        from agent.llm import FakeLLM
        from agent.loop import run
        replies = [json.dumps({"proposals": {"not": "a list"}}),
                   json.dumps({"proposals": [{"name": "널 SQL", "hypothesis": "", "sql": None}, "문자열 제안"]})]
        with tempfile.TemporaryDirectory() as d:
            hist = run(2, 4, llm=FakeLLM(replies), out_dir=Path(d))
            self.assertTrue((Path(d) / "accepted.json").exists())
        self.assertTrue(all(h["decision"] == "오류" for h in hist))
        self.assertGreaterEqual(len(hist), 3)


class FinalGuardTest(unittest.TestCase):
    def test_second_open_is_blocked(self):
        import final
        with tempfile.TemporaryDirectory() as d:
            guard = Path(d) / "test_opened.json"
            guard.write_text('[{"opened_at": "x"}]', encoding="utf-8")
            old, final.GUARD = final.GUARD, guard
            try:
                with self.assertRaises(SystemExit):
                    final.main(force=False)
            finally:
                final.GUARD = old


if __name__ == "__main__":
    unittest.main()
