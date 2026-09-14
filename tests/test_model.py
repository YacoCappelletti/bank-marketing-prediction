"""Phase 4 tests: model artifacts load, predictions are well-formed, and the
documented test-set minimums are met."""

import json

import joblib
import numpy as np
import pandas as pd
import pytest

from src.config import load_dataset, models_path, docs_json
from src.data.prepare import split_frames, target
from src.model import explain, selection

# Documented minimums (model_report.md / model_card.md). Note: accuracy is
# intentionally NOT a target here - the 20:1 cost matrix drives a recall-leaning
# threshold, so the business objective is minimized expected cost, not accuracy.
MIN_TEST_PR_AUC = 0.30
MIN_TEST_ROC_AUC = 0.70
MIN_TEST_RECALL = 0.50


@pytest.fixture(scope="module")
def bundle():
    pipeline = joblib.load(models_path("final_model.joblib"))
    pre = joblib.load(models_path("preprocessor.joblib"))
    spec = joblib.load(models_path("explainer.joblib"))
    return pipeline, pre, spec


@pytest.fixture(scope="module")
def data():
    return split_frames(load_dataset())


def test_artifacts_load(bundle):
    pipeline, pre, spec = bundle
    assert hasattr(pipeline, "predict_proba")
    assert hasattr(pre, "transform")
    assert isinstance(spec, dict) and spec["kind"] in {"tree", "linear", "permutation"}


def test_pipeline_has_named_steps(bundle):
    pipeline, _, _ = bundle
    assert "pre" in dict(pipeline.named_steps)
    assert "est" in dict(pipeline.named_steps)


def test_prediction_shape_and_range(bundle, data):
    pipeline, _, _ = bundle
    Xtr, Xval, Xtest, ytr, yval, ytest, cols = data
    proba = pipeline.predict_proba(Xtest)
    assert proba.shape == (len(Xtest), 2)
    assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-6)
    assert proba.min() >= 0.0 and proba.max() <= 1.0


def test_metadata_records_governance():
    meta = json.load(open(models_path("model_metadata.json"), encoding="utf-8"))
    assert meta["approved_target"] == target() == "y"
    assert meta["problem_type"] == "binary_classification"
    assert meta["target_approval_reference"]["approval_status"] == "approved"
    assert 0.0 < meta["chosen_decision_threshold"] < 1.0
    assert meta["split_sizes"]["train"] > 0
    assert "duration" not in meta["feature_columns"]
    for k in ["scikit_learn", "pandas", "numpy", "python"]:
        assert k in meta["library_versions"]


def test_test_metrics_meet_minimums():
    perf = json.load(open(docs_json("model_performance.json"), encoding="utf-8"))
    t = perf["test"]
    assert t["pr_auc_average_precision"] >= MIN_TEST_PR_AUC
    assert t["roc_auc"] >= MIN_TEST_ROC_AUC
    assert t["recall"] >= MIN_TEST_RECALL
    # Business objective: minimized expected cost must beat both naive policies.
    cm = t["confusion_matrix"]
    fn_cost = perf["cost_matrix"]["false_negative_cost"]
    fp_cost = perf["cost_matrix"]["false_positive_cost"]
    n = cm["tp"] + cm["fn"] + cm["fp"] + cm["tn"]
    actual_pos = cm["tp"] + cm["fn"]
    actual_neg = cm["tn"] + cm["fp"]
    all_no_cost = actual_pos * fn_cost / n  # never contact anyone
    all_yes_cost = actual_neg * fp_cost / n  # contact everyone
    assert t["expected_cost_per_client"] < all_no_cost
    assert t["expected_cost_per_client"] < all_yes_cost
    # beats baseline PR-AUC comfortably
    baseline = perf["baseline_reference"]["validation"]["pr_auc_average_precision"]
    assert t["pr_auc_average_precision"] > baseline + 0.1


def test_threshold_and_cost_consistency():
    meta = json.load(open(models_path("model_metadata.json"), encoding="utf-8"))
    cm = meta["test_metrics"]["confusion_matrix"]
    assert cm["tp"] + cm["fn"] + cm["fp"] + cm["tn"] == meta["split_sizes"]["test"]


def test_explainer_returns_top_contributions(bundle, data):
    pipeline, pre, spec = bundle
    Xtr, Xval, Xtest, ytr, yval, ytest, cols = data
    Xt = pre.transform(Xval.iloc[:3])
    for i in range(3):
        top = explain.top_contributions(spec, pipeline.named_steps["est"], Xt[[i]], k=5)
        assert top is not None
        assert 0 < len(top) <= 5
        assert {"feature", "contribution"} <= set(top[0].keys())


def test_test_evaluated_once_flag():
    perf = json.load(open(docs_json("model_performance.json"), encoding="utf-8"))
    assert (
        "exactly once" in perf["note"].lower()
        or "exactly once" in perf.get("note", "").lower()
    )
