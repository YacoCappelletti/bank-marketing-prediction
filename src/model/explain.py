"""Global (permutation) importance and a persisted local SHAP explainer.

Global importance is computed on the VALIDATION split (not test) to respect G6.
The local explainer spec is a small, picklable dict (kind + a background sample
and/or linear coefficients). The estimator is passed in at explain() time so it
is not duplicated inside explainer.joblib.
"""

import numpy as np
import shap
from sklearn.inspection import permutation_importance

from src.config import load_model_config


def global_permutation_importance(pipeline, X_val, y_val, seed, n_repeats=10):
    res = permutation_importance(
        pipeline,
        X_val,
        y_val,
        scoring="average_precision",
        n_repeats=n_repeats,
        random_state=seed,
        n_jobs=-1,
    )
    names = list(pipeline.named_steps["pre"].get_feature_names_out())
    order = np.argsort(-res.importances_mean)
    out = []
    for i in order:
        out.append(
            {
                "feature": names[i],
                "importance_mean": round(float(res.importances_mean[i]), 5),
                "importance_std": round(float(res.importances_std[i]), 5),
            }
        )
    return out


def _tree_explainer_kind(model_name):
    return model_name in (
        "RandomForestClassifier",
        "DecisionTreeClassifier",
        "GradientBoostingClassifier",
    )


def build_explainer(pipeline, X_train, model_name, seed, sample_rows=200):
    """Return a small picklable explainer spec bound to transformed training data."""
    from src.config import get_seed  # noqa

    pre = pipeline.named_steps["pre"]
    est = pipeline.named_steps["est"]
    Xt = pre.transform(X_train)
    Xarr = Xt.toarray() if hasattr(Xt, "toarray") else np.asarray(Xt)
    feature_names = list(pre.get_feature_names_out())

    rng = np.random.RandomState(seed)
    idx = rng.choice(Xarr.shape[0], size=min(sample_rows, Xarr.shape[0]), replace=False)
    background = Xarr[idx]

    spec = {"model_name": model_name, "feature_names": feature_names}
    if _tree_explainer_kind(model_name):
        spec["kind"] = "tree"
        spec["background"] = background
    elif model_name == "LogisticRegression":
        spec["kind"] = "linear"
        spec["coef"] = np.asarray(est.coef_).ravel()
        spec["mean"] = background.mean(axis=0)
    else:
        spec["kind"] = "permutation"
        spec["background"] = background
    return spec


def explain(spec, estimator, Xt, explainer=None):
    """Contribution matrix (positive class) for transformed rows Xt."""
    kind = spec["kind"]
    Xarr = Xt.toarray() if hasattr(Xt, "toarray") else np.asarray(Xt)

    if kind == "tree":
        # tree_path_dependent mode: exact for tree ensembles, no masker/subsampling warning
        expl = explainer or shap.TreeExplainer(estimator)
        vals = expl.shap_values(Xarr)
        if isinstance(vals, (list, tuple)):
            vals = vals[-1]
        vals = np.asarray(vals)
        if vals.ndim == 3:
            vals = vals[:, :, 1]
        return vals
    if kind == "linear":
        return (Xarr - spec["mean"]) * spec["coef"]
    return None


def top_contributions(spec, estimator, Xt_row, k=None, explainer=None):
    """Return top-k (feature, contribution) for a single transformed row."""
    if k is None:
        k = int(load_model_config()["feature_importance"]["top_k"])
    contrib = explain(spec, estimator, Xt_row, explainer=explainer)
    if contrib is None:
        return None
    row = np.asarray(contrib).reshape(-1)
    order = np.argsort(-np.abs(row))[:k]
    names = spec["feature_names"]
    return [
        {"feature": names[i], "contribution": round(float(row[i]), 5)} for i in order
    ]
