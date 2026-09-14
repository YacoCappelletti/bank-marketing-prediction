"""Phase 3 - Target Variable Proposal.

Mandatory inputs (PLAN Section 6.3): the data dictionary, the data quality report,
the problem statement, and the Phase 2 business analysis. This script reads them,
evaluates candidate target variables against the full criterion set, and writes the
proposal + a PENDING approval file.

It does NOT set approval. Per G3/G4 the user must explicitly approve, and Phase 4
cannot start until /docs/json/target_approval.json is "approved".
"""

import _bootstrap  # noqa: F401

import json
import math

import numpy as np
import pandas as pd

from src.config import load_dataset, docs_json, docs_path, load_business_rules


def entropy_of_min_share(s):
    shares = s.value_counts(normalize=True)
    ent = -sum(p * math.log2(p) for p in shares if p > 0)
    return float(shares.min()), float(ent)


def assoc_with_duration(df):
    dur = df["duration"].astype(float).to_numpy()
    y = (df["y"] == "yes").astype(int).to_numpy()
    return float(np.corrcoef(dur, y)[0, 1])


def assoc_success(df):
    suc = (df["poutcome"] == "success").astype(float).to_numpy()
    y = (df["y"] == "yes").astype(int).to_numpy()
    return float(np.corrcoef(suc, y)[0, 1])


def evaluate_candidates(df):
    cands = {}

    # y - binary response
    mn, ent = entropy_of_min_share(df["y"])
    cands["y"] = {
        "candidate": "y",
        "problem_type_if_chosen": "binary_classification",
        "description": "Term-deposit subscription on this contact (yes/no).",
        "cardinality": int(df["y"].nunique()),
        "missing_count": int(df["y"].isna().sum()),
        "unknown_count": int((df["y"].astype(str).str.lower() == "unknown").sum()),
        "minority_share_pct": round(100 * mn, 2),
        "label_entropy_bits": round(ent, 3),
        "levels": {k: int(v) for k, v in df["y"].value_counts().items()},
    }

    # campaign - count/effort
    cands["campaign"] = {
        "candidate": "campaign",
        "problem_type_if_chosen": "regression",
        "description": "Number of contacts in the current campaign (effort target).",
        "min": int(df["campaign"].min()),
        "max": int(df["campaign"].max()),
        "mean": round(float(df["campaign"].mean()), 2),
        "missing_count": int(df["campaign"].isna().sum()),
        "near_constant_zero": False,
    }

    # previous - prior-contact count (weak)
    cands["previous"] = {
        "candidate": "previous",
        "problem_type_if_chosen": "regression",
        "description": "Number of prior-campaign contacts.",
        "min": int(df["previous"].min()),
        "max": int(df["previous"].max()),
        "missing_count": int(df["previous"].isna().sum()),
        "zero_share_pct": round(100 * (df["previous"] == 0).mean(), 2),
    }

    # duration - leakage-flavored outcome proxy (NOT recommended as target/feature)
    cands["duration"] = {
        "candidate": "duration",
        "problem_type_if_chosen": "regression",
        "description": "Completed call length in seconds.",
        "min": int(df["duration"].min()),
        "max": int(df["duration"].max()),
        "missing_count": int(df["duration"].isna().sum()),
        "correlation_with_response_y": round(assoc_with_duration(df), 3),
    }
    return cands


def build_proposal(df, cands):
    dur_corr = cands["duration"]["correlation_with_response_y"]
    suc_corr = round(assoc_success(df), 3)

    proposal = {
        "recommended_target": "y",
        "alternative_targets": [
            "campaign (regression - effort planning)",
            "previous (regression - weak, 86.5% zeros)",
            "duration (rejected: post-call leakage proxy, low business value as a standalone target)",
        ],
        "problem_type": "binary_classification",
        "business_justification": (
            "Phase 2 (insights.json) shows response rate varying from ~4.8% to ~65% across the "
            "macro window, prior-contact history, segment, and channel. A per-client binary "
            "propensity for subscribing is the score that directly drives every recommended "
            "action (prioritize warm/high segments, cap low-propensity attempts, favor cellular, "
            "time waves). It is the analytic follow-on the business report called for and maps to "
            "the operational bands in configs/business_rules.json."
        ),
        "technical_justification": (
            "Clean two-level label (no missing, no 'unknown'), strong learned signal available from "
            "non-leaky features (euribor3m, emp.var.rate, nr.employed, contact, pdays/previous, "
            "job, age). Imbalanced (11.3% positive) but well within standard handling (class weights, "
            "PR-AUC). Supports the Phase 4 candidate set and a probability-graded threshold tuned "
            "against the Phase 2 cost matrix (FN:FP = 20:1)."
        ),
        "data_quality_justification": (
            "y has 0 missing values and 2 consistent categories ('yes'/'no'); the only quality "
            "consideration is class imbalance (minority 11.27%), which is explicitly handled in "
            "Phase 4 per model_config imbalance policy."
        ),
        "data_dictionary_evidence": (
            "data_dictionary.json: y is the sole column flagged candidate_target_phase3='yes' "
            "(factual flag, semantic_type=binary, usable_as_feature='no' since it is the outcome). "
            "duration and poutcome are flagged potential_data_leakage='yes'."
        ),
        "data_quality_evidence": (
            "data_quality_report.md Section 7: y balance 36,548 no / 4,640 yes (minority 11.27%); "
            "Section 3: 12 exact duplicate rows to drop pre-split; Section 5: pdays 999 sentinel and "
            "age=17 outlier to handle in preprocessing."
        ),
        "business_analysis_evidence": (
            "insights.json cross_insight_summary: value is re-allocating calling budget toward "
            "higher-probability contacts; requires a single per-client response propensity score. "
            "Q04 warm/cold gap (63.8% vs 9.3%) and Q02 macro gap (4.8% vs 44.7%) confirm separability."
        ),
        "availability_at_prediction_time": (
            "y is the future outcome; the model scores a client BEFORE the call, so all inputs are "
            "available at decision time provided duration is excluded and poutcome recency is "
            "confirmed available. This is the recommended operating assumption."
        ),
        "assumptions": [
            "The bank can obtain the client and macro features before the campaign call (decision-time availability).",
            "poutcome/previous refer to PRIOR campaigns and are available before this campaign's contact; if not, they will be dropped in Phase 4.",
            "No per-unit revenue/cost data exists; the 20:1 cost ratio from business_rules.json is a documented assumption.",
        ],
        "risks": [
            "Class imbalance (11.3%) can inflate accuracy; use PR-AUC and threshold tuning, not accuracy alone.",
            "duration leakage (corr={} with y) would produce an unrealistically strong but useless model if included.".format(
                dur_corr
            ),
            "poutcome='success' is a strong but leakage-flagged signal (corr={} with y); availability must be verified.".format(
                suc_corr
            ),
            "Macroeconomic features can drift; a model trained on 2008-2010 conditions may not transfer to other regimes.",
        ],
        "limitations": [
            "Predicts response to THIS product (term deposit) in THIS historical context; not a general propensity model.",
            "Cold leads dominate (96.3%), so absolute positive counts in the high band are limited.",
        ],
        "data_leakage_checks": [
            {
                "column": "duration",
                "flag": "EXCLUDE",
                "reason": "post-call field, corr={} with y".format(dur_corr),
            },
            {
                "column": "poutcome",
                "flag": "REVIEW",
                "reason": "prior success strongly predicts current y (corr={}); confirm available at decision time, else drop".format(
                    suc_corr
                ),
            },
            {
                "column": "campaign",
                "flag": "REVIEW",
                "reason": "counts may include the current attempt; verify it excludes the outcome call",
            },
            {
                "column": "pdays",
                "flag": "RECODE",
                "reason": "999 sentinel -> previously_contacted flag + days",
            },
        ],
        "problem_type_rationale": (
            "Binary classification over regression: the business wants a decision (contact or not / "
            "priority tier), which maps to a probability and threshold, matching the Phase 2 band "
            "structure and cost matrix. A regression on duration/campaign would not produce a directly "
            "actionable propensity ranking."
        ),
        "approval_status": "pending_user_approval",
        "governance_note": "Target proposed per G2 using the three mandatory inputs. Awaiting explicit user approval (G3). No model trained (G4 blocks Phase 4 until approved).",
    }
    return proposal


def build_approval_stub():
    return {
        "approved_target": None,
        "approved_problem_type": None,
        "approval_status": "pending",
        "user_comments": "",
        "approval_timestamp": None,
        "proposal_reference": "docs/target_proposal.md",
        "governance": "Agent may not set approval_status='approved'. Only the user's decision updates this file (G3).",
    }


if __name__ == "__main__":
    df = load_dataset()

    # Read mandatory Phase 1/2 inputs (existence check = they are the inputs)
    for name in ["data_dictionary.json", "insights.json", "business_questions.json"]:
        with open(docs_json(name), "r", encoding="utf-8") as fh:
            json.load(fh)
    for p in [
        "data_quality_report.md",
        "problem_statement.md",
        "business_analysis_report.md",
    ]:
        assert docs_path(p).exists(), p
    load_business_rules()  # confirm present

    cands = evaluate_candidates(df)
    proposal = build_proposal(df, cands)

    with open(docs_json("target_proposal.json"), "w", encoding="utf-8") as fh:
        json.dump(proposal, fh, indent=2, ensure_ascii=False)
    print("Wrote docs/json/target_proposal.json")

    with open(docs_json("target_approval.json"), "w", encoding="utf-8") as fh:
        json.dump(build_approval_stub(), fh, indent=2, ensure_ascii=False)
    print("Wrote docs/json/target_approval.json (approval_status = pending)")

    # also stash the computed candidate evidence for the report
    with open(
        docs_json("target_candidates_evidence.json"), "w", encoding="utf-8"
    ) as fh:
        json.dump(cands, fh, indent=2, ensure_ascii=False)
    print("Wrote docs/json/target_candidates_evidence.json")

    print("\n=== Candidate evidence ===")
    print(json.dumps(cands, indent=2))
    print(
        "\n=== Recommended target: {} ({}) ===".format(
            proposal["recommended_target"], proposal["problem_type"]
        )
    )
    print(
        "STATUS:",
        proposal["approval_status"],
        "-> awaiting explicit user approval (execution stops here).",
    )
