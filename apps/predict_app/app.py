"""Phase 6 - Predictive app (Streamlit).

A form for one contact observation; scores it through the prediction API at
API_URL and shows the probability, main contributing factors, risk band, and a
business recommendation. Validates inputs before calling the API.
"""

import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
PREDICT_ENDPOINT = f"{API_URL}/v1/predict"

JOBS = [
    "admin.",
    "blue-collar",
    "technician",
    "services",
    "management",
    "retired",
    "entrepreneur",
    "self-employed",
    "housemaid",
    "unemployed",
    "student",
    "unknown",
]
MARITAL = ["married", "single", "divorced", "unknown"]
EDUCATION = [
    "illiterate",
    "basic.4y",
    "basic.6y",
    "basic.9y",
    "high.school",
    "professional.course",
    "university.degree",
    "unknown",
]
YN = ["no", "yes", "unknown"]
CONTACT = ["cellular", "telephone"]
MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]
DOW = ["mon", "tue", "wed", "thu", "fri"]

BAND_COLORS = {"high": "red", "medium": "orange", "low": "green"}


def build_request():
    st.sidebar.header("Model inputs")
    age = st.sidebar.number_input("Age", 17, 120, 38)
    job = st.sidebar.selectbox("Job", JOBS, index=JOBS.index("technician"))
    marital = st.sidebar.selectbox("Marital status", MARITAL, index=0)
    education = st.sidebar.selectbox("Education", EDUCATION, index=6)
    default = st.sidebar.selectbox("Credit in default", YN, index=0)
    housing = st.sidebar.selectbox("Housing loan", YN, index=1)
    loan = st.sidebar.selectbox("Personal loan", YN, index=0)
    contact = st.sidebar.selectbox("Contact channel", CONTACT, index=0)
    month = st.sidebar.selectbox("Contact month", MONTHS, index=4)
    dow = st.sidebar.selectbox("Day of week", DOW, index=3)
    st.sidebar.caption("pdays = 999 means 'never contacted before'.")
    pdays = st.sidebar.number_input("Days since prior contact (pdays)", 0, 999, 999)
    previous = st.sidebar.number_input("Prior contacts (previous)", 0, 10, 0)
    emp = st.sidebar.slider("emp.var.rate", -3.4, 1.4, 1.1, step=0.1)
    cpi = st.sidebar.slider("cons.price.idx", 92.0, 94.8, 93.994, step=0.001)
    cci = st.sidebar.slider("cons.conf.idx", -50.8, -26.9, -36.4, step=0.1)
    eur = st.sidebar.slider("euribor3m", 0.6, 5.1, 4.857, step=0.001)
    nre = st.sidebar.slider("nr.employed", 4960.0, 5230.0, 5191.0, step=0.1)

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


def prevalidate(payload):
    errors = []
    if not (17 <= payload["age"] <= 120):
        errors.append("age must be between 17 and 120.")
    if payload["month"] not in MONTHS:
        errors.append("Invalid month.")
    return errors


def main():
    st.set_page_config(
        page_title="Subscription Predictor", page_icon="📈", layout="wide"
    )
    st.title("📈 Term-Deposit Subscription Predictor")
    st.caption(
        "Enter a campaign contact to score its subscription probability. "
        "Powered by the prediction API."
    )

    payload = build_request()

    errors = prevalidate(payload)
    if errors:
        for e in errors:
            st.warning(e)
        return

    if not st.sidebar.button("Predict"):
        st.info("Fill the inputs and press **Predict**.")
        return

    try:
        resp = requests.post(PREDICT_ENDPOINT, json=payload, timeout=15)
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

    c1, c2, c3 = st.columns(3)
    c1.metric("P(subscribe)", f"{r['probability']:.3f}")
    c2.metric("Decision", r["predicted_class"].upper())
    c3.metric("Model", f"v{r['model_version']}")

    st.markdown(
        f"**Risk band:** :{BAND_COLORS.get(band, 'gray')}-background[{band.upper()}]  |  "
        f"decision threshold = {r['decision_threshold']}"
    )
    st.info(f"Recommended action: {r['recommendation']}")

    st.subheader("Main contributing factors")
    st.caption("SHAP contributions (positive increases subscription likelihood).")
    df = pd.DataFrame(r["contributing_factors"])
    if not df.empty:
        df["abs"] = df["contribution"].abs()
        df = df.sort_values("abs", ascending=False).drop(columns="abs")
        st.bar_chart(df.set_index("original_field")["contribution"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(
        f"Model: {r['model_name']} | target: {r['target']} | generated: {r['timestamp']}"
    )


if __name__ == "__main__":
    main()
