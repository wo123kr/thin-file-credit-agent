"""모형과 교차 검증. 모든 피처 묶음이 같은 모형 · 같은 겹을 쓴다."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold

from metrics import auc

SEED = 42
N_FOLDS = 5


def gbm() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(learning_rate=0.05, max_iter=400, max_leaf_nodes=15, min_samples_leaf=50,
                                          l2_regularization=1.0, early_stopping=True, validation_fraction=0.15,
                                          n_iter_no_change=30, random_state=SEED)


REPEAT_SEEDS = (42, 7, 2026)   # 5겹을 세 번 다르게 나눠 15쌍으로 비교(겹 하나의 우연을 줄이려고)


def folds(y: pd.Series, thin: pd.Series, seeds=REPEAT_SEEDS) -> list[tuple[np.ndarray, np.ndarray]]:
    """라벨 × 얇은 이력으로 층화해 겹마다 얇은 이력 고객 비율이 같게."""
    strata = y.to_numpy() * 2 + thin.to_numpy().astype(int)
    out = []
    for s in seeds:
        out += list(StratifiedKFold(N_FOLDS, shuffle=True, random_state=s).split(np.zeros(len(y)), strata))
    return out


def cv_scores(X: pd.DataFrame, y: pd.Series, thin: pd.Series, fold_list) -> dict:
    """겹마다 검증 AUC(전체 · 얇은 이력)."""
    out = {"all": [], "thin": []}
    yv, tv = y.to_numpy(), thin.to_numpy()
    for tr, va in fold_list:
        p = gbm().fit(X.iloc[tr], yv[tr]).predict_proba(X.iloc[va])[:, 1]
        out["all"].append(auc(yv[va], p))
        out["thin"].append(auc(yv[va][tv[va]], p[tv[va]]))
    return {k: np.asarray(v) for k, v in out.items()}
