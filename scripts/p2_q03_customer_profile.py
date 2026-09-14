"""Phase 2 - Q03: Which customer segments respond best?

Descriptive response-rate comparison across demographic segments (age band, job,
marital status, education).
"""

import _p2util as u
import pandas as pd
import matplotlib.pyplot as plt

QID = "p2_q03"
TITLE = "Customer profile segments"
QUESTION = (
    "Which customer demographic segments (age band, job, marital status, education) "
    "are associated with the highest term-deposit response rate?"
)
RELEVANCE = (
    "Segment-level propensity lets the bank focus calling lists on warmer audiences, "
    "improving conversion per agent-hour."
)


def main():
    df = u.data()
    df["_resp"] = (df["y"] == "yes").astype(int)
    overall = df["_resp"].mean()

    bins = [0, 25, 35, 45, 55, 65, 200]
    labels = ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]
    df["_age_band"] = pd.cut(df["age"], bins=bins, labels=labels, include_lowest=True)

    age = rate_by(df, "_age_band")
    job = rate_by(df, "job").sort_values("response_rate", ascending=False)
    mar = rate_by(df, "marital")
    edu = rate_by(df, "education")

    top_job = job.iloc[0]
    top_age = age[age["response_rate"] > overall]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    axes[0].bar(age["segment"].astype(str), age["response_rate"] * 100, color="#2b6cb0")
    axes[0].axhline(overall * 100, ls="--", c="grey")
    axes[0].set_title("Q03 - Response by age band")
    axes[0].set_ylabel("Response rate (%)")
    jobtop = job.head(8)
    axes[1].barh(
        jobtop["segment"].astype(str), jobtop["response_rate"] * 100, color="#38a169"
    )
    axes[1].axvline(overall * 100, ls="--", c="grey")
    axes[1].invert_yaxis()
    axes[1].set_title("Q03 - Response by job (top 8)")
    axes[1].set_xlabel("Response rate (%)")

    metrics = {
        "question": QUESTION,
        "title": TITLE,
        "overall_response_rate": u.pct(overall),
        "response_by_age_band": to_records(age),
        "response_by_job": to_records(job),
        "response_by_marital": to_records(mar),
        "response_by_education": to_records(edu),
        "best_job": {
            "segment": str(top_job["segment"]),
            "response_rate_pct": u.pct(top_job["response_rate"]),
        },
        "age_bands_above_average": [str(s) for s in top_age["segment"]],
        "note": "Descriptive segment rates; no model trained.",
    }
    chart = u.save_chart(fig, QID)
    js = u.save_metrics(QID, metrics)

    lines = [
        "# {} - {}".format(QID, TITLE),
        "",
        "**Question:** " + QUESTION,
        "",
        "**Method:** response-rate aggregation per segment.",
        "",
        "## Response by age band",
        "",
    ]
    lines += u.md_table(
        ["Age band", "Contacts", "Subscribers", "Response %"], records_table(age)
    )
    lines += ["", "## Response by job", ""]
    lines += u.md_table(
        ["Job", "Contacts", "Subscribers", "Response %"], records_table(job)
    )
    lines += ["", "## Response by marital / education", ""]
    lines += u.md_table(
        ["Marital", "Response %"],
        [[r["segment"], r["response_rate_pct"]] for r in to_records(mar)],
    )
    lines += [""] + u.md_table(
        ["Education", "Response %"],
        [[r["segment"], r["response_rate_pct"]] for r in to_records(edu)],
    )
    lines += [
        "",
        "Best job segment: **{}** at **{:.2f}%**.".format(
            top_job["segment"], top_job["response_rate"] * 100
        ),
        "",
        "![chart](../images/{}.png)".format(chart.name),
    ]
    sn = u.save_snippet(QID, lines)
    print("OK", js, sn, chart)


def rate_by(df, col):
    g = (
        df.groupby(col, observed=True)["_resp"]
        .agg(["size", "sum", "mean"])
        .reset_index()
    )
    g.columns = ["segment", "contacts", "subscribers", "response_rate"]
    return g


def to_records(g):
    recs = []
    for _, r in g.iterrows():
        recs.append(
            {
                "segment": str(r["segment"]),
                "contacts": int(r["contacts"]),
                "subscribers": int(r["subscribers"]),
                "response_rate_pct": u.pct(r["response_rate"]),
            }
        )
    return recs


def records_table(g):
    return [
        (
            rec["segment"],
            "{:,}".format(rec["contacts"]),
            "{:,}".format(rec["subscribers"]),
            "{:.2f}".format(rec["response_rate_pct"]),
        )
        for rec in to_records(g)
    ]


if __name__ == "__main__":
    main()
