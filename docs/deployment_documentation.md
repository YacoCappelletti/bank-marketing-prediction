# Deployment Documentation

The project ships as **one Docker image** that runs all three processes; the services
differ only by their command.

## Prerequisites

- Docker Engine + Docker Compose plugin (v2 syntax).

## Build

```bash
make docker-build          # docker build -t bank-marketing-prediction:latest .
```

The `Dockerfile` uses `python:3.13-slim`, installs `requirements.txt`, copies code,
configs, models, and the raw dataset, and runs as a non-root user.

## Run the full stack

```bash
make docker-up             # docker compose up --build
```

| Service | URL | Command |
| --- | --- | --- |
| `api` | http://localhost:8000 | `uvicorn src.api.main:app --host 0.0.0.0 --port 8000` |
| `predict-app` | http://localhost:8501 | `streamlit run apps/predict_app/app.py --server.port 8501` |
| `dashboard` | http://localhost:8502 | `streamlit run apps/dashboard/app.py --server.port 8502` |

- The `api` service exposes a **healthcheck** on `/health`.
- `predict-app` waits for `api` to be healthy (`depends_on: condition: service_healthy`)
  and reaches it via `API_URL=http://api:8000` on the internal Compose network.
- Model artifacts (`models/*.joblib`, `model_metadata.json`) are baked into the image,
  so the API loads them at startup with no external mount required.

Stop the stack:

```bash
make docker-down
```

## Verify a running deployment

```bash
curl -s localhost:8000/health
curl -s localhost:8000/v1/model-card | head -c 200
curl -s -X POST localhost:8000/v1/predict -H 'Content-Type: application/json' \
  -d '{"age":34,"job":"technician","marital":"single","education":"university.degree","default":"no","housing":"yes","loan":"no","contact":"cellular","month":"may","day_of_week":"thu","pdays":999,"previous":0,"emp.var.rate":1.1,"cons.price.idx":93.994,"cons.conf.idx":-36.4,"euribor3m":4.857,"nr.employed":5191.0}'
```

The two Streamlit apps should return HTTP 200 on `:8501` and `:8502`.

## Environment variables

| Variable | Default | Used by | Notes |
| --- | --- | --- | --- |
| `API_HOST` | `0.0.0.0` | api | Bind host (uvicorn). |
| `API_PORT` | `8000` | api | Bind port. |
| `API_URL` | `http://localhost:8000` | predict-app | `http://api:8000` inside Compose. |
| `LOG_LEVEL` | `INFO` | api | Python logging level. |
| `MODEL_PATH` / `PREPROCESSOR_PATH` / `EXPLAINER_PATH` | `/models/...` | reference | The service resolves artifacts relative to the project root; these are documented for external mounts. |
| `DATA_PATH` | `data/raw/bank_data.csv` | dashboard | Dataset location. |

Copy `.env.example` to `.env` to override defaults (never commit secrets).

## Notes & limitations

- Reference deployment (no TLS / auth); front the API with a gateway in production.
- The image is data+model self-contained for reproducibility; mount volumes if you
  want to update the dataset without rebuilding.
