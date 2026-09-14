# Model Card - GradientBoostingClassifier v1.0.0

| Field | Value |
| --- | --- |
| Purpose | Predict probability a client subscribes a term deposit on contact |
| Target | y (binary: yes/no) |
| Problem type | Binary classification |
| Selected model | GradientBoostingClassifier |
| Version | 1.0.0 |
| Decision threshold | 0.31 (validation, cost-based) |
| Test PR-AUC | 0.4753 |
| Test ROC-AUC | 0.8194 |
| Test recall / precision @ thr | 0.8606 / 0.1875 |
| Test accuracy | 0.5640 |
| Trainable features | 19 (excludes duration, poutcome, campaign) |

## Intended use / out-of-scope
- Use: rank and tier marketing contacts for the term-deposit offer.
- Out of scope: any product other than term deposits; real-time pre-call scoring where the excluded fields' availability is uncertain.

## Key drivers (top)
- `cat__job_student` (importance 0.13816)
- `cat__job_services` (importance 0.04403)
- `cat__job_technician` (importance 0.02947)
- `num__nr.employed` (importance 0.01922)
- `cat__job_admin.` (importance 0.01547)
- `cat__job_unemployed` (importance 0.01369)
- `cat__job_blue-collar` (importance 0.01018)
- `cat__job_retired` (importance 0.00514)

## Limitations & risks
- Term-deposit response model for the historical (2008-2010) campaign context.
- duration/poutcome/campaign excluded per user-approved feature policy.
- Class imbalance handled via balanced weights; PR-AUC primary metric.
- Macro-indicator drift may limit transfer to future economic regimes.

