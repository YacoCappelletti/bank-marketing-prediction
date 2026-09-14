"""Prediction service: loads artifacts once and scores a single observation.

Adds per-prediction contributing factors (top-k from the persisted explainer) and a
business recommendation from the Phase 2 risk bands + the model's decision threshold.
"""

import json
from datetime import datetime, timezone
from functools import lru_cache

import joblib
import pandas as pd

from src.config import models_path, load_business_rules, load_project_config
from src.data.prepare import apply_engineering, target
from src.model import explain

RAW_FIELDS = [
    "age",
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "day_of_week",
    "pdays",
    "previous",
    "emp.var.rate",
    "cons.price.idx",
    "cons.conf.idx",
    "euribor3m",
    "nr.employed",
]

_ALIAS = {
    "emp_var_rate": "emp.var.rate",
    "cons_price_idx": "cons.price.idx",
    "cons_conf_idx": "cons.conf.idx",
    "nr_employed": "nr.employed",
}


class Predictor:
    def __init__(self):
        self.pipeline = joblib.load(models_path("final_model.joblib"))
        self.spec = joblib.load(models_path("explainer.joblib"))
        self.metadata = json.load(
            open(models_path("model_metadata.json"), encoding="utf-8")
        )
        self.rules = load_business_rules()
        self.feature_columns = self.metadata["feature_columns"]
        self.threshold = float(self.metadata["chosen_decision_threshold"])
        self.transformed_names = list(
            self.pipeline.named_steps["pre"].get_feature_names_out()
        )
        self._name_to_orig = self._build_name_map()

    def _build_name_map(self):
        cols = sorted(self.feature_columns, key=len, reverse=True)
        mapping = {}
        for tn in self.transformed_names:
            orig = "other"
            if tn.startswith("num__"):
                base = tn[5:]
                if base in self.feature_columns:
                    orig = base
            elif tn.startswith("cat__"):
                rest = tn[5:]
                for c in cols:
                    if rest == c or rest.startswith(c + "_"):
                        orig = c
                        break
            mapping[tn] = orig
        return mapping

    def _band(self, prob):
        bands = sorted(self.rules["risk_bands"], key=lambda b: b["max_probability"])
        for b in bands:
            if prob <= b["max_probability"]:
                return b["band"], b["recommendation"]
        last = bands[-1]
        return last["band"], last["recommendation"]

    def predict(self, features: dict) -> dict:
        row = {_ALIAS.get(k, k): v for k, v in features.items()}
        df = pd.DataFrame([{k: row.get(k) for k in RAW_FIELDS}])
        df = apply_engineering(df).reindex(columns=self.feature_columns)

        proba = float(self.pipeline.predict_proba(df)[0, 1])
        prediction = int(proba >= self.threshold)
        band, recommendation = self._band(proba)

        Xt = self.pipeline.named_steps["pre"].transform(df)
        top = (
            explain.top_contributions(
                self.spec, self.pipeline.named_steps["est"], Xt, k=5
            )
            or []
        )
        factors = [
            {
                "feature": t["feature"],
                "original_field": self._name_to_orig.get(t["feature"], "other"),
                "contribution": t["contribution"],
            }
            for t in top
        ]

        return {
            "prediction": prediction,
            "predicted_class": "yes" if prediction == 1 else "no",
            "probability": round(proba, 6),
            "decision_threshold": self.threshold,
            "risk_band": band,
            "recommendation": recommendation,
            "contributing_factors": factors,
            "model_version": self.metadata["model_version"],
            "model_name": self.metadata["model_name"],
            "target": self.metadata["approved_target"],
            "timestamp": datetime.now(timezone.utc),
        }

    def model_card(self) -> dict:
        return self.metadata

    @property
    def version(self):
        return self.metadata["model_version"]


@lru_cache(maxsize=1)
def get_predictor() -> Predictor:
    return Predictor()
