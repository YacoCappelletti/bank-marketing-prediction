"""Reusable data preparation for Phase 4 modeling and Phase 5 serving.

Centralizes the approved target, the user's feature-exclusion policy, feature
engineering (pdays sentinel, age clipping), duplicate handling, and the fixed
stratified 70/15/15 split so every script and the API share identical logic.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import load_dataset, load_model_config, load_target_approval

# Derived features added by apply_engineering (serving must send the raw fields only).
ENGINEERED_FEATURES = ("previously_contacted", "pdays_days")


def assert_gate4():
    """G4: refuse to proceed unless the target is user-approved."""
    approval = load_target_approval()
    if approval.get("approval_status") != "approved":
        raise RuntimeError(
            "Phase 4 blocked (G4): target_approval.json is not 'approved'. "
            "Obtain explicit user approval first."
        )
    return approval


def target():
    return load_target_approval()["approved_target"]


def excluded_features():
    mc = load_model_config()
    return list(mc.get("feature_policy", {}).get("excluded_features", []))


def apply_engineering(df):
    """Deterministic feature engineering only (no target). Safe for single-row serving."""
    df = df.copy()
    sentinel = int(
        load_model_config().get("feature_policy", {}).get("pdays_sentinel", 999)
    )
    df["previously_contacted"] = np.where(df["pdays"] == sentinel, "no", "yes")
    df["pdays_days"] = df["pdays"].replace(sentinel, 0)
    df["age"] = df["age"].clip(lower=18, upper=95)
    return df


def engineer(df):
    """Feature engineering plus the target column (training only)."""
    df = apply_engineering(df)
    df["_target"] = (df[target()] == "yes").astype(int)
    return df


def feature_columns(df):
    ex = set(excluded_features()) | {target()}
    return [c for c in df.columns if c not in ex and not c.startswith("_")]


def split_frames(df):
    """Drop duplicate rows, then split 70/15/15 (stratified on the target)."""
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    df = engineer(df)
    cols = feature_columns(df)
    X = df[cols]
    y = df["_target"]

    seed = int(load_model_config()["random_seed"])
    sp = load_model_config()["split"]
    train_frac = sp["train_size"]
    test_frac = sp["test_size"]

    X_train, X_tmp, y_train, y_tmp = train_test_split(
        X, y, test_size=(1 - train_frac), stratify=y, random_state=seed
    )
    # split remainder into validation/test with correct proportions
    relative_test = test_frac / (1 - train_frac)
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=relative_test, stratify=y_tmp, random_state=seed
    )
    return X_train, X_val, X_test, y_train, y_val, y_test, cols


def categorical_and_numeric(cols):
    numeric = [
        "age",
        "pdays_days",
        "previous",
        "emp.var.rate",
        "cons.price.idx",
        "cons.conf.idx",
        "euribor3m",
        "nr.employed",
    ]
    numeric = [c for c in numeric if c in cols]
    categorical = [c for c in cols if c not in numeric]
    return categorical, numeric
