"""Phase 2 - Q01: Which contact channel is associated with better conversion?

Descriptive analysis of response rate by contact channel (cellular vs telephone).
"""

import _p2util as u
import matplotlib.pyplot as plt

QID = "p2_q01"
TITLE = "Contact-channel conversion"
QUESTION = "Which contact channel (cellular vs telephone) is associated with a higher term-deposit response rate?"
RELEVANCE = (
    "Channel is the most direct lever the bank controls per contact; shifting outbound "
    "capacity toward the higher-converting channel raises conversion without new spend."
)


def main():
    df = u.data()
    df["_resp"] = (df["y"] == "yes").astype(int)

    grp = df.groupby("contact")["_resp"].agg(["size", "sum", "mean"]).reset_index()
    grp.columns = ["channel", "contacts", "subscribers", "response_rate"]
    rows = grp.to_dict("records")
    overall = float(df["_resp"].mean())

    by = {r["channel"]: float(r["response_rate"]) for r in rows}
    lift = (by["cellular"] / by["telephone"]) if by.get("telephone") else None

    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.bar(
        [r["channel"] for r in rows],
        [r["response_rate"] * 100 for r in rows],
        color=["#2b6cb0", "#dd6b20"],
    )
    ax.axhline(
        overall * 100, ls="--", c="grey", label="Overall {:.2f}%".format(overall * 100)
    )
    for i, r in enumerate(rows):
        ax.text(
            i,
            r["response_rate"] * 100 + 0.3,
            "{:.2f}%".format(r["response_rate"] * 100),
            ha="center",
        )
    ax.set_ylabel("Response rate (%)")
    ax.set_title("Q01 - Response rate by contact channel")
    ax.legend()

    metrics = {
        "question": QUESTION,
        "title": TITLE,
        "overall_response_rate": u.pct(overall),
        "by_channel": [
            {
                "channel": r["channel"],
                "contacts": int(r["contacts"]),
                "subscribers": int(r["subscribers"]),
                "response_rate_pct": u.pct(r["response_rate"]),
            }
            for r in rows
        ],
        "cellular_over_telephone_lift": round(float(lift), 3) if lift else None,
        "note": "Descriptive association only; no model trained.",
    }
    chart = u.save_chart(fig, QID)
    js = u.save_metrics(QID, metrics)

    lines = [
        "# {} - {}".format(QID, TITLE),
        "",
        "**Question:** " + QUESTION,
        "",
        "**Method:** response-rate aggregation by channel (no predictive model).",
        "",
    ]
    lines += u.md_table(
        ["Channel", "Contacts", "Subscribers", "Response %"],
        [
            [
                r["channel"],
                "{:,}".format(int(r["contacts"])),
                "{:,}".format(int(r["subscribers"])),
                "{:.2f}".format(r["response_rate"] * 100),
            ]
            for r in rows
        ],
    )
    lines += [
        "",
        "Overall response rate: **{:.2f}%**. Cellular contacts convert about "
        "**{:.1f}x** the telephone rate.".format(overall * 100, lift or 0),
        "",
        "![chart](../images/{}.png)".format(chart.name),
    ]
    sn = u.save_snippet(QID, lines)

    print("OK", js, sn, chart)


if __name__ == "__main__":
    main()
