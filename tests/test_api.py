"""Phase 5 tests: API health, valid prediction schema, invalid-input 422s."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


VALID_INPUT = {
    "age": 34,
    "job": "technician",
    "marital": "single",
    "education": "university.degree",
    "default": "no",
    "housing": "yes",
    "loan": "no",
    "contact": "cellular",
    "month": "may",
    "day_of_week": "thu",
    "pdays": 999,
    "previous": 0,
    "emp.var.rate": 1.1,
    "cons.price.idx": 93.994,
    "cons.conf.idx": -36.4,
    "euribor3m": 4.857,
    "nr.employed": 5191.0,
}

RESPONSE_KEYS = {
    "prediction",
    "predicted_class",
    "probability",
    "decision_threshold",
    "risk_band",
    "recommendation",
    "contributing_factors",
    "model_version",
    "model_name",
    "target",
    "timestamp",
}


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"]


def test_predict_valid(client):
    r = client.post("/v1/predict", json=VALID_INPUT)
    assert r.status_code == 200
    body = r.json()
    assert RESPONSE_KEYS <= set(body.keys())
    assert 0.0 <= body["probability"] <= 1.0
    assert body["prediction"] in (0, 1)
    assert body["predicted_class"] in ("yes", "no")
    assert isinstance(body["contributing_factors"], list)
    assert 0 < len(body["contributing_factors"]) <= 5
    assert body["risk_band"] in ("low", "medium", "high")
    assert isinstance(body["recommendation"], str) and body["recommendation"]


def test_predict_prediction_matches_threshold(client):
    r = client.post("/v1/predict", json=VALID_INPUT).json()
    expected = int(r["probability"] >= r["decision_threshold"])
    assert r["prediction"] == expected


def test_predict_band_consistent_with_prediction(client):
    r = client.post("/v1/predict", json=VALID_INPUT).json()
    assert (r["risk_band"] != "low") == (r["prediction"] == 1)
    assert (r["recommendation"].startswith("Deprioritize")) == (r["prediction"] == 0)


def test_predict_invalid_enum_422(client):
    bad = dict(VALID_INPUT, job="astronaut")
    assert client.post("/v1/predict", json=bad).status_code == 422


def test_predict_out_of_range_422(client):
    bad = dict(VALID_INPUT, age=250)
    assert client.post("/v1/predict", json=bad).status_code == 422


def test_predict_age_below_training_range_422(client):
    """Age is rejected below 18, matching the clipped training range."""
    bad = dict(VALID_INPUT, age=17)
    assert client.post("/v1/predict", json=bad).status_code == 422


def test_predict_missing_field_422(client):
    bad = {k: v for k, v in VALID_INPUT.items() if k != "age"}
    assert client.post("/v1/predict", json=bad).status_code == 422


def test_predict_wrong_type_422(client):
    bad = dict(VALID_INPUT, euribor3m="not-a-number")
    assert client.post("/v1/predict", json=bad).status_code == 422


def test_model_card(client):
    r = client.get("/v1/model-card")
    assert r.status_code == 200
    body = r.json()
    assert body["approved_target"] == "y"
    assert body["problem_type"] == "binary_classification"
    assert "test_metrics" in body and "model_version" in body
