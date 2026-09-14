# Business Dashboard - Documentation (Phase 7)

Streamlit dashboard that answers **what happened, why, and what the business should
do** across the five selected business questions.

## Run

```bash
make run-dashboard
# or
streamlit run apps/dashboard/app.py --server.port 8502
```

Reads `data/raw/bank_data.csv` directly (path overridable via the `DATA_PATH` env var);
no API dependency.

## What it shows

### KPIs (recomputed from the current filters)
- **Contacts** in view, **Subscribers**, **Conversion %**, **Warm share** (previously
  contacted), **Contacts per subscriber** (effort proxy).

### Interactive filters (sidebar)
- Contact channel, contact month, Euribor band, and a "warm leads only" toggle. Every
  KPI and chart recomputes live on the filtered subset.

### Charts (one block per Phase 2 question)
1. **Q01 Channel** - conversion by contact channel.
2. **Q02 Macro** - conversion by interest-rate band.
3. **Q03 Segments** - conversion by job and by age band.
4. **Q04 History** - conversion by prior-contact status and previous outcome
   (with an explicit leakage note, since the production model excludes `poutcome`).
5. **Q05 Effort** - conversion by number of contacts.

Each chart is paired with a "Why / Action" caption so the view is directly
actionable, and a summary table underlies every chart.

### What happened / Why / What to do
A closing panel consolidates the operating recommendations (when to run, who to call,
which channel, attempt caps, and the follow-on use of the predictive model).

## Data lineage

All figures are computed from the raw dataset at runtime using the same response-rate
aggregations as the Phase 2 scripts, so the dashboard stays consistent with
`docs/business_analysis_report.md`.

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATA_PATH` | `data/raw/bank_data.csv` | Dataset location (resolved relative to the project root). |
