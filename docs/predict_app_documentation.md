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

1. Presents a sidebar form with all 17 decision-time input fields (categorical
   fields as dropdowns, numeric fields as sliders/number inputs with the dataset's
   valid ranges). `pdays = 999` is the "never contacted" sentinel.
2. Validates the inputs client-side before calling the API.
3. `POST`s the observation to `{API_URL}/v1/predict`.
4. Displays:
   - **P(subscribe)** and the binary **decision** (yes/no) at the model threshold,
   - the model **version**,
   - a color-coded **risk band** and the matching **business recommendation**
     (from `configs/business_rules.json`),
   - the **top-5 contributing factors** as a bar chart of SHAP contributions, with
     each factor mapped back to its original dataset field.

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
