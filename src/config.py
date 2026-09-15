"""Shared configuration loader.

All scripts and services read paths, the random seed, and model/business
configuration from the JSON files under /configs via this module.
No hardcoded paths or seeds elsewhere (single source of truth in /configs).
"""

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIGS_DIR = ROOT / "configs"


@lru_cache(maxsize=None)
def _load(name):
    """JSON configs are immutable at runtime; cache to avoid disk I/O per request."""
    path = CONFIGS_DIR / name
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_project_config():
    return _load("project_config.json")


def load_model_config():
    return _load("model_config.json")


def load_business_rules():
    return _load("business_rules.json")


def load_target_approval():
    with open(docs_json("target_approval.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_target_proposal():
    with open(docs_json("target_proposal.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def resolve(relative_path, *parts):
    """Resolve a path that is relative to the project root, with optional extra parts."""
    return ROOT.joinpath(relative_path, *parts)


def raw_dataset_path():
    cfg = load_project_config()
    return resolve(cfg["dataset"]["raw_path"])


def processed_dir():
    cfg = load_project_config()
    return resolve(cfg["dataset"]["processed_dir"])


def docs_path(*parts):
    cfg = load_project_config()
    return resolve(cfg["paths"]["docs_dir"], *parts)


def docs_json(name):
    cfg = load_project_config()
    return resolve(cfg["paths"]["docs_json_dir"], name)


def docs_images(name):
    cfg = load_project_config()
    return resolve(cfg["paths"]["docs_images_dir"], name)


def docs_snippets(name):
    cfg = load_project_config()
    return resolve(cfg["paths"]["docs_snippets_dir"], name)


def models_path(name):
    cfg = load_project_config()
    return resolve(cfg["paths"]["models_dir"], name)


def get_seed():
    return int(load_model_config()["random_seed"])


def load_dataset():
    """Load the raw dataset using the configuration (separator, header)."""
    cfg = load_project_config()["dataset"]
    return pd.read_csv(
        raw_dataset_path(),
        sep=cfg["separator"],
        header=0 if cfg.get("has_header", True) else None,
    )
