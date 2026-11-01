"""지표: AUC · KS, 같은 연체율에서의 승인율, 부트스트랩 구간."""
import numpy as np
from sklearn.metrics import roc_auc_score


def auc(y: np.ndarray, risk: np.ndarray) -> float:
    return float(roc_auc_score(y, risk))


def ks_stat(y: np.ndarray, risk: np.ndarray) -> float:
    """연체자와 정상 고객의 누적 분포 차이의 최댓값(risk 가 클수록 위험). 같은 점수는 한 번에 넘긴다."""
    order = np.argsort(-risk, kind="mergesort")
    ys, rs = np.asarray(y)[order], np.asarray(risk)[order]
    cum_bad = np.cumsum(ys) / ys.sum()
    cum_good = np.cumsum(1 - ys) / (len(ys) - ys.sum())
    last_of_tie = np.r_[rs[1:] != rs[:-1], True]
    return float(np.max(np.abs(cum_bad - cum_good)[last_of_tie]))


def _cum_by_tie(y: np.ndarray, risk: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """덜 위험한 순으로 승인한다고 볼 때, 끊을 수 있는 자리(같은 점수 묶음의 끝)마다 승인 인원 · 승인자 연체 수."""
    order = np.argsort(risk, kind="mergesort")
    ys, rs = np.asarray(y)[order], np.asarray(risk)[order]
    cut = np.r_[rs[1:] != rs[:-1], True]
    k = np.arange(1, len(ys) + 1)[cut]
    bad = np.cumsum(ys)[cut]
    return k, bad


def bad_rate_at_share(y: np.ndarray, risk: np.ndarray, share: float) -> float:
    """위험이 낮은 순으로 share 만큼 승인했을 때 승인자 연체율(가장 가까운 끊을 자리)."""
    k, bad = _cum_by_tie(y, risk)
    i = int(np.argmin(np.abs(k - share * len(y))))
    return float(bad[i] / k[i])


def approval_at_bad_rate(y: np.ndarray, risk: np.ndarray, max_bad_rate: float) -> float:
    """승인자 연체율이 max_bad_rate 를 넘지 않게 승인할 수 있는 최대 비율."""
    k, bad = _cum_by_tie(y, risk)
    ok = bad / k <= max_bad_rate + 1e-12
    return float(k[ok].max() / len(y)) if ok.any() else 0.0


def uplift_at_anchor(y: np.ndarray, risk_base: np.ndarray, risk_new: np.ndarray, share: float) -> dict:
    """기준 모형이 share 를 승인할 때의 연체율에서, 새 모형이 승인할 수 있는 비율과 그 차이."""
    target = bad_rate_at_share(y, risk_base, share)
    base = approval_at_bad_rate(y, risk_base, target)
    new = approval_at_bad_rate(y, risk_new, target)
    return {"target_bad_rate": target, "approve_base": base, "approve_new": new, "uplift": new - base}


def bootstrap_uplift(y: np.ndarray, risk_base: np.ndarray, risk_new: np.ndarray, share: float,
                     n: int = 1000, seed: int = 0) -> dict:
    """같은 표본을 다시 뽑아 기준 연체율을 매번 다시 정하고 승인율 차이를 잰다(짝지은 비교)."""
    rng = np.random.default_rng(seed)
    y, rb, rn = map(np.asarray, (y, risk_base, risk_new))
    ups = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].sum() == 0:
            continue
        ups.append(uplift_at_anchor(y[idx], rb[idx], rn[idx], share)["uplift"])
    lo, hi = np.percentile(ups, [2.5, 97.5])
    return {"ci95": [float(lo), float(hi)], "share_positive": float(np.mean(np.asarray(ups) > 0)), "n": len(ups)}
