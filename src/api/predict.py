"""Prediction service: loads artifacts once and scores a single observation.

Adds per-prediction contributing factors (top-k from the persisted explainer) and a
business recommendation from the Phase 2 risk bands + the model's decision threshold.
The TreeExplainer is built once at startup, not per request.
"""

import json
from datetime import datetime, timezone
from functools import lru_cache

import joblib
import pandas as pd

from src.config import models_path, load_business_rules
from src.data.prepare import apply_engineering, ENGINEERED_FEATURES
from src.model import explain

_ALIASES = {
    "emp_var_rate": "emp.var.rate",
    "cons_price_idx": "cons.price.idx",
    "cons_conf_idx": "cons.conf.idx",
    "nr_employed": "nr.employed",
}


class Predictor:
    def __init__(self):
        self.pipeline = joblib.load(models_path("final_model.joblib"))
        self.spec = joblib.load(models_path("explainer.joblib"))
        self.metadata = json.loads(
            models_path("model_metadata.json").read_text(encoding="utf-8")
        )
        self.rules = load_business_rules()
        self.feature_columns = self.metadata["feature_columns"]
        self.raw_fields = [
            c for c in self.feature_columns if c not in ENGINEERED_FEATURES
        ]
        self.threshold = float(self.metadata["chosen_decision_threshold"])
        self.transformed_names = list(
            self.pipeline.named_steps["pre"].get_feature_names_out()
        )
        self._name_to_orig = self._build_name_map()
        # Build the SHAP explainer once; reuse it for every request.
        self._explainer = self._build_explainer()

    def _build_explainer(self):
        import shap

        return shap.TreeExplainer(self.pipeline.named_steps["est"])

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
        """Half-open bands [min, max); last band closes at 1.0.

        The low/medium boundary equals the model's decision threshold, so
        `prediction == 1` exactly when the band is not 'low' (no contradictions
        between the contact decision and the business recommendation).
        """
        bands = sorted(self.rules["risk_bands"], key=lambda b: b["max_probability"])
        for i, b in enumerate(bands):
            is_last = i == len(bands) - 1
            if prob < b["max_probability"] or (
                is_last and prob <= b["max_probability"]
            ):
                return b["band"], b["recommendation"]
        last = bands[-1]
        return last["band"], last["recommendation"]

    def predict(self, features: dict) -> dict:
        row = {_ALIASES.get(k, k): v for k, v in features.items()}
        df = pd.DataFrame([{k: row.get(k) for k in self.raw_fields}])
        df = apply_engineering(df).reindex(columns=self.feature_columns)

        pre = self.pipeline.named_steps["pre"]
        Xt = pre.transform(df)
        proba = float(self.pipeline.named_steps["est"].predict_proba(Xt)[0, 1])
        prediction = int(proba >= self.threshold)
        band, recommendation = self._band(proba)

        top = explain.top_contributions(
            self.spec,
            self.pipeline.named_steps["est"],
            Xt,
            k=5,
            explainer=self._explainer,
        )
        factors = [
            {
                "feature": t["feature"],
                "original_field": self._name_to_orig.get(t["feature"], "other"),
                "contribution": t["contribution"],
            }
            for t in (top or [])
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
