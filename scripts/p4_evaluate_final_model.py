"""Phase 4 - Final model evaluation on the test set (EXACTLY ONCE, G6), global
feature importance, persisted SHAP explainer, metadata, charts, and reports.

The decision threshold is carried over unchanged from validation (selected in the
candidates script). The test set is used for this single evaluation only; it was
never used for selection or tuning.
"""

import _bootstrap  # noqa: F401

import json
import platform
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sklearn
import shap as _shap
from sklearn.metrics import (
    roc_curve,
    precision_recall_curve,
    roc_auc_score,
    average_precision_score,
)

from src.config import (
    get_seed,
    load_model_config,
    load_business_rules,
    load_dataset,
    models_path,
    docs_json,
    docs_path,
)
from src.data.prepare import assert_gate4, target, split_frames, categorical_and_numeric
from src.model import selection, explain

VERSION = "1.0.0"


def main():
    approval = assert_gate4()  # G4 re-check
    seed = get_seed()
    ctx = json.load(open(models_path("selection_context.json"), encoding="utf-8"))
    threshold = ctx["selected_validation"]["val_optimal_threshold"]
    fn_cost = ctx["cost_matrix"]["false_negative_cost"]
    fp_cost = ctx["cost_matrix"]["false_positive_cost"]

    Xtr, Xval, Xtest, ytr, yval, ytest, cols = split_frames(load_dataset())
    cats, nums = categorical_and_numeric(cols)
    pipeline = joblib.load(models_path("final_model.joblib"))
    model_name = ctx["selected_model"]

    # ---- SINGLE test-set forward pass (G6) ----
    proba_test = pipeline.predict_proba(Xtest)[:, 1]
    pred_test = (proba_test >= threshold).astype(int)
    test_prob = selection.probability_metrics(ytest, proba_test)
    test_cls = selection.classify_metrics(ytest, pred_test)
    test_cost, fn, fp, tn, tp = selection.expected_cost(
        ytest, pred_test, fn_cost, fp_cost
    )

    # ---- validation (reusable) for calibration + threshold curve ----
    proba_val = pipeline.predict_proba(Xval)[:, 1]
    val_prob = selection.probability_metrics(yval, proba_val)
    val_cls = selection.classify_metrics(yval, (proba_val >= threshold).astype(int))
    calib = selection.calibration_table(yval, proba_val)

    # ---- global importance (permutation on validation) ----
    fi = explain.global_permutation_importance(pipeline, Xval, yval, seed=seed)
    with open(docs_json("feature_importance.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "method": "permutation_importance",
                "scoring": "average_precision",
                "split": "validation",
                "features": fi,
            },
            fh,
            indent=2,
        )

    # ---- local explainer ----
    spec = explain.build_explainer(pipeline, Xtr, model_name, seed)
    joblib.dump(spec, models_path("explainer.joblib"))

    # ---- charts ----
    chart = make_charts(ytest, proba_test, threshold, fi, calib, model_name)

    perf = {
        "model": model_name,
        "threshold": threshold,
        "cost_matrix": {"false_negative_cost": fn_cost, "false_positive_cost": fp_cost},
        "test": {
            "roc_auc": round(test_prob["roc_auc"], 4),
            "pr_auc_average_precision": round(test_prob["pr_auc_average_precision"], 4),
            "brier_score": round(test_prob["brier_score"], 4),
            "accuracy": round(test_cls["accuracy"], 4),
            "precision": round(test_cls["precision"], 4),
            "recall": round(test_cls["recall"], 4),
            "f1": round(test_cls["f1"], 4),
            "confusion_matrix": test_cls["confusion_matrix"],
            "expected_cost_per_client": round(test_cost, 4),
        },
        "validation": {
            "roc_auc": round(val_prob["roc_auc"], 4),
            "pr_auc_average_precision": round(val_prob["pr_auc_average_precision"], 4),
            "accuracy": round(val_cls["accuracy"], 4),
            "recall": round(val_cls["recall"], 4),
            "precision": round(val_cls["precision"], 4),
        },
        "baseline_reference": json.load(
            open(docs_json("baseline_metrics.json"), encoding="utf-8")
        ),
        "note": "Test evaluated exactly once (G6). Threshold from validation only.",
    }
    with open(docs_json("model_performance.json"), "w", encoding="utf-8") as fh:
        json.dump(perf, fh, indent=2)

    meta = build_metadata(
        model_name,
        threshold,
        cols,
        cats,
        nums,
        len(fi),
        seed,
        approval,
        perf,
        len(Xtr),
        len(Xval),
        len(Xtest),
    )
    with open(models_path("model_metadata.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    write_reports(ctx, perf, fi, calib, approval, threshold, model_name, meta)

    print(
        "TEST  PR-AUC {:.4f} ROC {:.4f} recall {:.4f} precision {:.4f} f1 {:.4f} exp_cost {:.4f}".format(
            perf["test"]["pr_auc_average_precision"],
            perf["test"]["roc_auc"],
            perf["test"]["recall"],
            perf["test"]["precision"],
            perf["test"]["f1"],
            perf["test"]["expected_cost_per_client"],
        )
    )
    print(
        "Wrote model_metadata.json, explainer.joblib, model_performance.json, feature_importance.json, charts, reports"
    )


def build_metadata(
    model_name,
    threshold,
    cols,
    cats,
    nums,
    n_fi,
    seed,
    approval,
    perf,
    ntr,
    nval,
    ntest,
):
    return {
        "model_name": model_name,
        "model_version": VERSION,
        "approved_target": target(),
        "problem_type": "binary_classification",
        "target_approval_reference": {
            "path": "docs/json/target_approval.json",
            "approval_status": approval["approval_status"],
            "approval_timestamp": approval["approval_timestamp"],
        },
        "training_timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "random_seed": seed,
        "feature_columns": cols,
        "excluded_features": load_model_config()["feature_policy"]["excluded_features"],
        "feature_types": {"numeric": nums, "categorical": cats},
        "preprocessing_summary": "Median impute + StandardScaler (numeric); most-frequent impute + one-hot, handle_unknown=ignore (categorical). Fit on TRAIN only. pdays 999 sentinel -> previously_contacted flag + pdays_days; age clipped [18,95].",
        "split_strategy": "Stratified 70/15/15 on the target, seed 42. Justification: no row-level chronological field exists (only cyclic month/day-of-week), so a stratified split preserves class balance; see model_report.md.",
        "split_sizes": {"train": ntr, "validation": nval, "test": ntest},
        "chosen_decision_threshold": threshold,
        "threshold_selection": "validation-only minimization of expected cost (G6)",
        "cost_matrix": perf["cost_matrix"],
        "validation_metrics": perf["validation"],
        "test_metrics": perf["test"],
        "library_versions": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "shap": _shap.__version__,
        },
        "notes_limitations": [
            "Term-deposit response model for the historical (2008-2010) campaign context.",
            "duration/poutcome/campaign excluded per user-approved feature policy.",
            "Class imbalance handled via balanced weights; PR-AUC primary metric.",
            "Macro-indicator drift may limit transfer to future economic regimes.",
        ],
    }


def make_charts(ytest, proba, thr, fi, calib, model_name):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fpr, tpr, _ = roc_curve(ytest, proba)
    axes[0, 0].plot(fpr, tpr, color="#2b6cb0")
    axes[0, 0].plot([0, 1], [0, 1], "--", c="grey")
    axes[0, 0].set_title("ROC (test) AUC={:.3f}".format(roc_auc_score(ytest, proba)))
    axes[0, 0].set_xlabel("FPR")
    axes[0, 0].set_ylabel("TPR")

    prec, rec, _ = precision_recall_curve(ytest, proba)
    ap = average_precision_score(ytest, proba)
    axes[0, 1].plot(rec, prec, color="#c05621")
    axes[0, 1].axhline(float(np.mean(ytest)), ls="--", c="grey", label="base rate")
    axes[0, 1].set_title("Precision-Recall (test) AP={:.3f}".format(ap))
    axes[0, 1].set_xlabel("Recall")
    axes[0, 1].set_ylabel("Precision")
    axes[0, 1].legend()

    top = fi[:12]
    names = [t["feature"] for t in top][::-1]
    vals = [t["importance_mean"] for t in top][::-1]
    axes[1, 0].barh(names, vals, color="#2c7a7b")
    axes[1, 0].set_title("Top permutation importance (validation)")
    axes[1, 0].tick_params(labelsize=7)

    if calib:
        axes[1, 1].plot(
            [c["mean_predicted"] for c in calib],
            [c["observed_rate"] for c in calib],
            "o-",
            color="#6b46c1",
        )
        axes[1, 1].plot([0, 1], [0, 1], "--", c="grey")
        axes[1, 1].set_title("Calibration (validation)")
        axes[1, 1].set_xlabel("mean predicted")
        axes[1, 1].set_ylabel("observed rate")

    fig.suptitle("{} - model performance".format(model_name))
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    path = docs_path("images", "model_performance_charts.png")
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


def _bar(name, val, fmt="{:.4f}"):
    return "| {} | {} |".format(name, fmt.format(val))


def write_reports(ctx, perf, fi, calib, approval, threshold, model_name, meta):
    t = perf["test"]
    v = perf["validation"]
    cm = t["confusion_matrix"]
    lines = []
    lines.append("# Model Report - Phase 4\n")
    lines.append("## Decision: classification vs regression\n")
    lines.append(
        "The user approved target **{}** is a binary outcome (term-deposit subscription), so this is "
        "**binary classification**. The business wants a decision (contact / priority tier), which "
        "maps naturally to a probability and a threshold, matching the Phase 2 band structure and the "
        "20:1 cost matrix (see `configs/business_rules.json`).\n".format(target())
    )
    lines.append("## Governance\n")
    lines.append(
        "- Target approval: `docs/json/target_approval.json` (status **{}**, {}).".format(
            approval["approval_status"], approval["approval_timestamp"]
        )
    )
    lines.append(
        "- Seed {} fixed across split, CV, and every model.".format(meta["random_seed"])
    )
    lines.append(
        "- Feature policy (user-approved): EXCLUDE {}.".format(
            ", ".join(meta["excluded_features"])
        )
    )
    lines.append(
        "- Test set evaluated exactly once at the validation-chosen threshold (G6).\n"
    )

    lines.append("## Split strategy\n")
    lines.append(meta["split_strategy"] + "\n")
    lines.append(
        "Sizes: train {train:,}, validation {val:,}, test {test:,}.\n".format(
            train=meta["split_sizes"]["train"],
            val=meta["split_sizes"]["validation"],
            test=meta["split_sizes"]["test"],
        )
    )

    lines.append("## Preprocessing\n")
    lines.append(meta["preprocessing_summary"] + "\n")

    lines.append("## Candidate selection (validation)\n")
    lines.append(
        "| Model | CV AP (mean) | Val PR-AUC | Val ROC-AUC | Thr | Val exp. cost |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in ctx["results"]:
        lines.append(
            "| {model} | {cv:.4f} | {vp:.4f} | {vr:.4f} | {th:.3f} | {ec:.4f} |".format(
                model=r["model"],
                cv=r["cv_average_precision_mean"],
                vp=r["val_pr_auc"],
                vr=r["val_roc_auc"],
                th=r["val_optimal_threshold"],
                ec=r["val_expected_cost_at_threshold"],
            )
        )
    lines.append("\nSelected **{}** on validation PR-AUC.\n".format(model_name))

    lines.append("## Decision threshold\n")
    lines.append(
        "Threshold **{}** chosen on validation by minimizing expected cost with "
        "false_negative_cost={}, false_positive_cost={} (recall-leaning: missing a "
        "subscriber is weighted far above a wasted contact).\n".format(
            threshold,
            ctx["cost_matrix"]["false_negative_cost"],
            ctx["cost_matrix"]["false_positive_cost"],
        )
    )

    lines.append("## Test results (single evaluation)\n")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    for row in [
        _bar("Accuracy", t["accuracy"]),
        _bar("Precision", t["precision"]),
        _bar("Recall", t["recall"]),
        _bar("F1", t["f1"]),
        _bar("ROC-AUC", t["roc_auc"]),
        _bar("PR-AUC (avg precision)", t["pr_auc_average_precision"]),
        _bar("Brier score", t["brier_score"]),
        _bar("Expected cost / client", t["expected_cost_per_client"]),
    ]:
        lines.append(row)
    lines.append(
        "\nConfusion matrix at threshold {}: TP={tp}, FN={fn}, FP={fp}, TN={tn} "
        "(positive = subscribed).\n".format(threshold, **cm)
    )
    lines.append(
        "Baseline reference: prior-probability model val PR-AUC {:.4f}, accuracy {:.4f}. "
        "The selected model far exceeds it.\n".format(
            perf["baseline_reference"]["validation"]["pr_auc_average_precision"],
            perf["baseline_reference"]["validation"]["accuracy_at_0.5"],
        )
    )

    lines.append("## Feature importance (global, permutation on validation)\n")
    lines.append("| Rank | Feature | Mean AP drop |")
    lines.append("| --- | --- | --- |")
    for i, r in enumerate(fi[:12], 1):
        lines.append(
            "| {} | `{}` | {:.5f} |".format(i, r["feature"], r["importance_mean"])
        )
    lines.append("")

    lines.append("## Calibration (validation)\n")
    lines.append("| Bin | Count | Mean predicted | Observed rate |")
    lines.append("| --- | --- | --- | --- |")
    for c in calib:
        lines.append(
            "| {} | {} | {:.3f} | {:.3f} |".format(
                c["bin"], c["count"], c["mean_predicted"], c["observed_rate"]
            )
        )
    lines.append("")
    lines.append("![performance](images/model_performance_charts.png)\n")

    lines.append("## Notes and limitations\n")
    for n in meta["notes_limitations"]:
        lines.append("- {}".format(n))
    lines.append("")
    with open(docs_path("model_report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    # Model card
    card = []
    card.append("# Model Card - {} v{}".format(model_name, VERSION))
    card.append("")
    card.append("| Field | Value |")
    card.append("| --- | --- |")
    card.append(
        "| Purpose | Predict probability a client subscribes a term deposit on contact |"
    )
    card.append("| Target | {} (binary: yes/no) |".format(target()))
    card.append("| Problem type | Binary classification |")
    card.append("| Selected model | {} |".format(model_name))
    card.append("| Version | {} |".format(VERSION))
    card.append(
        "| Decision threshold | {} (validation, cost-based) |".format(threshold)
    )
    card.append("| Test PR-AUC | {:.4f} |".format(t["pr_auc_average_precision"]))
    card.append("| Test ROC-AUC | {:.4f} |".format(t["roc_auc"]))
    card.append(
        "| Test recall / precision @ thr | {:.4f} / {:.4f} |".format(
            t["recall"], t["precision"]
        )
    )
    card.append("| Test accuracy | {:.4f} |".format(t["accuracy"]))
    card.append(
        "| Trainable features | {} (excludes {}) |".format(
            len(meta["feature_columns"]), ", ".join(meta["excluded_features"])
        )
    )
    card.append("")
    card.append("## Intended use / out-of-scope")
    card.append("- Use: rank and tier marketing contacts for the term-deposit offer.")
    card.append(
        "- Out of scope: any product other than term deposits; real-time pre-call scoring "
        "where the excluded fields' availability is uncertain."
    )
    card.append("")
    card.append("## Key drivers (top)")
    for r in fi[:8]:
        card.append(
            "- `{}` (importance {:.5f})".format(r["feature"], r["importance_mean"])
        )
    card.append("")
    card.append("## Limitations & risks")
    for n in meta["notes_limitations"]:
        card.append("- {}".format(n))
    card.append("")
    with open(docs_path("model_card.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(card) + "\n")


if __name__ == "__main__":
    main()
