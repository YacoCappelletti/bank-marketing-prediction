"""Phase 6 - Predictive app (Streamlit).

A form for one campaign contact observation; scores it through the prediction API at
API_URL and shows the probability, main contributing factors (SHAP, color by sign),
risk band, and a business recommendation. Enum lists and numeric bounds are derived
from the API schemas so there is a single source of truth.
"""

import os
import sys
from pathlib import Path
from typing import get_args

import altair as alt
import pandas as pd
import requests
import streamlit as st

# Allow `streamlit run apps/predict_app/app.py` from any CWD (Docker runs it as a
# console script, which unlike `python -m` does not add the project root).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.api.schemas import (
    ClientFeatures,
    CONTACT,
    DOW,
    EDUCATION,
    JOB,
    MARITAL,
    MONTH,
    YN,
)

API_URL = os.getenv("API_URL", "http://localhost:8000")
PREDICT_ENDPOINT = f"{API_URL}/v1/predict"

JOBS = list(get_args(JOB))
MARITALS = list(get_args(MARITAL))
EDUCATIONS = list(get_args(EDUCATION))
YNS = list(get_args(YN))
CONTACTS = list(get_args(CONTACT))
MONTHS = list(get_args(MONTH))
# The dataset only covers working days, so weekend options are not offered.
DOWS = ["mon", "tue", "wed", "thu", "fri"]


def _bound(field_name, kind):
    for meta in ClientFeatures.model_fields[field_name].metadata:
        v = getattr(meta, kind, None)
        if v is not None:
            return v
    return None


AGE_MIN, AGE_MAX = _bound("age", "ge"), _bound("age", "le")
PDAYS_SENTINEL = 999

# Dataset-observed ranges for the macroeconomic sliders.
MACRO = {
    "emp.var.rate": (-3.4, 1.4, 1.1, 0.1, "Employment variation rate"),
    "cons.price.idx": (92.2, 94.8, 93.994, 0.001, "Consumer price index"),
    "cons.conf.idx": (-50.8, -26.9, -36.4, 0.1, "Consumer confidence index"),
    "euribor3m": (0.634, 5.045, 4.857, 0.001, "Euribor 3-month rate"),
    "nr.employed": (4963.6, 5228.1, 5191.0, 0.1, "Number of employed"),
}

BAND_COLORS = {"high": "red", "medium": "orange", "low": "green"}

# Client archetypes: defaults used to pre-fill the form. Macro context is the
# last observed wave in the dataset (high-rate window, May 2010-like).
PRESETS = {
    "Cold lead - typical client": {
        "age": 38,
        "job": "technician",
        "marital": "married",
        "education": "university.degree",
        "default": "no",
        "housing": "yes",
        "loan": "no",
        "contact": "cellular",
        "month": "may",
        "day_of_week": "thu",
        "pdays": PDAYS_SENTINEL,
        "previous": 0,
    },
    "Warm lead - previously contacted": {
        "age": 31,
        "job": "admin.",
        "marital": "single",
        "education": "high.school",
        "default": "no",
        "housing": "yes",
        "loan": "no",
        "contact": "cellular",
        "month": "mar",
        "day_of_week": "tue",
        "pdays": 6,
        "previous": 1,
    },
    "High propensity - student": {
        "age": 22,
        "job": "student",
        "marital": "single",
        "education": "high.school",
        "default": "no",
        "housing": "no",
        "loan": "no",
        "contact": "cellular",
        "month": "oct",
        "day_of_week": "thu",
        "pdays": 999,
        "previous": 0,
    },
    "High propensity - retired": {
        "age": 68,
        "job": "retired",
        "marital": "married",
        "education": "basic.4y",
        "default": "no",
        "housing": "no",
        "loan": "no",
        "contact": "cellular",
        "month": "mar",
        "day_of_week": "wed",
        "pdays": 999,
        "previous": 0,
    },
}


def apply_preset():
    name = st.session_state.get("preset")
    if not name or name == "Custom":
        return
    for k, v in PRESETS[name].items():
        st.session_state[k] = v
    for k in MACRO:  # keep the macro context at its default wave
        st.session_state[f"macro_{k}"] = MACRO[k][2]


# Pre-fill the form with the "typical client" defaults on first load.
for _k, _v in PRESETS["Cold lead - typical client"].items():
    st.session_state.setdefault(_k, _v)
for _k in MACRO:
    st.session_state.setdefault(f"macro_{_k}", MACRO[_k][2])


def macro_value(key):
    lo, hi, default, step, _ = MACRO[key]
    lo_s, hi_s = float(lo), float(hi)
    default_s = min(max(float(default), lo_s), hi_s)
    key = f"macro_{key}"
    if key not in st.session_state:
        st.session_state[key] = default_s
    return st.session_state[key]


def build_form():
    c1, c2, c3 = st.columns(3)
    with c1:
        st.selectbox(
            "Client archetype (preset)",
            ["Custom", *PRESETS],
            key="preset",
            on_change=apply_preset,
            help="Pre-fills the form with a typical observation; then tweak any field.",
        )
        age = st.number_input(
            f"Age ({AGE_MIN}-{AGE_MAX})",
            AGE_MIN,
            AGE_MAX,
            key="age",
            help="Training data is clipped to this range.",
        )
        job = st.selectbox("Job", JOBS, key="job")
        marital = st.selectbox("Marital status", MARITALS, key="marital")
        education = st.selectbox("Education", EDUCATIONS, key="education")
    with c2:
        default = st.selectbox("Credit in default", YNS, key="default")
        housing = st.selectbox("Housing loan", YNS, key="housing")
        loan = st.selectbox("Personal loan", YNS, key="loan")
        contact = st.selectbox("Contact channel", CONTACTS, key="contact")
        month = st.selectbox("Contact month", MONTHS, key="month")
        dow = st.selectbox("Day of week", DOWS, key="day_of_week")
    with c3:
        pdays = st.number_input(
            "Days since prior contact (pdays)",
            0,
            PDAYS_SENTINEL,
            key="pdays",
            help=f"{PDAYS_SENTINEL} = never contacted before this campaign.",
        )
        previous = st.number_input("Prior contacts (previous)", 0, 27, key="previous")
        st.caption("Macroeconomic context at contact time (dataset range).")
        emp = st.slider(
            MACRO["emp.var.rate"][4],
            *MACRO["emp.var.rate"][:4],
            key="macro_emp.var.rate",
        )
        cpi = st.slider(
            MACRO["cons.price.idx"][4],
            *MACRO["cons.price.idx"][:4],
            key="macro_cons.price.idx",
        )
        cci = st.slider(
            MACRO["cons.conf.idx"][4],
            *MACRO["cons.conf.idx"][:4],
            key="macro_cons.conf.idx",
        )
        eur = st.slider(
            MACRO["euribor3m"][4], *MACRO["euribor3m"][:4], key="macro_euribor3m"
        )
        nre = st.slider(
            MACRO["nr.employed"][4], *MACRO["nr.employed"][:4], key="macro_nr.employed"
        )

    return {
        "age": int(age),
        "job": job,
        "marital": marital,
        "education": education,
        "default": default,
        "housing": housing,
        "loan": loan,
        "contact": contact,
        "month": month,
        "day_of_week": dow,
        "pdays": int(pdays),
        "previous": int(previous),
        "emp.var.rate": float(emp),
        "cons.price.idx": float(cpi),
        "cons.conf.idx": float(cci),
        "euribor3m": float(eur),
        "nr.employed": float(nre),
    }


def shap_chart(factors: pd.DataFrame) -> alt.Chart:
    # One-hot columns belong to the same original field; aggregate for readability.
    df = (
        factors.groupby("original_field", as_index=False)["contribution"]
        .sum()
        .assign(abs_c=lambda d: d["contribution"].abs())
        .sort_values("abs_c", ascending=False)
        .head(8)
        .sort_values("abs_c")
    )
    return (
        alt.Chart(df)
        .mark_bar(cornerRadius=2)
        .encode(
            x=alt.X(
                "contribution:Q",
                title="SHAP contribution (pushes probability up / down)",
            ),
            y=alt.Y("original_field:N", sort="-x", title=None),
            color=alt.condition(
                "datum.contribution > 0",
                alt.value("#38a169"),
                alt.value("#e53e3e"),
            ),
            tooltip=[
                alt.Tooltip("original_field:N", title="Field"),
                alt.Tooltip("contribution:Q", title="Contribution", format=".4f"),
            ],
        )
        .properties(height=300)
    )


def api_health():
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.status_code == 200 and r.json().get("model_loaded"):
            return r.json()
    except requests.RequestException:
        pass
    return None


def main():
    st.set_page_config(
        page_title="Subscription Predictor", page_icon="📈", layout="wide"
    )
    st.title("📈 Term-Deposit Subscription Predictor")
    st.caption(
        "Score one campaign contact **before** the call: predicted subscription "
        "probability, the factors behind it, and the recommended action."
    )

    health = api_health()
    sidebar = st.sidebar
    sidebar.header("Model status")
    if health:
        sidebar.success(f"API online - model v{health['model_version']}")
    else:
        sidebar.error(f"API unreachable at {API_URL}. Start it with `make run-api`.")

    payload = build_form()

    if not st.button("🔮 Predict", type="primary", use_container_width=True):
        st.info("Set the client attributes on the left, then press **Predict**.")
        return

    with st.spinner("Scoring..."):
        try:
            resp = requests.post(PREDICT_ENDPOINT, json=payload, timeout=30)
        except requests.RequestException:
            st.error(
                f"Cannot reach the prediction API at {API_URL}. Start it with `make run-api`."
            )
            return

    if resp.status_code == 422:
        st.error("The API rejected the input (422). Details:")
        st.json(resp.json())
        return
    if resp.status_code != 200:
        st.error(f"API error {resp.status_code}: {resp.text}")
        return

    r = resp.json()
    band = r["risk_band"]
    prob = r["probability"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("P(subscribe)", f"{prob:.1%}")
    m2.metric("Decision", r["predicted_class"].upper())
    m3.metric("Risk band", band.upper())
    m4.metric("Model", f"v{r['model_version']}")
    st.progress(
        min(max(prob, 0.0), 1.0),
        text=f"Probability {prob:.3f} (threshold {r['decision_threshold']})",
    )

    st.markdown(
        f"**Risk band:** :{BAND_COLORS.get(band, 'gray')}-background[{band.upper()}]"
    )
    st.info(f"Recommended action: {r['recommendation']}", icon="🎯")

    st.subheader("Main contributing factors")
    st.caption(
        "SHAP contributions for this prediction (positive = increases subscription likelihood)."
    )
    factors = pd.DataFrame(r["contributing_factors"])
    if not factors.empty:
        st.altair_chart(shap_chart(factors), use_container_width=True)
        st.dataframe(
            factors[["original_field", "feature", "contribution"]],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        f"Model: {r['model_name']} | target: {r['target']} | generated: {r['timestamp']}"
    )


if __name__ == "__main__":
    main()
