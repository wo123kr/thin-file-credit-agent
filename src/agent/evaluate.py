"""제안 하나를 검증해 채택 · 기각을 정한다. 결정은 전부 이 코드가 한다."""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from features import sandbox, validate_new
from metrics import auc
from model import cv_scores, folds
from sandbox import SqlRejected

MAX_MISSING = 0.95
LEAK_AUC = 0.85
DUP_CORR = 0.98
MIN_DELTA_THIN = 0.002
MIN_POS_SHARE = 0.7          # 15쌍 중 11쌍 이상에서 얇은 이력 AUC 가 올라야
MIN_DELTA_ALL = -0.001


@dataclass
class Evaluator:
    meta: pd.DataFrame          # id 색인: part · thin · is_default
    feats: pd.DataFrame         # id 색인: 지금 쓰는 피처(전체 고객)
    _base: dict | None = field(default=None, repr=False)

    def __post_init__(self):
        dev = self.meta["part"] == "dev"
        self.dev_ids = self.meta.index[dev]
        self.y = self.meta.loc[dev, "is_default"]
        self.thin = self.meta.loc[dev, "thin"]
        self.fold_list = folds(self.y, self.thin)

    def base_scores(self) -> dict:
        if self._base is None:
            self._base = cv_scores(self.feats.loc[self.dev_ids], self.y, self.thin, self.fold_list)
        return self._base

    def accept(self, new: pd.DataFrame) -> None:
        self.feats = self.feats.join(new)
        self._base = None

    def gates(self, new: pd.DataFrame) -> tuple[str | None, dict]:
        """CV 전에 거르는 검사. (기각 이유 또는 None, 수치)"""
        d = new.loc[self.dev_ids]
        info = {"missing": round(float(d.isna().mean().max()), 4)}
        if info["missing"] > MAX_MISSING:
            return f"결측 {info['missing']:.0%} 로 너무 많음", info
        single = [abs(auc(self.y.to_numpy(), d[c].fillna(d[c].median()).to_numpy()) - 0.5) + 0.5 for c in d]
        info["single_auc_max"] = round(float(max(single)), 4)
        if info["single_auc_max"] > LEAK_AUC:
            return f"피처 하나로 AUC {info['single_auc_max']:.3f} — 누수 의심", info
        base = self.feats.loc[self.dev_ids]
        for c in d:
            for b in base:
                r = spearmanr(d[c], base[b], nan_policy="omit").statistic
                if np.isfinite(r) and abs(r) > DUP_CORR:
                    return f"{b} 와 순위 상관 {r:.3f} — 같은 정보", info
        return None, info

    def evaluate(self, proposal: dict) -> tuple[dict, pd.DataFrame | None]:
        if not isinstance(proposal, dict):
            return {"name": str(proposal)[:60], "hypothesis": "", "sql": "", "decision": "오류",
                    "reason": "제안이 객체(JSON object)가 아님"}, None
        rec = {k: proposal.get(k) or "" for k in ("name", "hypothesis", "sql")}
        try:
            raw = sandbox().run(proposal.get("sql"))
            new = validate_new(raw, self.meta.index, list(self.feats.columns))
        except SqlRejected as e:
            return {**rec, "decision": "오류", "reason": str(e)}, None
        except Exception as e:  # noqa: BLE001 — 에이전트 출력이 낸 예상 밖 오류도 그 제안만 오류로 기록하고 루프는 계속
            return {**rec, "decision": "오류", "reason": f"처리 중 오류 {type(e).__name__}: {str(e)[:200]}"}, None
        rec["columns"] = list(new.columns)
        why, info = self.gates(new)
        rec.update(info)
        if why:
            return {**rec, "decision": "기각", "reason": why}, None
        return self._cv_decide(rec, new)

    def _cv_decide(self, rec: dict, new: pd.DataFrame) -> tuple[dict, pd.DataFrame | None]:
        base = self.base_scores()
        X = self.feats.join(new).loc[self.dev_ids]
        s = cv_scores(X, self.y, self.thin, self.fold_list)
        dt, da = s["thin"] - base["thin"], s["all"] - base["all"]
        rec.update(delta_thin_mean=round(float(dt.mean()), 4), delta_all_mean=round(float(da.mean()), 4),
                   pos_share=round(float((dt > 0).mean()), 3))   # 이유 문장과 같은 자릿수(4)로 한 번만 반올림
        ok = dt.mean() >= MIN_DELTA_THIN and (dt > 0).mean() >= MIN_POS_SHARE and da.mean() >= MIN_DELTA_ALL
        if ok:
            return {**rec, "decision": "채택", "reason": "기준 통과"}, new
        fails = []
        if dt.mean() < MIN_DELTA_THIN:
            fails.append(f"얇은 이력 ΔAUC 평균 {dt.mean():+.4f} < +{MIN_DELTA_THIN}")
        if (dt > 0).mean() < MIN_POS_SHARE:
            fails.append(f"오른 쌍 {(dt > 0).mean():.0%} < {MIN_POS_SHARE:.0%}")
        if da.mean() < MIN_DELTA_ALL:
            fails.append(f"전체 ΔAUC {da.mean():+.4f}")
        return {**rec, "decision": "기각", "reason": " · ".join(fails)}, None
