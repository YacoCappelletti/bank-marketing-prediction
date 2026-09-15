# Target Variable Proposal - Phase 3

> **This phase ends in a mandatory stop.** The proposal below requires explicit
> approval before any model is built. Approval is recorded only by the project
> stakeholder in `docs/json/target_approval.json` (G3). Phase 4 cannot start
> until that file reads `approval_status: "approved"` (G4).

## Recommended target

**`y` - "Has the client subscribed a term deposit on this contact?" (yes / no)**
**Problem type: binary classification.**

## Alternatives considered (not recommended)

| Candidate | Type if chosen | Verdict | Why |
| --- | --- | --- | --- |
| `campaign` | regression | Alternative | Predicting contact attempts is a valid effort-planning target (Phase 1 Option C) but is a weaker business driver than response and partly an *input* to the response story (Q05). |
| `previous` | regression | Rejected | 86.34% zeros - near-constant, negligible signal. |
| `duration` | regression | Rejected as target AND excluded as feature | Correlates **0.405** with `y`; it is a post-call field. As a standalone target it has little campaign value; as a feature it is leakage. |

## Evaluation of the recommended target (`y`)

| Criterion | Finding | Source |
| --- | --- | --- |
| Alignment with business problem | Directly scores Phase 2's core need: a per-client propensity to allocate a fixed calling budget. | insights.json |
| Actionability | High - maps to the low/medium/high bands in business_rules.json. | business_analysis_report.md |
| Availability at prediction time | Outcome is future; scored from pre-call features. Valid once `duration` is excluded and `poutcome` availability confirmed. | data_dictionary.md |
| Potential data leakage | None in the label itself; two inputs flagged (`duration` 0.405, `poutcome` 0.316). | data_quality_report.md |
| Data quality | 0 missing, 2 consistent levels, no "unknown". | data_quality_report.md |
| Class balance | Imbalanced: 36,548 no / 4,640 yes (minority 11.27%). | data_quality_report.md |
| Temporal consistency | Response tied to campaign month + macro window; handled via features. | data_dictionary.md |
| Ethical / legal | No direct PII; sensitive financial flags reviewed separately. | data_quality_report.md |
| ML feasibility | Strong non-leaky signal available; standard imbalance tooling suffices. | insights.json |

## Justification

**Business.** Phase 2 quantified response ranging from ~4.8% (high-rate windows, cold, telephone)
to ~65% (warm history, favorable macro). Every recommended action - prioritize warm leads, favor
cellular, cap low-propensity repeats, time waves to macro windows - is driven by a single
**probability of subscription**. `y` is exactly that label.

**Technical.** Clean two-class target; supports the Phase 4 candidate set (logistic regression,
tree, random forest, gradient boosting). Imbalance is handled by class weights + PR-AUC and by a
decision threshold tuned on validation against the Phase 2 cost matrix (FN:FP = 20:1), which
rightly biases toward catching subscribers.

**Data quality.** `y` is complete and well-defined. The only caveat is imbalance, which is
explicitly planned for.

## Evidence by input source

- **Data dictionary:** `y` is the only column factually flagged `candidate_target_phase3 = yes`
  (binary, `usable_as_feature = no` because it is the outcome). `duration` and `poutcome` carry
  `potential_data_leakage = yes`.
- **Data quality report:** balance 88.73 / 11.27; 12 duplicate rows to drop before splitting;
  `pdays` 999 sentinel and `age=17` outlier to handle in preprocessing.
- **Business analysis:** cross-insight summary states the whole value proposition is a per-client
  response propensity; Q02 and Q04 gaps confirm the population is separable.

## Data-leakage checks (carried into Phase 4)

1. **EXCLUDE `duration`** from all features (post-call, corr 0.405 with `y`).
2. **REVIEW `poutcome`** (corr 0.316): keep only if the bank confirms prior-campaign outcome is
   available at decision time; otherwise drop.
3. **REVIEW `campaign`**: ensure it counts attempts up to, not including, the outcome-defining call.
4. **RECODE `pdays`**: transform the 999 sentinel into a `previously_contacted` flag + numeric days.

## Assumptions

- Client + macroeconomic features are obtainable **before** the campaign call.
- `poutcome`/`previous` describe **prior** campaigns and are available at decision time.
- No per-unit revenue/cost data exists; the 20:1 cost ratio is a documented assumption to be
  replaced if the business supplies real economics.

## Risks

- Imbalance can make accuracy misleading (majority class = 88.7%) - use PR-AUC / thresholded recall.
- Leakage fields (`duration`, `poutcome`) can inflate apparent performance if mishandled.
- Macro-condition drift: a model fit on the 2008-2010 collection may not transfer to other regimes.

## Limitations

- Predicts response to the term-deposit product in the historical marketing context only.
- Cold leads are 96.3% of contacts, so the high-propensity band has limited absolute volume.

## Open questions for you

1. Do you **approve `y` (binary term-deposit subscription) as the modeling target**, or request changes?
2. Should `poutcome` (prior-campaign outcome) be treated as **available** at decision time, or dropped as leakage?
3. Is `campaign` interpreted as "attempts **before** this call" (so it can stay a feature)?
4. Any real **unit economics** to replace the assumed 20:1 false-negative:false-positive cost ratio?

---

**Approval status: `pending_user_approval`.** No model has been trained and none will be until
this file and `docs/json/target_approval.json` reflect your explicit approval (G3, G4).
