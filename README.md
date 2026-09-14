# Bank Marketing Prediction

End-to-end analytical project on the **Bank Marketing** dataset (UCI Machine Learning
Repository, `bank-additional-full`; Moro, Cortez & Silva, 2014). It covers a neutral data
audit, a business-value analysis, a governed target-variable proposal, a machine-learning
model, a prediction API, a Streamlit predictive app, a business dashboard, and Docker
deployment.

The project follows a strict, gated methodology defined in [`PLAN.md`](PLAN.md). In
particular, no target variable is selected, ranked, or proposed before **Phase 3**, and no
model is trained before the user **explicitly approves** the proposed target
(governance rules **G1-G6**).

## Dataset

- **File:** `data/raw/bank_data.csv` (semicolon-separated, 41,188 rows x 21 columns)
- **Content:** direct-marketing campaigns of a Portuguese banking institution, combining
  client attributes, campaign attributes, and social/economic indicators.
- **Source:** UCI ML Repository - Bank Marketing dataset.

## Quickstart

```bash
make setup                 # create .venv and install pinned requirements
make data-audit            # Phase 1: audit + data dictionary
make business-analysis     # Phase 2: 5 business questions
make target-proposal       # Phase 3: target proposal (stops for your approval)
# --- approve the target in docs/json/target_approval.json (set "approved") ---
make train                 # Phase 4: baseline -> candidates -> final evaluation
make test                  # run pytest suite
```

## Running each layer

```bash
make run-api               # FastAPI prediction API on :8000
make run-predict-app       # Streamlit predictive app on :8501
make run-dashboard         # Streamlit business dashboard on :8502
```

## Full stack with Docker

A single image serves all three processes:

```bash
make docker-build
make docker-up             # api:8000, predict-app:8501, dashboard:8502
make docker-down
```

## Project structure

```
├── data/raw            raw dataset (versioned)
├── configs             project / model / business configuration (JSON)
├── scripts             phase scripts (p1_, p2_, p3_, p4_)
├── src                 package code: config loader + API (src/api)
├── apps                Streamlit predict app + dashboard
├── models              persisted model / preprocessor / explainer / metadata
├── tests             test_data.py, test_model.py, test_api.py
└── docs                Markdown reports, JSON artifacts, charts
```

## Key documents (`/docs`)

| Document | Purpose |
| --- | --- |
| [data_dictionary.md](docs/data_dictionary.md) | Per-column schema, PII/temporal/leakage flags |
| [data_quality_report.md](docs/data_quality_report.md) | Missing values, duplicates, imbalance, PII inventory |
| [problem_statement.md](docs/problem_statement.md) | Neutral discovery of business problems (no target, G1) |
| [business_analysis_report.md](docs/business_analysis_report.md) | Quantified insights and recommended actions |
| [target_proposal.md](docs/target_proposal.md) | Proposed target with evidence and approval gate |
| [model_report.md](docs/model_report.md) | Modeling decisions, evaluation, features, explanations |
| [model_card.md](docs/model_card.md) | Model purpose, performance, and limitations |
| [api_documentation.md](docs/api_documentation.md) | Prediction API reference |
| [deployment_documentation.md](docs/deployment_documentation.md) | Docker deployment guide |

## Governance

Target-variable selection is user-gated. See **Section 2** and **Section 3** of
[`PLAN.md`](PLAN.md) for rules G1-G6 and the approval workflow.
