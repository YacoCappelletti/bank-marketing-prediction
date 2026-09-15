# Predictive App - Documentation (Phase 6)

Streamlit app for scoring a single campaign contact through the prediction API.

## Run

```bash
make run-predict-app          # API_URL defaults to http://localhost:8000
# or
API_URL=http://api:8000 streamlit run apps/predict_app/app.py --server.port 8501
```

Requires the prediction API to be running (`make run-api`, or the `api` Docker service).

## What it does

1. Shows an **API status indicator** (sidebar) so the operator knows the backend is
   reachable before entering data.
2. Presents a three-column form with all 17 decision-time input fields (categorical
   fields as dropdowns, numeric fields bounded to the schema and dataset ranges).
   `pdays = 999` is the "never contacted" sentinel.
3. Offers **client-archetype presets** (cold lead, warm lead, high-propensity
   student/retiree) that pre-fill the form; every field stays editable. Enum lists
   and numeric bounds are derived from the API's Pydantic schemas (single source of
   truth).
4. `POST`s the observation to `{API_URL}/v1/predict`.
5. Displays:
   - **P(subscribe)** with a probability bar and the binary **decision** at the model
     threshold,
   - the **risk band** (color-coded pill) and the matching **business recommendation**
     (from `configs/business_rules.json`, aligned with the model's decision threshold),
   - the model name and **version**,
   - the **contributing factors** as a bar chart of SHAP contributions, aggregated by
     original dataset field, colored by sign (green = pushes probability up,
     red = pushes it down), with the detailed per-feature table underneath.

## Inputs not shown

`duration`, `poutcome`, and `campaign` are deliberately absent - the user-approved
feature policy excludes them (leakage / decision-time availability). The API also
rejects them.

## Behavior & edge cases

- **API unreachable:** a clear error tells the operator to start `make run-api`.
- **Validation error (422):** the API's error detail is shown.
- **Empty/failed prediction:** handled with an error message; no stack trace leaks.

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_URL` | `http://localhost:8000` | Base URL of the prediction API (`http://api:8000` in Docker). |
