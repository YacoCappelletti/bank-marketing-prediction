"""Metric computation, threshold optimization (validation only, G6), calibration."""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

POS_LABEL = 1


def probability_metrics(y_true, proba_pos):
    proba_pos = np.asarray(proba_pos, dtype=float)
    return {
        "roc_auc": _safe(roc_auc_score, y_true, proba_pos),
        "pr_auc_average_precision": _safe(average_precision_score, y_true, proba_pos),
        "brier_score": _safe(brier_score_loss, y_true, proba_pos),
    }


def classify_metrics(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }


def expected_cost(y_true, y_pred, fn_cost, fp_cost):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    total = fn * fn_cost + fp * fp_cost
    return float(total / len(y_true)), int(fn), int(fp), int(tn), int(tp)


def optimize_threshold(y_true, proba_pos, fn_cost, fp_cost, grid=None):
    """Pick the threshold minimizing expected cost. Call on VALIDATION only (G6)."""
    if grid is None:
        grid = np.linspace(0.01, 0.99, 99)
    best = None
    curve = []
    y = np.asarray(y_true)
    p = np.asarray(proba_pos, dtype=float)
    for thr in grid:
        pred = (p >= thr).astype(int)
        cost, fn, fp, tn, tp = expected_cost(y, pred, fn_cost, fp_cost)
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        curve.append(
            {
                "threshold": round(float(thr), 3),
                "expected_cost": round(cost, 4),
                "recall": round(rec, 4),
                "precision": round(prec, 4),
            }
        )
        if best is None or cost < best["expected_cost"] - 1e-12:
            best = {
                "threshold": float(thr),
                "expected_cost": cost,
                "fn": fn,
                "fp": fp,
                "tn": tn,
                "tp": tp,
                "recall": rec,
                "precision": prec,
            }
    return best, curve


def default_threshold_metrics(y_true, proba_pos, fn_cost, fp_cost):
    """Metrics at the standard 0.5 cut for reference (not for tuning)."""
    pred = (np.asarray(proba_pos) >= 0.5).astype(int)
    return classify_metrics(y_true, pred)


def calibration_table(y_true, proba_pos, n_bins=10):
    y = np.asarray(y_true)
    p = np.asarray(proba_pos, dtype=float)
    edges = np.linspace(0, 1, n_bins + 1)
    rows = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (p >= lo) & (p < hi if i < n_bins - 1 else p <= hi)
        if mask.sum() == 0:
            continue
        rows.append(
            {
                "bin": "[{:.1f},{:.1f})".format(lo, hi),
                "count": int(mask.sum()),
                "mean_predicted": round(float(p[mask].mean()), 4),
                "observed_rate": round(float(y[mask].mean()), 4),
            }
        )
    return rows


def _safe(fn, *args):
    try:
        return float(fn(*args))
    except Exception:
        return None
