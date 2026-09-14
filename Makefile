# Bank Marketing Prediction - Makefile
# Auto-detect a project virtualenv; fall back to system python3.
VENV := .venv
PY  := $(shell test -x $(VENV)/bin/python && echo $(VENV)/bin/python || echo python3)
PIP := $(PY) -m pip

.PHONY: help setup data-audit business-analysis target-proposal train test \
        run-api run-predict-app run-dashboard docker-build docker-up docker-down clean

help:
	@echo "Available targets:"
	@echo "  make setup              Create virtualenv and install pinned requirements"
	@echo "  make data-audit         Run Phase 1 scripts (audit + data dictionary)"
	@echo "  make business-analysis  Run Phase 2 scripts (5 business questions)"
	@echo "  make target-proposal    Run Phase 3 script (target proposal)"
	@echo "  make train              Run Phase 4: baseline -> candidates -> final evaluation"
	@echo "  make test               Run pytest on /tests"
	@echo "  make run-api            Start FastAPI locally (uvicorn :8000)"
	@echo "  make run-predict-app    Start the Streamlit predictive app (:8501)"
	@echo "  make run-dashboard      Start the Streamlit business dashboard (:8502)"
	@echo "  make docker-build       Build the Docker image"
	@echo "  make docker-up          Start all services via docker-compose"
	@echo "  make docker-down        Stop all services"

$(VENV)/bin/python:
	python3 -m venv $(VENV)

setup: $(VENV)/bin/python
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Setup complete. Interpreter: $(PY)"

data-audit:
	$(PY) scripts/p1_data_dictionary.py
	$(PY) scripts/p1_data_audit.py

business-analysis:
	$(PY) scripts/p2_q01_channel_conversion.py
	$(PY) scripts/p2_q02_economic_conditions.py
	$(PY) scripts/p2_q03_customer_profile.py
	$(PY) scripts/p2_q04_contact_history.py
	$(PY) scripts/p2_q05_campaign_effort.py

target-proposal:
	$(PY) scripts/p3_target_proposal.py

train:
	$(PY) scripts/p4_train_baseline.py
	$(PY) scripts/p4_train_candidate_models.py
	$(PY) scripts/p4_evaluate_final_model.py

test:
	$(PY) -m pytest tests -v

run-api:
	$(PY) -m uvicorn src.api.main:app --host $${API_HOST:-0.0.0.0} --port $${API_PORT:-8000}

run-predict-app:
	$(PY) -m streamlit run apps/predict_app/app.py --server.port 8501

run-dashboard:
	$(PY) -m streamlit run apps/dashboard/app.py --server.port 8502

docker-build:
	docker build -t bank-marketing-prediction:latest .

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
