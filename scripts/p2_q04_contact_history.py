"""Phase 2 - Q04: How does prior contact history relate to response?

Descriptive response-rate analysis of prior-engagement signals (previous-campaign
outcome, recency `pdays`, number of prior contacts `previous`).
"""

import _p2util as u
import matplotlib.pyplot as plt

QID = "p2_q04"
TITLE = "Prior-contact history"
QUESTION = (
    "How does prior contact history (previous outcome, contact recency, number of prior "
    "contacts) relate to the current term-deposit response rate?"
)
RELEVANCE = (
    "Warm leads with prior positive contact history convert far better; identifying them "
    "lets the bank focus re-contact budgets and avoid cold-only dialing."
)


def main():
    df = u.data()
    df["_resp"] = (df["y"] == "yes").astype(int)
    df["_previously_contacted"] = df["pdays"] != 999
    overall = df["_resp"].mean()

    pout = rate_by(df, "poutcome").sort_values("response_rate", ascending=False)
    recency = rate_by(df, "_previously_contacted")
    prev = rate_by(df, "previous").sort_values("segment")

    success = pout[pout["segment"] == "success"]
    success_rate = float(success["response_rate"].iloc[0]) if len(success) else None

    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.bar(
        pout["segment"].astype(str),
        pout["response_rate"] * 100,
        color=["#a0aec0", "#dd6b20", "#2c7a7b"],
    )
    ax.axhline(
        overall * 100, ls="--", c="grey", label="Overall {:.2f}%".format(overall * 100)
    )
    for i, r in enumerate(pout.to_dict("records")):
        ax.text(
            i,
            r["response_rate"] * 100 + 0.5,
            "{:.1f}%".format(r["response_rate"] * 100),
            ha="center",
        )
    ax.set_ylabel("Response rate (%)")
    ax.set_title("Q04 - Response by previous-campaign outcome")
    ax.legend()

    metrics = {
        "question": QUESTION,
        "title": TITLE,
        "overall_response_rate": u.pct(overall),
        "response_by_poutcome": to_records(pout),
        "response_by_previously_contacted": to_records(recency),
        "response_by_previous_count": to_records(prev),
        "success_share_of_rows": u.pct((df["poutcome"] == "success").mean()),
        "note": "Descriptive; `poutcome=success` is leakage-flagged for any modeling use (Phase 3/4 review).",
    }
    chart = u.save_chart(fig, QID)
    js = u.save_metrics(QID, metrics)

    lines = [
        "# {} - {}".format(QID, TITLE),
        "",
        "**Question:** " + QUESTION,
        "",
        "**Method:** response-rate aggregation by prior-history fields.",
        "",
        "## Response by previous outcome",
        "",
    ]
    lines += u.md_table(
        ["poutcome", "Contacts", "Subscribers", "Response %"], records_table(pout)
    )
    lines += ["", "## Response by previously contacted (pdays != 999)", ""]
    lines += u.md_table(
        ["Previously contacted", "Contacts", "Subscribers", "Response %"],
        records_table(recency),
    )
    lines += [
        "",
        "Clients with `poutcome=success` convert at **{}%**.".format(
            round(success_rate * 100, 2) if success_rate is not None else "n/a"
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
    return [
        {
            "segment": str(r["segment"]),
            "contacts": int(r["contacts"]),
            "subscribers": int(r["subscribers"]),
            "response_rate_pct": u.pct(r["response_rate"]),
        }
        for _, r in g.iterrows()
    ]


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
