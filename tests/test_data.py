"""Phase 1 tests: dataset integrity and data-dictionary consistency."""

import json
import os

import pandas as pd
import pytest

from src.config import load_dataset, docs_json, docs_path, load_project_config
from src.data.columns import EXPECTED_COLUMNS


@pytest.fixture(scope="module")
def df():
    return load_dataset()


@pytest.fixture(scope="module")
def dictionary():
    with open(docs_json("data_dictionary.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_dataset_loads_and_nonempty(df):
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] > 0 and df.shape[1] > 0


def test_expected_columns_exist(df):
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    assert not missing, f"Missing expected columns: {missing}"


def test_no_unexpected_columns(df):
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    assert not extra, f"Unexpected columns present: {extra}"


def test_no_fully_empty_columns(df):
    empty = [c for c in df.columns if df[c].isna().all()]
    assert not empty, f"Fully-empty columns: {empty}"


def test_dtypes_match_dictionary(df, dictionary):
    dict_types = {c["name"]: c["data_type"] for c in dictionary["columns"]}
    for col, dtype in dict_types.items():
        assert col in df.columns
        assert str(df[col].dtype) == dtype, f"dtype mismatch for {col}"


def test_dictionary_row_count_matches(df, dictionary):
    assert dictionary["rows"] == int(df.shape[0])
    assert dictionary["column_count"] == int(df.shape[1])
    assert len(dictionary["columns"]) == int(df.shape[1])


def test_no_direct_pii_columns(df):
    forbidden = ["name", "email", "phone", "national_id", "passport", "account_number"]
    present = [c for c in forbidden if c in df.columns]
    assert not present, f"Direct PII columns found: {present}"


def test_governance_target_requires_approval():
    """G1/G4: a target may only be set in config if the user explicitly approved it.

    Before Phase 3 approval target_column must be null (G1). After approval it must
    exactly match the approved target with approval_status == 'approved' (G3/G4).
    """
    cfg = load_project_config()["dataset"]
    target = cfg["target_column"]
    with open(docs_json("target_approval.json"), "r", encoding="utf-8") as fh:
        approval = json.load(fh)
    if approval.get("approval_status") != "approved":
        assert target is None, "G1 violated: target set in config without approval."
    else:
        assert target == approval["approved_target"], (
            "Config target must match approved target."
        )


def test_phase1_deliverables_exist():
    for p in [
        "data_dictionary.md",
        "data_quality_report.md",
        "problem_statement.md",
        "images/p1_distributions.png",
    ]:
        assert os.path.exists(docs_path(p)), f"Missing Phase 1 deliverable: {p}"
    assert os.path.exists(docs_json("data_dictionary.json"))
