"""Pydantic schemas for the prediction API (v2)."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

JOB = Literal[
    "admin.",
    "blue-collar",
    "technician",
    "services",
    "management",
    "retired",
    "entrepreneur",
    "self-employed",
    "housemaid",
    "unemployed",
    "student",
    "unknown",
]
MARITAL = Literal["married", "single", "divorced", "unknown"]
EDUCATION = Literal[
    "illiterate",
    "basic.4y",
    "basic.6y",
    "basic.9y",
    "high.school",
    "professional.course",
    "university.degree",
    "unknown",
]
YN = Literal["no", "yes", "unknown"]
CONTACT = Literal["cellular", "telephone"]
MONTH = Literal[
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
]
DOW = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class ClientFeatures(BaseModel):
    """One campaign contact observation, in the raw decision-time fields.

    `pdays` uses 999 as the 'never contacted before' sentinel (recoded internally).
    """

    age: int = Field(
        ...,
        ge=18,
        le=95,
        description="Client age (matching the training range; training data is clipped to [18, 95]).",
    )
    job: JOB
    marital: MARITAL
    education: EDUCATION
    default: YN
    housing: YN
    loan: YN
    contact: CONTACT
    month: MONTH
    day_of_week: DOW
    pdays: int = Field(
        ..., ge=0, le=999, description="Days since prior campaign contact; 999 = never."
    )
    previous: int = Field(..., ge=0, le=1000)
    emp_var_rate: float = Field(..., alias="emp.var.rate")
    cons_price_idx: float = Field(..., alias="cons.price.idx")
    cons_conf_idx: float = Field(..., alias="cons.conf.idx")
    euribor3m: float
    nr_employed: float = Field(..., alias="nr.employed")

    model_config = {"populate_by_name": True}


class ContributingFactor(BaseModel):
    feature: str
    original_field: str
    contribution: float


class PredictionResponse(BaseModel):
    prediction: int = Field(
        ..., description="1 = subscribed, 0 = not, at the model threshold."
    )
    predicted_class: Literal["yes", "no"]
    probability: float = Field(..., description="P(subscribe).")
    decision_threshold: float
    risk_band: str
    recommendation: str
    contributing_factors: List[ContributingFactor]
    model_version: str
    model_name: str
    target: str
    timestamp: datetime


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    model_loaded: bool
    model_version: Optional[str] = None


class ErrorDetail(BaseModel):
    detail: str
