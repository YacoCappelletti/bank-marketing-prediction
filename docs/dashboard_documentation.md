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
- **Contacts** in view, **Subscribers**, **Conversion %** (with a delta vs. the full
  dataset), **Warm share** (previously contacted), **Contacts per subscriber** (effort
  proxy, with an inverse-colored delta), plus a **CSV download** of the filtered rows.

### Interactive filters (sidebar)
- Contact channel, contact month, Euribor band, and a "warm leads only" toggle. Every
  KPI and chart recomputes live on the filtered subset.

### Tabbed views (one per Phase 2 question)
1. **Overview** - Q01 conversion by channel and Q04 prior-contact status.
2. **Segments** - Q03 conversion by job and by age band.
3. **Macro** - Q02 conversion by interest-rate band.
4. **Effort** - Q05 conversion by number of contacts (with the leakage note about
   `poutcome`, excluded from the production model).
5. **Actions** - the consolidated "what happened / why / what to do" panel.

Every chart carries a dashed reference line at the overall response rate of the
current filter, plus a summary table underneath.

## Data lineage

All figures are computed from the raw dataset at runtime using the same response-rate
aggregations as the Phase 2 scripts, so the dashboard stays consistent with
`docs/business_analysis_report.md`.

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATA_PATH` | `data/raw/bank_data.csv` | Dataset location (resolved relative to the project root). |
