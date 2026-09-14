"""Phase 2 - Q02: How do macroeconomic conditions relate to campaign demand?

Descriptive analysis of response rate across interest-rate and labor-market bands.
"""

import _p2util as u
import numpy as np
import matplotlib.pyplot as plt

QID = "p2_q02"
TITLE = "Economic conditions and demand"
QUESTION = (
    "How do macroeconomic conditions (euribor3m, employment rate) relate to the "
    "term-deposit response rate?"
)
RELEVANCE = (
    "Demand for deposits moves with the rate environment; timing and sizing campaign "
    "waves to favorable windows materially changes booked deposits per call."
)


def main():
    df = u.data()
    df["_resp"] = (df["y"] == "yes").astype(int)
    overall = df["_resp"].mean()

    # euribor bands
    bins = [0, 1.5, 2.5, 3.5, 4.5, 5.1]
    labels = ["0-1.5", "1.5-2.5", "2.5-3.5", "3.5-4.5", "4.5-5.1"]
    df["_euribor_band"] = pd_cut(df["euribor3m"], bins, labels)
    eur = (
        df.groupby("_euribor_band", observed=True)["_resp"]
        .agg(["size", "sum", "mean"])
        .reset_index()
    )
    eur.columns = ["euribor3m_band", "contacts", "subscribers", "response_rate"]

    corr_eur = association(df["euribor3m"], df["_resp"])
    corr_emp = association(df["emp.var.rate"], df["_resp"])
    corr_empn = association(df["nr.employed"], df["_resp"])
    corr_conf = association(df["cons.conf.idx"], df["_resp"])

    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.bar(
        eur["euribor3m_band"].astype(str), eur["response_rate"] * 100, color="#2c7a7b"
    )
    ax.axhline(
        overall * 100, ls="--", c="grey", label="Overall {:.2f}%".format(overall * 100)
    )
    for i, r in enumerate(eur.itertuples()):
        ax.text(
            i,
            r.response_rate * 100 + 0.3,
            "{:.1f}%".format(r.response_rate * 100),
            ha="center",
        )
    ax.set_xlabel("euribor3m band (%)")
    ax.set_ylabel("Response rate (%)")
    ax.set_title("Q02 - Response rate by interest-rate band")
    ax.legend()

    metrics = {
        "question": QUESTION,
        "title": TITLE,
        "overall_response_rate": u.pct(overall),
        "response_by_euribor_band": [
            {
                "band": str(r.euribor3m_band),
                "contacts": int(r.contacts),
                "subscribers": int(r.subscribers),
                "response_rate_pct": u.pct(r.response_rate),
            }
            for r in eur.itertuples()
        ],
        "point_biserial_correlation_with_response": {
            "euribor3m": round(corr_eur, 3),
            "emp.var.rate": round(corr_emp, 3),
            "nr.employed": round(corr_empn, 3),
            "cons.conf.idx": round(corr_conf, 3),
        },
        "note": "Descriptive association only; correlation is a summary statistic, not a model.",
    }
    chart = u.save_chart(fig, QID)
    js = u.save_metrics(QID, metrics)

    lines = [
        "# {} - {}".format(QID, TITLE),
        "",
        "**Question:** " + QUESTION,
        "",
        "**Method:** response rate by banded macro indicator; point-biserial correlation "
        "(descriptive association).",
        "",
    ]
    lines += u.md_table(
        ["euribor3m band", "Contacts", "Subscribers", "Response %"],
        [
            [
                str(r.euribor3m_band),
                "{:,}".format(r.contacts),
                "{:,}".format(r.subscribers),
                "{:.2f}".format(r.response_rate * 100),
            ]
            for r in eur.itertuples()
        ],
    )
    lines += [
        "",
        "Correlation with response - euribor3m {:.2f}, emp.var.rate {:.2f}, "
        "nr.employed {:.2f}, cons.conf.idx {:.2f}.".format(
            corr_eur, corr_emp, corr_empn, corr_conf
        ),
        "",
        "![chart](../images/{}.png)".format(chart.name),
    ]
    sn = u.save_snippet(QID, lines)
    print("OK", js, sn, chart)


def pd_cut(series, bins, labels):
    import pandas as pd

    return pd.cut(series, bins=bins, labels=labels, include_lowest=True)


def association(x, y_bin):
    import pandas as pd

    x = pd.Series(x).astype(float)
    y = pd.Series(y_bin).astype(float)
    m = x.notna() & y.notna()
    x, y = x[m], y[m]
    return float(np.corrcoef(x, y)[0, 1])


if __name__ == "__main__":
    main()
