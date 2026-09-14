"""FastAPI prediction API.

Endpoints: /health, /v1/predict, /v1/model-card.
Structured logging never emits raw input values (no PII). Model versioning is read
from models/model_metadata.json via the Predictor.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.api.schemas import ClientFeatures, PredictionResponse, HealthResponse
from src.api.predict import get_predictor, Predictor

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("bank_api")


@asynccontextmanager
async def lifespan(app):
    try:
        p = get_predictor()
        logger.info("model loaded version=%s", p.version)
    except Exception as exc:  # pragma: no cover
        logger.error("model failed to load: %s", exc)
    yield


app = FastAPI(
    title="Bank Marketing Prediction API",
    version="1.0.0",
    description="Term-deposit subscription propensity API for the Bank Marketing model.",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    # structured, PII-free access log
    logger.info(
        "request method=%s path=%s status=%s",
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


@app.get("/health", response_model=HealthResponse)
def health():
    try:
        p = get_predictor()
        return HealthResponse(status="ok", model_loaded=True, model_version=p.version)
    except Exception as exc:
        logger.error("health check failed: %s", exc)
        return HealthResponse(status="degraded", model_loaded=False, model_version=None)


@app.post("/v1/predict", response_model=PredictionResponse)
def predict(features: ClientFeatures):
    payload = features.model_dump(by_alias=True)
    try:
        p = get_predictor()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Model not available")
    try:
        result = p.predict(payload)
    except Exception as exc:
        # never log raw input values; log only the exception class
        logger.error("prediction error type=%s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Prediction failed")
    logger.info(
        "predict ok proba=%.3f band=%s pred=%s version=%s",
        result["probability"],
        result["risk_band"],
        result["prediction"],
        result["model_version"],
    )
    return result


@app.get("/v1/model-card")
def model_card():
    try:
        return get_predictor().model_card()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Model not available")


@app.exception_handler(ValueError)
async def _value_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
