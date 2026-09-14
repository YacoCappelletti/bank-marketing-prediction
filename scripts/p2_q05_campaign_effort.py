"""Phase 2 - Q05: How does contact intensity relate to conversion and effort?

Descriptive analysis of response rate by number of contacts in the current campaign
(`campaign`), plus campaign-effort efficiency.
"""

import _p2util as u
import pandas as pd
import matplotlib.pyplot as plt

QID = "p2_q05"
TITLE = "Campaign effort"
QUESTION = (
    "How does the number of contacts within the current campaign relate to conversion, and "
    "how much outbound effort is consumed by repeated contacting?"
)
RELEVANCE = (
    "Over-contacting burns agent capacity and may fatigue clients; knowing where marginal "
    "returns fall off lets the bank cap attempts and reallocate effort."
)


def main():
    df = u.data()
    df["_resp"] = (df["y"] == "yes").astype(int)
    overall = df["_resp"].mean()

    df["_attempts_bucket"] = pd.cut(
        df["campaign"], bins=[0, 1, 2, 3, 5, 100], labels=["1", "2", "3", "4-5", "6+"]
    )
    b = (
        df.groupby("_attempts_bucket", observed=True)["_resp"]
        .agg(["size", "sum", "mean"])
        .reset_index()
    )
    b.columns = ["attempts", "contacts", "subscribers", "response_rate"]

    # effort share: fraction of all contacts made to clients needing >1 attempt
    total_contacts = int(df["campaign"].sum())
    repeat_contacts = int(df.loc[df["campaign"] > 1, "campaign"].sum())
    repeat_share = repeat_contacts / total_contacts

    subscribers = int(df["_resp"].sum())
    contacts_per_subscriber = total_contacts / subscribers if subscribers else None

    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.bar(b["attempts"].astype(str), b["response_rate"] * 100, color="#6b46c1")
    ax.axhline(
        overall * 100, ls="--", c="grey", label="Overall {:.2f}%".format(overall * 100)
    )
    for i, r in enumerate(b.to_dict("records")):
        ax.text(
            i,
            r["response_rate"] * 100 + 0.3,
            "{:.1f}%".format(r["response_rate"] * 100),
            ha="center",
        )
    ax.set_xlabel("Contacts in current campaign")
    ax.set_ylabel("Response rate (%)")
    ax.set_title("Q05 - Response rate by contact attempts")
    ax.legend()

    metrics = {
        "question": QUESTION,
        "title": TITLE,
        "overall_response_rate": u.pct(overall),
        "response_by_attempts": [
            {
                "attempts": str(r["attempts"]),
                "contacts": int(r["contacts"]),
                "subscribers": int(r["subscribers"]),
                "response_rate_pct": u.pct(r["response_rate"]),
            }
            for _, r in b.iterrows()
        ],
        "total_contacts": total_contacts,
        "repeat_contact_share_of_all_contacts": u.pct(repeat_share),
        "subscribers_total": subscribers,
        "contacts_per_subscriber": round(contacts_per_subscriber, 2)
        if contacts_per_subscriber
        else None,
        "note": "Descriptive efficiency metrics; no model trained.",
    }
    chart = u.save_chart(fig, QID)
    js = u.save_metrics(QID, metrics)

    lines = [
        "# {} - {}".format(QID, TITLE),
        "",
        "**Question:** " + QUESTION,
        "",
        "**Method:** response rate by attempts bucket; effort share from campaign counts.",
        "",
    ]
    lines += u.md_table(
        ["Attempts", "Contacts", "Subscribers", "Response %"],
        [
            (
                str(r["attempts"]),
                "{:,}".format(int(r["contacts"])),
                "{:,}".format(int(r["subscribers"])),
                "{:.2f}".format(r["response_rate"] * 100),
            )
            for _, r in b.iterrows()
        ],
    )
    lines += [
        "",
        "{:.2f}% of all outbound contacts go to clients needing more than one attempt.".format(
            repeat_share * 100
        ),
        "It takes on average **{:.1f} contacts per subscriber**.".format(
            contacts_per_subscriber or 0
        ),
        "",
        "![chart](../images/{}.png)".format(chart.name),
    ]
    sn = u.save_snippet(QID, lines)
    print("OK", js, sn, chart)


if __name__ == "__main__":
    main()
