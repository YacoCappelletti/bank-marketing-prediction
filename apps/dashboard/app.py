"""Phase 7 - Business dashboard (Streamlit).

KPIs, interactive filters, and charts for the five selected business questions,
answering: What happened? Why did it happen? What should the business do?
Reads the raw dataset and recomputes every metric live from the filtered rows.
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = os.getenv("DATA_PATH", str(ROOT / "data" / "raw" / "bank_data.csv"))

EURIBOR_BINS = [0, 1.5, 2.5, 3.5, 4.5, 5.1]
EURIBOR_LABELS = ["<1.5", "1.5-2.5", "2.5-3.5", "3.5-4.5", "4.5-5.1"]
AGE_BINS = [0, 25, 35, 45, 55, 65, 200]
AGE_LABELS = ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, sep=";")
    df["_resp"] = (df["y"] == "yes").astype(int)
    df["_previously_contacted"] = df["pdays"] != 999
    df["_euribor_band"] = pd.cut(
        df["euribor3m"], bins=EURIBOR_BINS, labels=EURIBOR_LABELS, include_lowest=True
    )
    df["_age_band"] = pd.cut(
        df["age"], bins=AGE_BINS, labels=AGE_LABELS, include_lowest=True
    )
    return df


def rate_by(df, col):
    g = (
        df.groupby(col, observed=True)["_resp"]
        .agg(["size", "sum", "mean"])
        .reset_index()
    )
    g.columns = ["segment", "contacts", "subscribers", "response_rate"]
    g["segment"] = g["segment"].astype(str)
    return g.sort_values("response_rate", ascending=False)


def chart(df, col, title):
    st.subheader(title)
    g = rate_by(df, col)
    st.bar_chart(g.set_index("segment")["response_rate"] * 100)
    st.dataframe(
        g.assign(
            **{
                "response_rate_%": (g["response_rate"] * 100).round(2),
                "contacts": g["contacts"].astype(int),
                "subscribers": g["subscribers"].astype(int),
            }
        )[["segment", "contacts", "subscribers", "response_rate_%"]],
        use_container_width=True,
        hide_index=True,
    )


def main():
    st.set_page_config(
        page_title="Bank Marketing Dashboard", page_icon="🏦", layout="wide"
    )
    st.title("🏦 Bank Marketing Campaign Dashboard")

    try:
        df = load_data()
    except Exception as exc:
        st.error(f"Could not load dataset at {DATA_PATH}: {exc}")
        return

    st.sidebar.header("Filters")
    channels = st.sidebar.multiselect(
        "Contact channel",
        sorted(df["contact"].unique()),
        default=sorted(df["contact"].unique()),
    )
    months = st.sidebar.multiselect(
        "Month", sorted(df["month"].unique()), default=sorted(df["month"].unique())
    )
    bands = st.sidebar.multiselect(
        "Euribor band", EURIBOR_LABELS, default=EURIBOR_LABELS
    )
    warm = st.sidebar.checkbox("Warm leads only (previously contacted)", value=False)

    f = df[
        df["contact"].isin(channels)
        & df["month"].isin(months)
        & df["_euribor_band"].astype(str).isin(bands)
    ]
    if warm:
        f = f[f["_previously_contacted"]]

    if len(f) == 0:
        st.warning("No rows match the current filters.")
        return

    contacts = len(f)
    subs = int(f["_resp"].sum())
    conv = 100.0 * subs / contacts
    warm_share = 100.0 * f["_previously_contacted"].mean()
    total_attempts = int(f["campaign"].sum())
    per_sub = total_attempts / subs if subs else float("inf")

    st.subheader("KPIs")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Contacts", f"{contacts:,}")
    c2.metric("Subscribers", f"{subs:,}")
    c3.metric("Conversion", f"{conv:.2f}%")
    c4.metric("Warm share", f"{warm_share:.1f}%")
    c5.metric("Contacts / subscriber", f"{per_sub:.1f}")

    st.divider()
    st.caption(
        f"Segment view reflects current filters ({contacts:,} contacts, {conv:.2f}% conversion)."
    )

    chart(f, "contact", "Q01 - Conversion by contact channel")
    st.info(
        "Why: cellular reaches engaged clients who answer; telephone converts far lower. "
        "Action: shift outbound capacity to cellular where both channels can reach the client."
    )

    chart(f, "_euribor_band", "Q02 - Conversion by interest-rate band")
    st.info(
        "Why: deposits are more attractive in low-rate windows; high-rate periods suppress demand. "
        "Action: size and time campaign waves to favorable macro windows."
    )

    chart(f, "job", "Q03 - Conversion by job segment")
    chart(f, "_age_band", "Q03 - Conversion by age band")
    st.info(
        "Why: students, retirees, and the 65+/under-25 bands are far above base rate. "
        "Action: curate calling lists toward high-propensity segments."
    )

    chart(f, "_previously_contacted", "Q04 - Conversion by prior-contact status")
    chart(f, "poutcome", "Q04 - Conversion by previous-campaign outcome")
    st.warning(
        "Note: poutcome/previously-contacted are strong but subject to the leakage review "
        "from Phase 1-3; the production model excludes poutcome."
    )
    st.info(
        "Why: warm leads convert several times higher than cold ones. "
        "Action: work warm/previously-contacted leads first."
    )

    chart(f, "campaign", "Q05 - Conversion by number of contacts")
    st.info(
        "Why: marginal conversion falls with each extra attempt while effort accumulates. "
        "Action: cap attempts on low-propensity clients and reallocate capacity."
    )

    st.divider()
    st.subheader("What should the business do?")
    st.markdown(
        "- **When:** concentrate intensive waves in low-rate / weak-employment windows.\n"
        "- **Who:** contact warm (previously-contacted) and high-propensity segments first.\n"
        "- **How:** prefer cellular; cap repeat attempts on low-propensity clients.\n"
        "- **Next:** use the predictive app / API to score and rank the cold majority."
    )


if __name__ == "__main__":
    main()
