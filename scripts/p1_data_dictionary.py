"""Phase 1 - Data Dictionary generator.

Profiles every column of the raw dataset and merges the computed statistics with
the curated semantic metadata in ``src/data/columns.py``. Emits both a JSON and a
Markdown data dictionary following the schema in PLAN Section 6.1.

Governance: G1 - the ``candidate_target_phase3`` value is a factual flag only.
No target is selected, ranked, or proposed here.
"""

import _bootstrap  # noqa: F401  (adds project root to sys.path)

import json

import numpy as np

from src.config import load_dataset, docs_json
from src.data.columns import COLUMN_META


def profile_column(df, col):
    s = df[col]
    n = len(df)
    missing = int(s.isna().sum())
    unique = int(s.nunique(dropna=True))

    dtype = str(s.dtype)
    is_numeric = pd_is_numeric(s)

    entry = {
        "name": col,
        "data_type": dtype,
        "missing_count": missing,
        "missing_pct": round(100.0 * missing / n, 3),
        "unique_count": unique,
    }

    # Value counts (for categorical/binary/low-cardinality numeric)
    if not is_numeric and unique <= 25:
        vc = s.value_counts(dropna=False)
        entry["possible_values"] = [str(k) for k in vc.index.tolist()]
        entry["value_distribution"] = {str(k): int(v) for k, v in vc.items()}
    # Example values
    ex = s.dropna().astype(str).unique()[:5]
    entry["example_values"] = list(ex)

    # Unknown-category sentinel (functions as effective missing)
    if not is_numeric:
        unknown_mask = s.astype(str).str.strip().str.lower() == "unknown"
        entry["unknown_category_count"] = int(unknown_mask.sum())
    else:
        entry["unknown_category_count"] = 0

    if is_numeric:
        q1 = float(np.nanpercentile(s.astype(float), 25))
        q3 = float(np.nanpercentile(s.astype(float), 75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = int(((s.astype(float) < lower) | (s.astype(float) > upper)).sum())
        entry["numeric_stats"] = {
            "min": float(np.nanmin(s)),
            "max": float(np.nanmax(s)),
            "mean": round(float(np.nanmean(s)), 4),
            "std": round(float(np.nanstd(s)), 4),
            "median": round(float(np.nanmedian(s)), 4),
            "q1": q1,
            "q3": q3,
            "iqr_outlier_count": outliers,
            "iqr_outlier_pct": round(100.0 * outliers / n, 3),
        }

    entry.update(COLUMN_META.get(col, {}))
    return entry


def pd_is_numeric(s):
    import pandas as pd

    return bool(pd.api.types.is_numeric_dtype(s))


def md_escape(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


def render_markdown(df, cols, c_map):
    lines = []
    lines.append("# Data Dictionary")
    lines.append("")
    lines.append(
        "Bank Marketing dataset (`data/raw/bank_data.csv`, semicolon-separated)."
    )
    lines.append("")
    lines.append("- **Rows:** {:,}  | **Columns:** {:d}".format(len(df), df.shape[1]))
    lines.append(
        "- **Source:** UCI Machine Learning Repository - Bank Marketing "
        "(bank-additional-full); Moro, Cortez & Silva (2014)."
    )
    lines.append(
        "- **Governance (G1):** the `Candidate target (Phase 3)` column below is a "
        "purely factual flag identifying outcome-style columns. No target variable is "
        "selected, ranked, or proposed in this phase."
    )
    lines.append("")

    # Summary table
    lines.append("## Column overview")
    lines.append("")
    lines.append(
        "| Column | Type | Role | Missing | Unique | Leak? | PII? | Temporal | Usable feat. | Cand. target (flag) |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for c in cols:
        e = c_map[c]
        leak = e.get("potential_data_leakage", "")
        pii = e.get("pii_sensitive", "")
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                md_escape(c),
                md_escape(e.get("data_type", "")),
                md_escape(e.get("semantic_type", "")),
                e.get("missing_count", 0),
                e.get("unique_count", ""),
                md_escape(leak),
                md_escape(pii),
                md_escape(e.get("temporal", "")),
                md_escape(e.get("usable_as_feature", "")),
                md_escape(e.get("candidate_target_phase3", "")),
            )
        )
    lines.append("")

    # Detailed per-column
    lines.append("## Column details")
    lines.append("")
    for c in cols:
        e = c_map[c]
        lines.append("### `{}`".format(c))
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("| --- | --- |")
        for key in [
            "description",
            "data_type",
            "semantic_type",
            "business_meaning",
            "missing_count",
            "missing_pct",
            "unique_count",
            "unknown_category_count",
            "example_values",
            "usable_as_feature",
            "candidate_target_phase3",
            "potential_data_leakage",
            "leakage_reason",
            "pii_sensitive",
            "pii_category",
            "temporal",
            "temporal_reason",
        ]:
            val = e.get(key, "")
            if isinstance(val, (list, tuple)):
                val = ", ".join(str(x) for x in val)
            lines.append("| {} | {} |".format(md_escape(key), md_escape(val)))
        if "numeric_stats" in e:
            ns = e["numeric_stats"]
            lines.append(
                "| numeric_stats | min={}, max={}, mean={}, median={}, std={}, "
                "IQR outliers={:,} ({}) |".format(
                    ns["min"],
                    ns["max"],
                    ns["mean"],
                    ns["median"],
                    ns["std"],
                    ns["iqr_outlier_count"],
                    str(ns["iqr_outlier_pct"]) + "%",
                )
            )
        if "value_distribution" in e:
            vd = e["value_distribution"]
            top = sorted(vd.items(), key=lambda kv: -kv[1])[:8]
            lines.append(
                "| value_distribution (top) | {} |".format(
                    md_escape(", ".join("{}={:,}".format(k, v) for k, v in top))
                )
            )
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    from src.config import docs_path

    df = load_dataset()
    cols = list(df.columns)

    profiles = [profile_column(df, c) for c in cols]
    c_map = {e["name"]: e for e in profiles}

    doc = {
        "dataset": "bank_data.csv",
        "source": "UCI ML Repository - Bank Marketing (bank-additional-full); Moro, Cortez & Silva (2014)",
        "rows": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "governance_note": "G1 respected: candidate_target_phase3 is a factual flag only; no ranking or selection.",
        "columns": profiles,
    }

    out_json = docs_json("data_dictionary.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
    print("Wrote", out_json)

    md = render_markdown(df, cols, c_map)
    out_md = docs_path("data_dictionary.md")
    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write(md + "\n")
    print("Wrote", out_md)
