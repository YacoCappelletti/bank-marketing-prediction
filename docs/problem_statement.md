# Problem Statement - Neutral Discovery (Phase 1)

> **Governance note (G1).** This document is a neutral, diagnostic discovery of business
> problems and predictive opportunities present in the Bank Marketing dataset. The problems
> below are listed as **equal-weight options**. They are **not ranked**, no "most relevant"
> problem is chosen, and **no target variable is selected, ranked, or proposed in this phase.**
> Problem types (classification / regression) are stated only as **preliminary hypotheses**,
> not decisions. Target proposal and selection occur exclusively in Phase 3, subject to user
> approval (G2, G3, G4).

## Context

The dataset records direct out-bound cold-call marketing campaigns of a Portuguese banking
institution promoting a **term deposit**. Each row is a contact attempt combining client
demographics, existing-liability flags, campaign/contact attributes, and quarterly/monthly
socio-economic indicators. The business domain is lead prioritization and campaign
resource allocation.

Reference: UCI ML Repository, Bank Marketing (bank-additional-full); Moro, Cortez & Silva (2014).

## Business problems and predictive opportunities (equal-weight options)

Each option lists the expected business metric it could impact, the variables that descriptively
relate to it, and a preliminary problem-type hypothesis. Ordering is arbitrary and carries no
rank.

### Option A - Response likelihood for a term-deposit offer
- **Description:** Estimate, for a given client under given conditions, the likelihood that the
  campaign contact results in a subscription.
- **Expected business metric to impact:** conversion rate, cost per acquisition, revenue from
  term deposits.
- **Variables descriptively related:** client attributes (`age`, `job`, `marital`, `education`),
  liability flags (`default`, `housing`, `loan`), contact channel (`contact`), timing (`month`,
  `day_of_week`), prior-engagement history (`pdays`, `previous`, `poutcome`), and macro indicators
  (`emp.var.rate`, `cons.price.idx`, `cons.conf.idx`, `euribor3m`, `nr.employed`).
- **Preliminary problem-type hypothesis:** binary classification (a discrete outcome-style field
  exists in the data). Hypothesis only - not a decision.

### Option B - Contact-channel and timing effectiveness
- **Description:** Understand which channel and contact timing are associated with better
  reachability and engagement, so campaigns can be allocated efficiently.
- **Expected business metric to impact:** answer/reach rate, cost per useful conversation,
  agent utilization.
- **Variables descriptively related:** `contact`, `month`, `day_of_week`, `campaign`,
  and outcome-style response fields.

### Option C - Contact-intensity / effort estimation
- **Description:** Estimate the number of contact attempts a client needs before a decision, to
  plan call-center effort and avoid over-contact.
- **Expected business metric to impact:** agent hours, cost per campaign, client fatigue/complaints.
- **Variables descriptively related:** `campaign`, `pdays`, `previous`, `poutcome`, `duration`
  (leakage-flagged), client attributes.
- **Preliminary problem-type hypothesis:** regression (count target). Hypothesis only.

### Option D - Macro-condition sensitivity of demand
- **Description:** Quantify how demand for term deposits moves with the economic environment
  (interest rates, employment, confidence) to time and size campaign waves.
- **Expected business metric to impact:** total deposits booked, ROI by campaign period.
- **Variables descriptively related:** `euribor3m`, `emp.var.rate`, `nr.employed`,
  `cons.price.idx`, `cons.conf.idx`, `month`.
- **Preliminary problem-type hypothesis:** classification or regression depending on the chosen
  outcome measure. Hypothesis only.

### Option E - Prior-relationship follow-up prioritization
- **Description:** Identify clients who already engaged with a previous campaign so follow-up
  resources are focused on warmer leads.
- **Expected business metric to impact:** conversion on re-contact, wasted-call reduction.
- **Variables descriptively related:** `poutcome`, `previous`, `pdays`, `campaign`.
- **Note:** `poutcome='success'` is leakage-flagged; any opportunity built on it must be reviewed
  for availability at decision time.

### Option F - Value-weighted client prioritization
- **Description:** Rank the client pool to reach (e.g., by expected value given demographics and
  economic context) to maximize return per call.
- **Expected business metric to impact:** revenue per contact, overall campaign margin.
- **Variables descriptively related:** broad set across all three data groups.

## Cross-cutting observations from Phase 1

- **Class imbalance** is present in the outcome-style fields (minority responses well under 20%),
  so any predictive task would need explicit imbalance handling.
- **`duration` is a leakage column** (only known after the call ends) and must be excluded from
  deployable models.
- **`pdays = 999`** is a sentinel ("never contacted"), not a real value.
- **No direct PII** is present; sensitive financial flags (`default`, `housing`, `loan`) require a
  documented privacy/fairness review.

---

**No target variable has been selected, ranked, or proposed in this phase (G1).** The candidate
variables above are described purely for discovery. Selection happens in Phase 3 with mandatory
inputs from the data dictionary, the data quality report, and the Phase 2 business analysis, and
requires explicit user approval.
