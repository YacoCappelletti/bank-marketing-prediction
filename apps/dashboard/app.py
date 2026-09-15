"""Phase 7 - Business dashboard (Streamlit).

KPIs, interactive filters, and tabs for the five selected business questions,
answering: What happened? Why did it happen? What should the business do?
Reads the raw dataset and recomputes every metric live from the filtered rows.
"""

import os
from pathlib import Path

import altair as alt
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


def conversion_chart(df, col, title, sort_by_rate=True):
    g = rate_by(df, col)
    y_order = (
        list(g["segment"])
        if sort_by_rate
        else list(g.sort_values("segment")["segment"])
    )
    base = float(df["_resp"].mean())
    chart = (
        alt.Chart(g)
        .mark_bar(cornerRadius=2)
        .encode(
            x=alt.X(
                "response_rate:Q", title="Response rate", axis=alt.Axis(format="%")
            ),
            y=alt.Y("segment:N", sort=y_order, title=None),
            color=alt.Color(
                "response_rate:Q",
                scale=alt.Scale(scheme="tealblues"),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("segment:N", title="Segment"),
                alt.Tooltip("contacts:Q", title="Contacts", format=",.0f"),
                alt.Tooltip("subscribers:Q", title="Subscribers", format=",.0f"),
                alt.Tooltip("response_rate:Q", title="Response rate", format=".2%"),
            ],
        )
        .properties(title=title, height=320)
    )
    rule = (
        alt.Chart(pd.DataFrame({"x": [base]}))
        .mark_rule(color="#c05621", strokeDash=[4, 4])
        .encode(x=alt.X("x:Q", title=""))
    )
    st.altair_chart((chart + rule).resolve_scale(x="shared"), use_container_width=True)
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


def kpis(f):
    contacts = len(f)
    subs = int(f["_resp"].sum())
    conv = 100.0 * subs / contacts
    warm_share = 100.0 * f["_previously_contacted"].mean()
    total_attempts = int(f["campaign"].sum())
    per_sub = total_attempts / subs if subs else float("inf")
    return contacts, subs, conv, warm_share, per_sub


def main():
    st.set_page_config(
        page_title="Bank Marketing Dashboard", page_icon="🏦", layout="wide"
    )
    st.title("🏦 Bank Marketing Campaign Dashboard")
    st.caption(
        "Direct-marketing performance of a Portuguese bank (2008-2010). "
        "Every chart recomputes live from the filters - answering: what happened, "
        "why, and what to do next."
    )

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

    contacts, subs, conv, warm_share, per_sub = kpis(f)
    dataset_conv = 100.0 * df["_resp"].mean()

    conv_delta = conv - dataset_conv
    per_sub_full = df["campaign"].sum() / df["_resp"].sum()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Contacts", f"{contacts:,}")
    c2.metric("Subscribers", f"{subs:,}")
    c3.metric(
        "Conversion",
        f"{conv:.2f}%",
        delta=f"{conv_delta:+.2f} pp vs full dataset"
        if abs(conv_delta) > 1e-9
        else None,
    )
    c4.metric("Warm share", f"{warm_share:.1f}%")
    c5.metric(
        "Contacts / subscriber",
        f"{per_sub:.1f}",
        delta=f"{per_sub - per_sub_full:+.1f}"
        if abs(per_sub - per_sub_full) > 1e-9
        else None,
        delta_color="inverse",
    )

    dl1, dl2 = st.columns([3, 1])
    dl2.download_button(
        "⬇️ Download filtered data (CSV)",
        f.to_csv(index=False).encode("utf-8"),
        file_name="filtered_campaign_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

    tab_overview, tab_seg, tab_macro, tab_effort, tab_actions = st.tabs(
        ["📌 Overview", "👥 Segments", "💹 Macro", "☎️ Effort", "✅ Actions"]
    )

    with tab_overview:
        conversion_chart(f, "contact", "Q01 - Conversion by contact channel")
        st.info(
            "**Why:** cellular reaches engaged clients who answer; telephone converts far lower. "
            "**Action:** shift outbound capacity to cellular where both channels can reach the client.",
            icon="💡",
        )
        conversion_chart(
            f, "_previously_contacted", "Q04 - Conversion by prior-contact status"
        )
        st.info(
            "**Why:** warm leads convert several times higher than cold ones. "
            "**Action:** work warm/previously-contacted leads first.",
            icon="🔥",
        )

    with tab_seg:
        conversion_chart(f, "job", "Q03 - Conversion by job segment")
        conversion_chart(f, "_age_band", "Q03 - Conversion by age band")
        st.info(
            "**Why:** students, retirees, and the 65+/under-25 bands are far above base rate. "
            "**Action:** curate calling lists toward high-propensity segments.",
            icon="👥",
        )

    with tab_macro:
        conversion_chart(f, "_euribor_band", "Q02 - Conversion by interest-rate band")
        st.info(
            "**Why:** deposits are more attractive in low-rate windows; high-rate periods suppress demand. "
            "**Action:** size and time campaign waves to favorable macro windows.",
            icon="💹",
        )

    with tab_effort:
        conversion_chart(
            f, "campaign", "Q05 - Conversion by number of contacts", sort_by_rate=False
        )
        st.info(
            "**Why:** marginal conversion falls with each extra attempt while effort accumulates. "
            "**Action:** cap attempts on low-propensity clients and reallocate capacity.",
            icon="☎️",
        )
        st.warning(
            "Note: `poutcome` is a strong descriptive signal but is excluded from the "
            "production model after the leakage review; charts here are descriptive only.",
            icon="⚠️",
        )

    with tab_actions:
        st.subheader("What should the business do?")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("#### 📌 What happened")
            st.markdown(
                f"- {contacts:,} contacts → {subs:,} subscribers ({conv:.2f}%).\n"
                f"- Conversion varies widely by channel, segment, macro window, and history."
            )
        with col_b:
            st.markdown("#### 🔍 Why it happened")
            st.markdown(
                "- Cellular vs telephone reachability gap (Q01).\n"
                "- Macro windows: rate level drives deposit appeal (Q02).\n"
                "- Segment mix: students/retirees/warm leads over-index (Q03, Q04).\n"
                "- Effort waste: repeated dials convert little (Q05)."
            )
        with col_c:
            st.markdown("#### 🎯 What to do")
            st.markdown(
                "- **When:** concentrate intensive waves in low-rate / weak-employment windows.\n"
                "- **Who:** contact warm and high-propensity segments first.\n"
                "- **How:** prefer cellular; cap repeat attempts on low-propensity clients.\n"
                "- **Next:** score and rank the cold majority with the predictive app / API."
            )


if __name__ == "__main__":
    main()
