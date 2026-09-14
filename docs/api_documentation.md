# Prediction API Documentation

FastAPI service exposing the approved term-deposit propensity model.

- **Base URL (local):** `http://localhost:8000`
- **Run:** `make run-api` (or `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`)
- **Interactive docs:** `/docs` (Swagger UI), `/redoc`

## Authentication

None in this reference implementation. In production, place behind an API gateway /
service token.

## Endpoints

### `GET /health`
Liveness + model-load status.

```json
{ "status": "ok", "model_loaded": true, "model_version": "1.0.0" }
```

Returns `status: "degraded"` and `model_loaded: false` if artifacts cannot be loaded.

### `POST /v1/predict`
Scores a single contact observation and returns the propensity, decision, contributing
factors, and a business recommendation.

**Request body** (all fields required; `emp.var.rate`, `cons.price.idx`, `cons.conf.idx`,
`nr.employed` use their dotted dataset names):

| Field | Type | Constraints |
| --- | --- | --- |
| age | int | 17-120 |
| job | enum | admin., blue-collar, technician, services, management, retired, entrepreneur, self-employed, housemaid, unemployed, student, unknown |
| marital | enum | married, single, divorced, unknown |
| education | enum | illiterate, basic.4y, basic.6y, basic.9y, high.school, professional.course, university.degree, unknown |
| default | enum | no, yes, unknown |
| housing | enum | no, yes, unknown |
| loan | enum | no, yes, unknown |
| contact | enum | cellular, telephone |
| month | enum | jan..dec |
| day_of_week | enum | mon..sun |
| pdays | int | 0-999 (999 = never contacted; recoded internally to a `previously_contacted` flag + `pdays_days`) |
| previous | int | >= 0 |
| emp.var.rate | float | quarterly employment rate change |
| cons.price.idx | float | consumer price index |
| cons.conf.idx | float | consumer confidence index |
| euribor3m | float | 3-month Euribor rate |
| nr.employed | float | number employed (social indicator) |

> Note: `duration`, `poutcome`, and `campaign` are intentionally **not** accepted. They
> were excluded by the user-approved feature policy (leakage / decision-time availability).

**Response `200`**

```json
{
  "prediction": 1,
  "predicted_class": "yes",
  "probability": 0.93052,
  "decision_threshold": 0.31,
  "risk_band": "high",
  "recommendation": "Priority outreach: assign best agents / cellular, personalized offer, contact within favorable macro window.",
  "contributing_factors": [
    {"feature": "num__euribor3m", "original_field": "euribor3m", "contribution": 0.42},
    {"feature": "num__nr.employed", "original_field": "nr.employed", "contribution": 0.31}
  ],
  "model_version": "1.0.0",
  "model_name": "GradientBoostingClassifier",
  "target": "y",
  "timestamp": "2026-09-13T19:39:04.392895Z"
}
```

Fields:
- `prediction` / `predicted_class`: the binary decision at `decision_threshold`.
- `probability`: P(subscribe).
- `decision_threshold`: cost-optimized cut from validation (G6); shown so callers can reason about the cut.
- `risk_band` / `recommendation`: from `configs/business_rules.json` bands keyed to `probability`.
- `contributing_factors`: top-5 SHAP features (positive = raises subscription likelihood), each mapped back to its original dataset field.

**Errors**
- `422` validation error: unknown category, out-of-range, missing field, or wrong type. Response is a Pydantic validation error listing each problem.
- `503`: model not available (artifacts failed to load).
- `500`: internal prediction error (details are not returned to the client).

### `GET /v1/model-card`
Returns the full `models/model_metadata.json` (versions, metrics, feature policy,
approval reference, threshold, limitations).

## Validation & error handling

Input validation is enforced by Pydantic v2 models (`src/api/schemas.py`). Categoricals
are `Literal` enums and numerics carry `ge`/`le` bounds, so malformed inputs are rejected
with `422` before any model call. Unexpected failures return generic messages; raw input
values are never echoed back.

## Logging

Structured access logging records method, path, status, and, for predictions, the numeric
probability, risk band, prediction, and model version. **Raw input values (including the
sensitive financial flags) are never logged.** Level is set via the `LOG_LEVEL` env var.

## Versioning

The model version is read from `models/model_metadata.json` at load time and surfaced in
`/health`, every `/v1/predict` response, and `/v1/model-card`.

## Worked examples

See [`json/api_examples.json`](json/api_examples.json) for a low-propensity request, a
high-propensity request, and validation-error cases with their exact responses.

## cURL

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/v1/predict -H 'Content-Type: application/json' -d '{
  "age":34,"job":"technician","marital":"single","education":"university.degree",
  "default":"no","housing":"yes","loan":"no","contact":"cellular","month":"may",
  "day_of_week":"thu","pdays":999,"previous":0,"emp.var.rate":1.1,"cons.price.idx":93.994,
  "cons.conf.idx":-36.4,"euribor3m":4.857,"nr.employed":5191.0}'
```
