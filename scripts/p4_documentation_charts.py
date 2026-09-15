"""Phase 4 - Documentation charts: threshold-cost curve and candidate comparison.

Both charts use the VALIDATION split only (G6: the test set is never used for
tuning or visualization of selection curves). Deterministic: fixed seed split.
"""

import _bootstrap  # noqa: F401

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.config import (
    get_seed,
    load_business_rules,
    load_dataset,
    docs_json,
    docs_images,
    models_path,
)
from src.data.prepare import split_frames
from src.model import selection


def main():
    rules = load_business_rules()
    fn_cost = rules["cost_matrix"]["false_negative_cost"]
    fp_cost = rules["cost_matrix"]["false_positive_cost"]
    ctx = json.load(open(models_path("selection_context.json"), encoding="utf-8"))
    chosen_thr = ctx["selected_validation"]["val_optimal_threshold"]

    # ---- Chart 1: expected cost vs decision threshold (validation) ----
    _, Xval, _, _, yval, _, _ = split_frames(load_dataset())
    import joblib

    pipeline = joblib.load(models_path("final_model.joblib"))
    proba_val = pipeline.predict_proba(Xval)[:, 1]
    _, curve = selection.optimize_threshold(yval, proba_val, fn_cost, fp_cost)

    thrs = [c["threshold"] for c in curve]
    costs = [c["expected_cost"] for c in curve]
    best_i = int(np.argmin(costs))

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.plot(thrs, costs, color="#2b6cb0", lw=2, label="Expected cost per client")
    ax.axvline(
        chosen_thr,
        color="#c05621",
        ls="--",
        lw=1.5,
        label=f"Chosen threshold = {chosen_thr:.2f}",
    )
    ax.scatter(
        [thrs[best_i]],
        [costs[best_i]],
        color="#c05621",
        zorder=5,
        s=45,
        label=f"Minimum = {min(costs):.4f}",
    )
    naive_pos = (
        fp_cost  # contact nobody => cost = FN * p(1) = fp_cost * base? computed below
    )
    base_rate = float(np.mean(yval))
    ax.axhline(
        base_rate * fn_cost,
        color="grey",
        ls=":",
        lw=1.2,
        label=f"Never contact (cost {base_rate * fn_cost:.2f})",
    )
    ax.axhline(
        (1 - base_rate) * fp_cost,
        color="grey",
        ls="-.",
        lw=1.2,
        label=f"Contact everyone (cost {(1 - base_rate) * fp_cost:.2f})",
    )
    ax.set_xlabel("Decision threshold (validation)")
    ax.set_ylabel("Expected cost per client")
    ax.set_title("Decision threshold selection - validation set only (G6)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(docs_images("threshold_cost_curve.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)

    # ---- Chart 2: baseline vs candidates (validation PR-AUC) ----
    baseline = json.load(open(docs_json("baseline_metrics.json"), encoding="utf-8"))
    rows = [("Baseline\n(prior)", baseline["validation"]["pr_auc_average_precision"])]
    rows += [
        (r["model"].replace("Classifier", ""), r["val_pr_auc"]) for r in ctx["results"]
    ]
    rows.sort(key=lambda r: r[1])
    names = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    colors = ["#a0aec0"] + ["#2b6cb0"] * (len(rows) - 1)
    colors[vals.index(max(vals))] = "#276749"

    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    bars = ax.barh(names, vals, color=colors)
    for b, v in zip(bars, vals):
        ax.text(
            v + 0.006,
            b.get_y() + b.get_height() / 2,
            f"{v:.4f}",
            va="center",
            fontsize=9,
        )
    ax.set_xlabel("Validation PR-AUC (average precision)")
    ax.set_title(f"Candidate comparison - selected {ctx['selected_model']}")
    ax.set_xlim(0, max(vals) * 1.15)
    fig.tight_layout()
    fig.savefig(docs_images("model_vs_baseline.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)

    print(
        "Wrote docs/images/threshold_cost_curve.png and docs/images/model_vs_baseline.png"
    )


if __name__ == "__main__":
    main()
