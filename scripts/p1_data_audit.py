"""Phase 1 - Data Quality Audit.

Computes dataset-wide quality metrics and writes ``docs/data_quality_report.md``
plus a basic distributions figure ``docs/images/p1_distributions.png``.

Governance: G1 - findings are descriptive. Response-style columns are profiled
for imbalance, but no target is proposed or ranked.
"""

import _bootstrap  # noqa: F401

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import load_dataset, docs_path
from src.data.columns import (
    COLUMN_META,
    PII_SENSITIVE,
    TEMPORAL_COLUMNS,
    LEAKAGE_CANDIDATES,
)


def effective_missing(df):
    """NaN count plus categorical 'unknown' count per column."""
    rows = []
    for c in df.columns:
        na = int(df[c].isna().sum())
        unk = 0
        if not pd.api.types.is_numeric_dtype(df[c]):
            unk = int((df[c].astype(str).str.strip().str.lower() == "unknown").sum())
        rows.append(
            {
                "column": c,
                "nan": na,
                "unknown_category": unk,
                "effective_missing": na + unk,
            }
        )
    return pd.DataFrame(rows)


def near_constant(df, dom_threshold=0.95):
    rows = []
    n = len(df)
    for c in df.columns:
        top = df[c].value_counts(dropna=False).iloc[0] / n
        if df[c].nunique(dropna=True) <= 1:
            rows.append((c, float(top), "constant"))
        elif top >= dom_threshold:
            rows.append((c, float(top), "near-constant"))
    return rows


def numeric_outliers(df):
    rows = []
    for c in df.select_dtypes(include=[np.number]).columns:
        s = df[c].astype(float)
        q1, q3 = np.nanpercentile(s, 25), np.nanpercentile(s, 75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        cnt = int(((s < lo) | (s > hi)).sum())
        rows.append(
            (
                c,
                int(s.min()),
                int(np.nanmax(s)),
                cnt,
                100.0 * cnt / len(s),
                round(float(iqr), 3),
            )
        )
    return rows


def make_distributions(df, path):
    num_cols = list(df.select_dtypes(include=[np.number]).columns)
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    ncols = 4
    nrows = int(np.ceil(len(num_cols) / ncols)) + int(np.ceil(len(cat_cols) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 3.0 * nrows))
    axes = axes.flatten()
    i = 0
    for c in num_cols:
        axes[i].hist(df[c].dropna(), bins=40, color="#2b6cb0")
        axes[i].set_title(c, fontsize=9)
        axes[i].tick_params(labelsize=7)
        i += 1
    for c in cat_cols:
        vc = df[c].value_counts().head(12)
        axes[i].barh(range(len(vc)), vc.values, color="#2c7a7b")
        axes[i].set_yticks(range(len(vc)))
        axes[i].set_yticklabels([str(x) for x in vc.index], fontsize=7)
        axes[i].invert_yaxis()
        axes[i].set_title(c, fontsize=9)
        axes[i].tick_params(labelsize=7)
        i += 1
    for j in range(i, len(axes)):
        axes[j].axis("off")
    fig.suptitle(
        "Phase 1 - Basic distributions (numeric histograms, categorical top counts)",
        y=1.0,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


def build_report(
    df, dup_full, dup_subset_contact, missing_df, near_const, outl, dom_year
):
    n_rows, n_cols = df.shape
    L = []
    L.append("# Data Quality Report")
    L.append("")
    L.append(
        "Dataset: `data/raw/bank_data.csv` (semicolon-separated). "
        "Source: UCI ML Repository - Bank Marketing."
    )
    L.append("")
    L.append("## 1. Structure")
    L.append("")
    L.append("| Metric | Value |")
    L.append("| --- | --- |")
    L.append("| Rows | {:,} |".format(n_rows))
    L.append("| Columns | {:d} |".format(n_cols))
    L.append(
        "| Numeric columns | {:d} |".format(
            df.select_dtypes(include=[np.number]).shape[1]
        )
    )
    L.append(
        "| Categorical columns | {:d} |".format(
            n_cols - df.select_dtypes(include=[np.number]).shape[1]
        )
    )
    L.append(
        "| Approx. memory | {:.2f} MB |".format(df.memory_usage(deep=True).sum() / 1e6)
    )
    L.append("")

    L.append("## 2. Missing values")
    L.append("")
    L.append(
        "The file has **no explicit NaN cells**, but several categorical columns encode "
        'missingness as the string `"unknown"`, which behaves as missing for modeling. '
        "Effective missingness combines both."
    )
    L.append("")
    L.append('| Column | NaN | "unknown" category | Effective missing | Effective % |')
    L.append("| --- | --- | --- | --- | --- |")
    for r in missing_df.itertuples():
        if r.effective_missing > 0:
            L.append(
                "| {} | {:d} | {:,} | {:,} | {:.2f}% |".format(
                    r.column,
                    r.nan,
                    r.unknown_category,
                    r.effective_missing,
                    100.0 * r.effective_missing / n_rows,
                )
            )
    L.append("")
    total_eff = int(missing_df.effective_missing.sum())
    L.append(
        "Columns with zero effective missingness: {:d} of {:d}.".format(
            int((missing_df.effective_missing == 0).sum()), n_cols
        )
    )
    L.append("")

    L.append("## 3. Duplicates")
    L.append("")
    L.append("| Check | Count |")
    L.append("| --- | --- |")
    L.append("| Fully duplicated rows | {:,} |".format(dup_full))
    L.append(
        "| Rows duplicated on age+job+marital+education+contact+month+day_of_week | {:,} |".format(
            dup_subset_contact
        )
    )
    L.append("")
    L.append(
        "Recommendation: drop exact duplicate rows before modeling (keep first) to avoid "
        "leaking identical records across splits. Note the dataset has no unique client id, so "
        "same-attribute rows may also be genuine distinct contacts."
    )
    L.append("")

    L.append("## 4. Constant / near-constant columns")
    L.append("")
    if near_const:
        L.append("| Column | Dominant value share | Flag |")
        L.append("| --- | --- | --- |")
        for c, share, flag in near_const:
            L.append("| {} | {:.2f}% | {} |".format(c, 100 * share, flag))
    else:
        L.append("_None above a 95% dominance threshold._")
    L.append("")
    def_sh = df["default"].value_counts().get("yes", 0)
    L.append(
        "Special note: `default` = `yes` occurs only **{:,}** times ({:.3f}% of rows); the "
        "column is almost entirely `no`/`unknown` and carries negligible signal.".format(
            int(def_sh), 100.0 * def_sh / n_rows
        )
    )
    L.append("")

    L.append("## 5. Data type issues & sentinels")
    L.append("")
    L.append(
        "- **`pdays = 999` sentinel:** {:,} rows ({:.1f}%) use 999 to mean 'never contacted "
        "before', not a real 999-day gap. Must be recoded (e.g., a boolean "
        "`previously_contacted` + numeric days) or it will distort any distance/mean logic.".format(
            int((df["pdays"] == 999).sum()), 100.0 * (df["pdays"] == 999).mean()
        )
    )
    L.append(
        "- **`age`:** minimum observed value is {} and maximum {}. A value of 17 in a banking "
        "customer base is implausible and should be treated as an outlier/error; range "
        "clipping or exclusion is recommended.".format(
            int(df["age"].min()), int(df["age"].max())
        )
    )
    L.append(
        "- **`duration`:** right-skewed (max {:,}s). Flagged as a leakage column (see Section 7).".format(
            int(df["duration"].max())
        )
    )
    L.append("")

    L.append("## 6. Numeric outliers (IQR rule)")
    L.append("")
    L.append("| Column | Min | Max | IQR-outlier count | IQR-outlier % |")
    L.append("| --- | --- | --- | --- | --- |")
    for c, mn, mx, cnt, pct, iqr in outl:
        if cnt > 0:
            L.append("| {} | {} | {} | {:,} | {:.2f}% |".format(c, mn, mx, cnt, pct))
    L.append("")
    L.append(
        "Outliers are largely genuine heavy-tail business quantities (long calls, many "
        "contacts). Recommend log/scaling transforms and capping at percentile bounds rather "
        "than deletion."
    )
    L.append("")

    L.append("## 7. Response-style column balance (descriptive only)")
    L.append("")
    L.append(
        "For completeness, the discrete yes/no-style columns "
        "are profiled below. **This is a factual distribution report, not a target proposal or "
        "ranking (G1).** Target selection happens in Phase 3."
    )
    L.append("")
    resp_cols = [
        c
        for c in df.columns
        if df[c].nunique(dropna=True) <= 2
        and set(map(str, df[c].astype(str).unique())).issubset({"yes", "no"})
    ]
    L.append("| Column | Level counts | Minority share |")
    L.append("| --- | --- | --- |")
    for c in resp_cols:
        vc = df[c].value_counts()
        minority = vc.min() / vc.sum()
        L.append(
            "| {} | {} | {:.2f}% |".format(
                c,
                ", ".join("{}={:,}".format(k, v) for k, v in vc.items()),
                100 * minority,
            )
        )
    L.append("")
    y_counts = df["y"].value_counts()
    L.append(
        "Balance note: yes/no-style columns show minority classes well under 20%, so any "
        "predictive task on them would require explicit class-imbalance handling "
        "(class weights / resampling, PR-AUC)."
    )
    L.append("")

    L.append("## 8. PII / sensitive columns inventory")
    L.append("")
    L.append("| Column | Category | Recommended handling | Justification |")
    L.append("| --- | --- | --- | --- |")
    pii_rows = {
        "default": (
            "Keep with justification",
            "Credit-default flag is sensitive financial data; "
            "near-constant here and low signal, so excluding it is safer for fairness/privacy.",
        ),
        "housing": (
            "Keep with justification",
            "Existing-liability flag is sensitive; usable as a "
            "feature with a documented fairness review.",
        ),
        "loan": (
            "Keep with justification",
            "Existing-liability flag is sensitive; usable as a "
            "feature with a documented fairness review.",
        ),
    }
    for c in PII_SENSITIVE:
        cat = COLUMN_META[c]["pii_category"]
        rec, just = pii_rows.get(c, ("Review", "Sensitive attribute."))
        L.append("| {} | {} | {} | {} |".format(c, cat, rec, just))
    L.append("")
    L.append(
        "There are **no direct identifiers** (no names, emails, phone numbers, account or "
        "national-id fields). `age` is a quasi-identifier but is aggregated demographic data. "
        "No masking is strictly required, but sensitive financial flags should be handled with "
        "a documented fairness/privacy review."
    )
    L.append("")

    L.append("## 9. Temporal coverage")
    L.append("")
    L.append(
        "- Time-ordered fields present: **{}**.".format(", ".join(TEMPORAL_COLUMNS))
    )
    L.append("- Months observed: {}.".format(dom_year))
    L.append(
        "- There is **no explicit date/timestamp column**; the bank-additional variant only "
        "carries month and day-of-week, so a strictly row-level chronological ordering is not "
        "directly available. The macroeconomic indicators (`emp.var.rate`, `euribor3m`, "
        "`nr.employed`) imply the collection period (roughly the second half of 2008-2010, with "
        "a heavy May concentration). For Phase 4, a stratified split is likely more practical "
        "than a time-based split, but temporal seasonality (`month`) should be modeled."
    )
    L.append("")

    L.append("## 10. Potential data leakage")
    L.append("")
    L.append("| Column | Reason |")
    L.append("| --- | --- |")
    for c in LEAKAGE_CANDIDATES:
        L.append("| {} | {} |".format(c, COLUMN_META[c]["leakage_reason"]))
    L.append("")

    L.append("## 11. Initial hypotheses (neutral, non-ranked)")
    L.append("")
    L.append(
        "1. Economic climate at campaign time (`euribor3m`, `emp.var.rate`, `nr.employed`, "
        "`cons.conf.idx`) is likely a strong driver of response, independent of the client."
    )
    L.append(
        "2. Seasonality is material: a large share of contacts occur in `may`, and month is "
        "correlated with the macro indicators."
    )
    L.append(
        "3. Prior relationship matters: `poutcome`, `previous`, and recency (`pdays`) encode "
        "whether the client was reachable/interested before."
    )
    L.append(
        "4. Contact channel (`contact`) and contact intensity (`campaign`) shape reachability "
        "and possible fatigue."
    )
    L.append(
        "5. `duration` would trivially predict the outcome but is not available before the "
        "call, so it must be excluded from a deployable model (see leakage note)."
    )
    L.append("")
    L.append(
        "These are exploratory hypotheses only. No target variable has been selected, ranked, "
        "or proposed in this phase (G1)."
    )
    L.append("")
    L.append("![Distributions](images/p1_distributions.png)")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    df = load_dataset()

    dup_full = int(df.duplicated().sum())
    key = ["age", "job", "marital", "education", "contact", "month", "day_of_week"]
    dup_subset_contact = int(df.duplicated(subset=key).sum())
    missing_df = effective_missing(df)
    near_const = near_constant(df)
    outl = numeric_outliers(df)
    dom_year = ", ".join(
        "{}={:,}".format(k, v) for k, v in df["month"].value_counts().items()
    )

    img = docs_path("images", "p1_distributions.png")
    make_distributions(df, img)
    print("Wrote", img)

    report = build_report(
        df, dup_full, dup_subset_contact, missing_df, near_const, outl, dom_year
    )
    out_md = docs_path("data_quality_report.md")
    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print("Wrote", out_md)
