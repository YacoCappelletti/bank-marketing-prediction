# Business Questions - Phase 2

Ten business questions answerable with the Bank Marketing dataset, and the selection
of the **5 most important** by business impact, feasibility, and actionability.

> **Governance (G1).** This prioritization applies to **business questions only**. No
> modeling target variable is selected, ranked, or proposed here. Each selected question
> is answered descriptively in its own script; no predictive model is trained.

Base campaign response rate across the dataset: **11.27%**.

## The 10 candidate questions

| # | Question | Selected | Rationale / reason not selected |
| --- | --- | --- | --- |
| Q01 | Which contact channel (cellular vs telephone) converts best? | **Yes** | Directly controllable lever; 2.8x observed gap. Impact 4 / Feas 5 / Action 5. |
| Q02 | How do macroeconomic conditions relate to demand? | **Yes** | Strongest descriptive drivers; dictates wave timing. Impact 5 / Feas 5 / Action 4. |
| Q03 | Which customer segments respond best? | **Yes** | Enables calling-list curation; segments 2-4x base. Impact 4 / Feas 5 / Action 5. |
| Q04 | How does prior-contact history relate to response? | **Yes** | Warm leads convert ~64% vs ~9% cold. Impact 5 / Feas 4 / Action 4. |
| Q05 | How does contact intensity relate to conversion and effort? | **Yes** | Exposes effort inefficiency (83% on repeat dials). Impact 4 / Feas 5 / Action 5. |
| Q06 | What is response seasonality by month / day-of-week? | No | Correlated with Q02 (month drives macro indicators); folded in to avoid double-counting. |
| Q07 | Do existing liabilities (housing/loan/default) affect response? | No | Weak/ambiguous signal (`default` ~0.007% "yes"); privacy-sensitive; low actionability. |
| Q08 | Cold vs returning-client mix / campaign saturation? | No | Largely overlaps Q04; kept as context. |
| Q09 | How strongly does call duration track response? | No | `duration` is leakage-flagged; excluded from actionable analysis. |
| Q10 | Expected contacts-per-acquisition under current policy? | No | Partially covered by Q05; retained as a KPI, not a standalone question. |

## Selection method

Each candidate was scored 1-5 on three axes:

- **Business impact** - how much value a better decision would capture.
- **Feasibility** - how well the data can answer it (coverage, quality).
- **Actionability** - how directly the bank can act on the answer.

The top-5 (all scoring 13+/15) were selected. The remaining 5 were dropped for
overlap with a selected question (Q06, Q08, Q10), weak/sensitive signal (Q07), or
leakage exclusion (Q09). The five selected questions are collectively complete:
they cover channel, environment, audience, history, and effort - the five operational
dimensions of a cold-call campaign.

## Analysis per question

| Question | Script | Snippet | Metrics | Chart |
| --- | --- | --- | --- | --- |
| Q01 Channel | `scripts/p2_q01_channel_conversion.py` | `docs/snippets/p2_q01_output.md` | `docs/json/p2_q01_metrics.json` | `docs/images/p2_q01_chart.png` |
| Q02 Economic | `scripts/p2_q02_economic_conditions.py` | `docs/snippets/p2_q02_output.md` | `docs/json/p2_q02_metrics.json` | `docs/images/p2_q02_chart.png` |
| Q03 Segments | `scripts/p2_q03_customer_profile.py` | `docs/snippets/p2_q03_output.md` | `docs/json/p2_q03_metrics.json` | `docs/images/p2_q03_chart.png` |
| Q04 History | `scripts/p2_q04_contact_history.py` | `docs/snippets/p2_q04_output.md` | `docs/json/p2_q04_metrics.json` | `docs/images/p2_q04_chart.png` |
| Q05 Effort | `scripts/p2_q05_campaign_effort.py` | `docs/snippets/p2_q05_output.md` | `docs/json/p2_q05_metrics.json` | `docs/images/p2_q05_chart.png` |

Interpretations, evidence, and recommended actions are consolidated in
[`business_analysis_report.md`](business_analysis_report.md) and machine-readably in
[`json/insights.json`](json/insights.json). Operational logic is codified in
[`../configs/business_rules.json`](../configs/business_rules.json).
