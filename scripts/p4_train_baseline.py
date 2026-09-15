"""Phase 4 - Baseline model.

First action (G4): verify the target is user-approved. Then split (deterministic,
seed 42), fit the preprocessing on TRAIN ONLY, and evaluate a prior-probability
baseline on the VALIDATION split. The test set is not touched here.
"""

import _bootstrap  # noqa: F401

import json

import joblib
import numpy as np

from src.config import get_seed, load_model_config, models_path, docs_json
from src.data.prepare import assert_gate4, target, split_frames, categorical_and_numeric
from src.model.preprocess import build_preprocessor
from src.model import models, selection


def fit_preprocessor(cats, nums, X_train):
    """Always fit fresh from the current feature policy (no stale cached artifact)."""
    pre = build_preprocessor(nums, cats)
    pre.fit(X_train)
    joblib.dump(pre, models_path("preprocessor.joblib"))
    return pre


def main():
    approval = assert_gate4()
    seed = get_seed()
    Xtr, Xval, Xtest, ytr, yval, ytest, cols = split_frames(load_dataset())
    cats, nums = categorical_and_numeric(cols)
    pre = fit_preprocessor(cats, nums, Xtr)

    base = models.build_baseline()
    base.fit(pre.transform(Xtr), ytr)
    proba_val = base.predict_proba(pre.transform(Xval))[:, 1]

    pr_auc = selection.probability_metrics(yval, proba_val)["pr_auc_average_precision"]
    base_rate = float(np.mean(ytr))
    metrics = {
        "approved_target": target(),
        "approval_timestamp": approval["approval_timestamp"],
        "seed": seed,
        "baseline_model": "DummyClassifier(strategy='prior')",
        "train_positive_rate": round(base_rate, 4),
        "validation": {
            "pr_auc_average_precision": round(pr_auc, 4),
            "roc_auc": selection.probability_metrics(yval, proba_val)["roc_auc"],
            "accuracy_at_0.5": selection.default_threshold_metrics(
                yval, proba_val, 1, 1
            )["accuracy"],
        },
        "note": "Baseline floor. A useful model must beat this PR-AUC and expected cost on validation.",
        "split": {"train": len(Xtr), "val": len(Xval), "test": len(Xtest)},
    }
    with open(docs_json("baseline_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    print("Baseline:", json.dumps(metrics["validation"], indent=2))
    print("Wrote docs/json/baseline_metrics.json and models/preprocessor.joblib")


if __name__ == "__main__":
    main()
