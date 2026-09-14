"""Phase 4 - Candidate model training, cross-validation, and selection.

- 5-fold StratifiedKFold CV (fixed seed) with the preprocessor refit inside each
  fold (no preprocessing leakage).
- Fit each candidate on the full training split, evaluate on VALIDATION.
- Imbalance mitigation: class_weight=balanced (LR/DT/RF) or balanced sample_weight
  (GradientBoosting); PR-AUC is the primary validation metric.
- Select the best model on validation (G6). Decision threshold tuned on validation
  against the Phase 2 cost matrix (G6). Refit the winner on train and persist it.
- The test set is NEVER used here.
"""

import _bootstrap  # noqa: F401

import json

import joblib
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.metrics import average_precision_score

from src.config import (
    get_seed,
    load_model_config,
    load_business_rules,
    models_path,
    docs_json,
    load_dataset,
)
from src.data.prepare import assert_gate4, target, split_frames, categorical_and_numeric
from src.model.preprocess import build_preprocessor
from src.model import models, selection

TREE_ENSEMBLE = "GradientBoostingClassifier"


def cv_average_precision(name, est, Xtr, ytr, cats, nums, seed, folds):
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    scores = []
    for tr, va in skf.split(Xtr, ytr):
        pre = build_preprocessor(nums, cats)
        Xt = pre.fit_transform(Xtr.iloc[tr])
        Xv = pre.transform(Xtr.iloc[va])
        e = type(est)(**est.get_params())
        if name == TREE_ENSEMBLE:
            e.fit(
                Xt,
                ytr.iloc[tr],
                sample_weight=models.balanced_sample_weight(ytr.iloc[tr]),
            )
        else:
            e.fit(Xt, ytr.iloc[tr])
        scores.append(average_precision_score(ytr.iloc[va], e.predict_proba(Xv)[:, 1]))
    return float(np.mean(scores)), float(np.std(scores))


def fit_on_train(name, est, Xt, ytr):
    if name == TREE_ENSEMBLE:
        est.fit(Xt, ytr, sample_weight=models.balanced_sample_weight(ytr))
    else:
        est.fit(Xt, ytr)
    return est


def main():
    approval = assert_gate4()
    seed = get_seed()
    mc = load_model_config()
    folds = mc["cross_validation"]["folds"]
    rules = load_business_rules()
    fn_cost = rules["cost_matrix"]["false_negative_cost"]
    fp_cost = rules["cost_matrix"]["false_positive_cost"]

    Xtr, Xval, Xtest, ytr, yval, ytest, cols = split_frames(load_dataset())
    cats, nums = categorical_and_numeric(cols)
    pre = joblib.load(models_path("preprocessor.joblib"))
    Xt = pre.transform(Xtr)
    Xv = pre.transform(Xval)

    results = []
    for name, est in models.get_candidates().items():
        fresh = type(est)(**est.get_params())
        cv_mean, cv_std = cv_average_precision(
            name, fresh, Xtr, ytr, cats, nums, seed, folds
        )

        est2 = type(est)(**est.get_params())
        fit_on_train(name, est2, Xt, ytr)
        proba_val = est2.predict_proba(Xv)[:, 1]
        pm = selection.probability_metrics(yval, proba_val)
        best_thr, _ = selection.optimize_threshold(yval, proba_val, fn_cost, fp_cost)
        at = selection.classify_metrics(
            yval, (proba_val >= best_thr["threshold"]).astype(int)
        )
        results.append(
            {
                "model": name,
                "cv_average_precision_mean": round(cv_mean, 4),
                "cv_average_precision_std": round(cv_std, 4),
                "val_roc_auc": round(pm["roc_auc"], 4),
                "val_pr_auc": round(pm["pr_auc_average_precision"], 4),
                "val_optimal_threshold": round(best_thr["threshold"], 3),
                "val_expected_cost_at_threshold": round(best_thr["expected_cost"], 4),
                "val_recall_at_threshold": round(at["recall"], 4),
                "val_precision_at_threshold": round(at["precision"], 4),
            }
        )
        print(
            "trained {:28s} val PR-AUC {:.4f} thr {:.3f} exp_cost {:.4f}".format(
                name,
                pm["pr_auc_average_precision"],
                best_thr["threshold"],
                best_thr["expected_cost"],
            )
        )

    best = max(
        results, key=lambda r: (r["val_pr_auc"], -r["val_expected_cost_at_threshold"])
    )
    best_name = best["model"]

    final_est = type(models.get_candidates()[best_name])(
        **models.get_candidates()[best_name].get_params()
    )
    fit_on_train(best_name, final_est, Xt, ytr)
    final_pipeline = Pipeline(steps=[("pre", pre), ("est", final_est)])
    joblib.dump(final_pipeline, models_path("final_model.joblib"))

    context = {
        "approved_target": target(),
        "approval_timestamp": approval["approval_timestamp"],
        "problem_type": "binary_classification",
        "seed": seed,
        "cv_folds": folds,
        "cost_matrix": {"false_negative_cost": fn_cost, "false_positive_cost": fp_cost},
        "primary_metric": "val_pr_auc_average_precision",
        "results": sorted(results, key=lambda r: -r["val_pr_auc"]),
        "selected_model": best_name,
        "selected_validation": best,
        "excluded_features": mc["feature_policy"]["excluded_features"],
        "note": "Threshold selected on validation only (G6). Test evaluation happens once in p4_evaluate_final_model.py.",
    }
    for path in [
        docs_json("model_candidates.json"),
        models_path("selection_context.json"),
    ]:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(context, fh, indent=2)
    print(
        "\nSELECTED:",
        best_name,
        "| val PR-AUC",
        best["val_pr_auc"],
        "| threshold",
        best["val_optimal_threshold"],
    )
    print("Wrote models/final_model.joblib and docs/json/model_candidates.json")


if __name__ == "__main__":
    main()
