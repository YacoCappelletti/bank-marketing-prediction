# Data Dictionary

Bank Marketing dataset (`data/raw/bank_data.csv`, semicolon-separated).

- **Rows:** 41,188  | **Columns:** 21
- **Source:** UCI Machine Learning Repository - Bank Marketing (bank-additional-full); Moro, Cortez & Silva (2014).
- **Governance (G1):** the `Candidate target (Phase 3)` column below is a purely factual flag identifying outcome-style columns. No target variable is selected, ranked, or proposed in this phase.

## Column overview

| Column | Type | Role | Missing | Unique | Leak? | PII? | Temporal | Usable feat. | Cand. target (flag) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| age | int64 | numeric_discrete | 0 | 78 | no | no | no | yes | no |
| job | str | categorical_nominal | 0 | 12 | no | no | no | yes | no |
| marital | str | categorical_nominal | 0 | 4 | no | no | no | yes | no |
| education | str | categorical_ordinal | 0 | 8 | no | no | no | yes | no |
| default | str | binary | 0 | 3 | no | yes | no | conditional | no |
| housing | str | binary | 0 | 3 | no | yes | no | conditional | no |
| loan | str | binary | 0 | 3 | no | yes | no | conditional | no |
| contact | str | categorical_nominal | 0 | 2 | no | no | no | yes | no |
| month | str | categorical_ordinal | 0 | 10 | no | no | yes | conditional | no |
| day_of_week | str | categorical_ordinal | 0 | 5 | no | no | yes | conditional | no |
| duration | int64 | numeric_continuous | 0 | 1544 | yes | no | no | no | no |
| campaign | int64 | numeric_discrete | 0 | 42 | no | no | no | yes | no |
| pdays | int64 | numeric_discrete | 0 | 27 | no | no | no | conditional | no |
| previous | int64 | numeric_discrete | 0 | 8 | no | no | no | yes | no |
| poutcome | str | categorical_nominal | 0 | 3 | yes | no | no | conditional | no |
| emp.var.rate | float64 | numeric_continuous | 0 | 10 | no | no | no | yes | no |
| cons.price.idx | float64 | numeric_continuous | 0 | 26 | no | no | no | yes | no |
| cons.conf.idx | float64 | numeric_continuous | 0 | 26 | no | no | no | yes | no |
| euribor3m | float64 | numeric_continuous | 0 | 316 | no | no | no | yes | no |
| nr.employed | float64 | numeric_continuous | 0 | 11 | no | no | no | yes | no |
| y | str | binary | 0 | 2 | not_applicable (outcome column) | no | no | no | yes |

## Column details

### `age`

| Field | Value |
| --- | --- |
| description | Age of the client. |
| data_type | int64 |
| semantic_type | numeric_discrete |
| business_meaning | Client demographic; used for segment-level targeting and product fit. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 78 |
| unknown_category_count | 0 |
| example_values | 56, 57, 37, 40, 45 |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Static client attribute, known before the campaign. |
| pii_sensitive | no |
| pii_category | none (quasi-identifier on its own; not a direct identifier) |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=17.0, max=98.0, mean=40.0241, median=38.0, std=10.4211, IQR outliers=469 (1.139%) |

### `job`

| Field | Value |
| --- | --- |
| description | Type of job (categorical). |
| data_type | str |
| semantic_type | categorical_nominal |
| business_meaning | Occupational segment; proxies income and product needs. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 12 |
| unknown_category_count | 330 |
| example_values | housemaid, services, admin., blue-collar, technician |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Pre-existing client attribute. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | admin.=10,422, blue-collar=9,254, technician=6,743, services=3,969, management=2,924, retired=1,720, entrepreneur=1,456, self-employed=1,421 |

### `marital`

| Field | Value |
| --- | --- |
| description | Marital status (categorical: married, single, divorced; 'unknown' possible). |
| data_type | str |
| semantic_type | categorical_nominal |
| business_meaning | Household life-stage; relevant to savings/loan propensity. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 4 |
| unknown_category_count | 80 |
| example_values | married, single, divorced, unknown |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Pre-existing client attribute. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | married=24,928, single=11,568, divorced=4,612, unknown=80 |

### `education`

| Field | Value |
| --- | --- |
| description | Education level (categorical; 'unknown' possible). |
| data_type | str |
| semantic_type | categorical_ordinal |
| business_meaning | Financial literacy proxy; ordinal from basic.4y to university.degree. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 8 |
| unknown_category_count | 1731 |
| example_values | basic.4y, high.school, basic.6y, basic.9y, professional.course |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Pre-existing client attribute. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | university.degree=12,168, high.school=9,515, basic.9y=6,045, professional.course=5,243, basic.4y=4,176, basic.6y=2,292, unknown=1,731, illiterate=18 |

### `default`

| Field | Value |
| --- | --- |
| description | Has credit in default? (no, yes, unknown). |
| data_type | str |
| semantic_type | binary |
| business_meaning | Credit-risk flag; sensitive financial standing of the client. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 3 |
| unknown_category_count | 8597 |
| example_values | no, unknown, yes |
| usable_as_feature | conditional |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Known before the campaign, but a sensitive financial attribute. |
| pii_sensitive | yes |
| pii_category | financial / credit standing (sensitive) |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | no=32,588, unknown=8,597, yes=3 |

### `housing`

| Field | Value |
| --- | --- |
| description | Has housing loan? (no, yes, unknown). |
| data_type | str |
| semantic_type | binary |
| business_meaning | Existing liability; indicates cash-flow commitments. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 3 |
| unknown_category_count | 990 |
| example_values | no, yes, unknown |
| usable_as_feature | conditional |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Known before the campaign; sensitive financial attribute. |
| pii_sensitive | yes |
| pii_category | financial / existing liability (sensitive) |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | yes=21,576, no=18,622, unknown=990 |

### `loan`

| Field | Value |
| --- | --- |
| description | Has personal loan? (no, yes, unknown). |
| data_type | str |
| semantic_type | binary |
| business_meaning | Existing liability; indicates cash-flow commitments. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 3 |
| unknown_category_count | 990 |
| example_values | no, yes, unknown |
| usable_as_feature | conditional |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Known before the campaign; sensitive financial attribute. |
| pii_sensitive | yes |
| pii_category | financial / existing liability (sensitive) |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | no=33,950, yes=6,248, unknown=990 |

### `contact`

| Field | Value |
| --- | --- |
| description | Contact communication type (cellular, telephone). |
| data_type | str |
| semantic_type | categorical_nominal |
| business_meaning | Channel used to reach the client; drives reachability and answer rate. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 2 |
| unknown_category_count | 0 |
| example_values | telephone, cellular |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Known at dial time, before the outcome. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | cellular=26,144, telephone=15,044 |

### `month`

| Field | Value |
| --- | --- |
| description | Last contact month of year (jan..dec). |
| data_type | str |
| semantic_type | categorical_ordinal |
| business_meaning | Seasonality of the campaign wave; strong macro/behavioral signal. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 10 |
| unknown_category_count | 0 |
| example_values | may, jun, jul, aug, oct |
| usable_as_feature | conditional |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Known at contact time. Cyclical/seasonal field. |
| pii_sensitive | no |
| pii_category | none |
| temporal | yes |
| temporal_reason | Time-ordered field (month of year); enables temporal/seasonal features. |
| value_distribution (top) | may=13,769, jul=7,174, aug=6,178, jun=5,318, nov=4,101, apr=2,632, oct=718, sep=570 |

### `day_of_week`

| Field | Value |
| --- | --- |
| description | Last contact day of week (mon..fri). |
| data_type | str |
| semantic_type | categorical_ordinal |
| business_meaning | Weekly contact timing; affects answer quality. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 5 |
| unknown_category_count | 0 |
| example_values | mon, tue, wed, thu, fri |
| usable_as_feature | conditional |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Known at contact time. Cyclical field. |
| pii_sensitive | no |
| pii_category | none |
| temporal | yes |
| temporal_reason | Time-ordered field (day of week); cyclical. |
| value_distribution (top) | thu=8,623, mon=8,514, wed=8,134, tue=8,090, fri=7,827 |

### `duration`

| Field | Value |
| --- | --- |
| description | Last contact duration, in seconds. |
| data_type | int64 |
| semantic_type | numeric_continuous |
| business_meaning | Length of the completed call. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 1544 |
| unknown_category_count | 0 |
| example_values | 261, 149, 226, 151, 307 |
| usable_as_feature | no |
| candidate_target_phase3 | no |
| potential_data_leakage | yes |
| leakage_reason | Only known AFTER the call ends and is a near-deterministic proxy for the outcome (a refusal typically ends the call early). Must be excluded from any pre-call/predictive model. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=0.0, max=4918.0, mean=258.285, median=180.0, std=259.2761, IQR outliers=2,963 (7.194%) |

### `campaign`

| Field | Value |
| --- | --- |
| description | Number of contacts performed during this campaign for this client. |
| data_type | int64 |
| semantic_type | numeric_discrete |
| business_meaning | Contact intensity within the current campaign; over-contact can fatigue clients. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 42 |
| unknown_category_count | 0 |
| example_values | 1, 2, 3, 4, 5 |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Counts contacts up to and including the current one; borderline but commonly used. Documented as monitored. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=1.0, max=56.0, mean=2.5676, median=2.0, std=2.77, IQR outliers=2,406 (5.842%) |

### `pdays`

| Field | Value |
| --- | --- |
| description | Number of days that passed after the client was contacted by a previous campaign (999 = not contacted before). |
| data_type | int64 |
| semantic_type | numeric_discrete |
| business_meaning | Recency of prior contact; 999 is a sentinel for 'never contacted'. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 27 |
| unknown_category_count | 0 |
| example_values | 999, 6, 4, 3, 5 |
| usable_as_feature | conditional |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Pre-campaign history. Contains a 999 sentinel requiring explicit handling. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=0.0, max=999.0, mean=962.4755, median=999.0, std=186.9086, IQR outliers=1,515 (3.678%) |

### `previous`

| Field | Value |
| --- | --- |
| description | Number of contacts performed before this campaign for this client. |
| data_type | int64 |
| semantic_type | numeric_discrete |
| business_meaning | Prior engagement volume with the bank. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 8 |
| unknown_category_count | 0 |
| example_values | 0, 1, 2, 3, 4 |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | Pre-campaign history. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=0.0, max=7.0, mean=0.173, median=0.0, std=0.4949, IQR outliers=5,625 (13.657%) |

### `poutcome`

| Field | Value |
| --- | --- |
| description | Outcome of the previous marketing campaign (failure, nonexistent, success). |
| data_type | str |
| semantic_type | categorical_nominal |
| business_meaning | Whether a prior campaign converted this client. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 3 |
| unknown_category_count | 0 |
| example_values | nonexistent, failure, success |
| usable_as_feature | conditional |
| candidate_target_phase3 | no |
| potential_data_leakage | yes |
| leakage_reason | 'success' reflects a prior subscription and correlates strongly with the current outcome; usable only if the business truly has it at decision time. Flagged as potential leakage to review. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | nonexistent=35,563, failure=4,252, success=1,373 |

### `emp.var.rate`

| Field | Value |
| --- | --- |
| description | Quarterly variation of employment rate (social indicator). |
| data_type | float64 |
| semantic_type | numeric_continuous |
| business_meaning | Macroeconomic labor-market condition at campaign time. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 10 |
| unknown_category_count | 0 |
| example_values | 1.1, 1.4, -0.1, -0.2, -1.8 |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | External macro indicator, available at campaign time. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason | Varies over time but is an aggregate indicator, not a per-row date field. |
| numeric_stats | min=-3.4, max=1.4, mean=0.0819, median=1.1, std=1.5709, IQR outliers=0 (0.0%) |

### `cons.price.idx`

| Field | Value |
| --- | --- |
| description | Monthly consumer price index (social indicator). |
| data_type | float64 |
| semantic_type | numeric_continuous |
| business_meaning | Macroeconomic inflation proxy at campaign time. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 26 |
| unknown_category_count | 0 |
| example_values | 93.994, 94.465, 93.918, 93.444, 93.798 |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | External macro indicator. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=92.201, max=94.767, mean=93.5757, median=93.749, std=0.5788, IQR outliers=0 (0.0%) |

### `cons.conf.idx`

| Field | Value |
| --- | --- |
| description | Monthly consumer confidence index (social indicator). |
| data_type | float64 |
| semantic_type | numeric_continuous |
| business_meaning | Consumer sentiment at campaign time. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 26 |
| unknown_category_count | 0 |
| example_values | -36.4, -41.8, -42.7, -36.1, -40.4 |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | External macro indicator. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=-50.8, max=-26.9, mean=-40.5026, median=-41.8, std=4.6281, IQR outliers=447 (1.085%) |

### `euribor3m`

| Field | Value |
| --- | --- |
| description | Euribor 3-month rate (social indicator). |
| data_type | float64 |
| semantic_type | numeric_continuous |
| business_meaning | Interest-rate environment; strongly tied to term-deposit appeal. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 316 |
| unknown_category_count | 0 |
| example_values | 4.857, 4.856, 4.855, 4.859, 4.86 |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | External macro indicator. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=0.634, max=5.045, mean=3.6213, median=4.857, std=1.7344, IQR outliers=0 (0.0%) |

### `nr.employed`

| Field | Value |
| --- | --- |
| description | Number of employed citizens (social indicator). |
| data_type | float64 |
| semantic_type | numeric_continuous |
| business_meaning | Macro labor-market size proxy. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 11 |
| unknown_category_count | 0 |
| example_values | 5191.0, 5228.1, 5195.8, 5176.3, 5099.1 |
| usable_as_feature | yes |
| candidate_target_phase3 | no |
| potential_data_leakage | no |
| leakage_reason | External macro indicator. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| numeric_stats | min=4963.6, max=5228.1, mean=5167.0359, median=5191.0, std=72.2507, IQR outliers=0 (0.0%) |

### `y`

| Field | Value |
| --- | --- |
| description | Has the client subscribed a term deposit? (yes, no). |
| data_type | str |
| semantic_type | binary |
| business_meaning | Campaign response: whether the term-deposit was sold on this contact. |
| missing_count | 0 |
| missing_pct | 0.0 |
| unique_count | 2 |
| unknown_category_count | 0 |
| example_values | no, yes |
| usable_as_feature | no |
| candidate_target_phase3 | yes |
| potential_data_leakage | not_applicable (outcome column) |
| leakage_reason | This is the campaign outcome itself; not usable as a feature. |
| pii_sensitive | no |
| pii_category | none |
| temporal | no |
| temporal_reason |  |
| value_distribution (top) | no=36,548, yes=4,640 |

