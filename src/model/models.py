"""Candidate models and baseline for the approved binary classification target."""

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from src.config import load_model_config


def get_seed():
    return int(load_model_config()["random_seed"])


def build_baseline():
    """Prior-probability baseline (majority class via predict, class prior via proba)."""
    return DummyClassifier(strategy="prior", random_state=get_seed())


def get_candidates():
    seed = get_seed()
    return {
        "LogisticRegression": LogisticRegression(
            C=1.0,
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
            random_state=seed,
        ),
        "DecisionTreeClassifier": DecisionTreeClassifier(
            max_depth=12,
            min_samples_leaf=50,
            class_weight="balanced",
            random_state=seed,
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_leaf=5,
            class_weight="balanced",
            n_jobs=-1,
            random_state=seed,
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.1, max_depth=3, random_state=seed
        ),
    }


def supports_class_weight(name):
    return name in {
        "LogisticRegression",
        "DecisionTreeClassifier",
        "RandomForestClassifier",
    }


def balanced_sample_weight(y):
    """Weights n/(k*count_class) per sample; used for GradientBoosting (no class_weight)."""
    y = np.asarray(y)
    classes, counts = np.unique(y, return_counts=True)
    weight_per_class = {
        c: len(y) / (len(classes) * cnt) for c, cnt in zip(classes, counts)
    }
    return np.array([weight_per_class[v] for v in y])


def is_tree_ensemble(name):
    return name in {
        "DecisionTreeClassifier",
        "RandomForestClassifier",
        "GradientBoostingClassifier",
    }


def is_linear(name):
    return name == "LogisticRegression"
