"""Tests du contrat de données Great Expectations (src/validate_data.py, Lab 3)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.dataset_config import load_config
from src.validate_data import (
    PROJECT_ROOT,
    REFERENCE_CSV,
    SUITE,
    build_expectations,
    column_roles,
    load_rules,
    run_checks,
)

CFG = load_config()
SUITE_JSON = PROJECT_ROOT / "gx" / "expectations" / f"{SUITE}.json"
TEST_CSV = Path("data/processed/test.csv")
needs_data = pytest.mark.skipif(
    not (Path(CFG.raw_path).exists() and REFERENCE_CSV.exists() and TEST_CSV.exists()),
    reason="données locales absentes : dvc pull",
)


def committed_suite() -> list[dict]:
    return json.loads(SUITE_JSON.read_text(encoding="utf-8"))["expectations"]


def test_roles_come_from_contract_not_dtype():
    """Les ordinales déclarées catégorielles restent catégorielles, quel que soit leur dtype."""
    ref = pd.DataFrame({c: [1, 2] for c in CFG.columns})
    numeric, categorical = column_roles(CFG, ref)
    assert set(CFG.categorical) <= set(categorical)
    assert set(CFG.numeric) <= set(numeric)
    assert CFG.target not in numeric + categorical


def test_suite_covers_every_contract_column():
    covered: dict[str, int] = {}
    for e in committed_suite():
        for col in [e["kwargs"].get("column"), *e["kwargs"].get("column_set", [])]:
            covered[col] = covered.get(col, 0) + 1
    assert not [c for c in CFG.columns if covered.get(c, 0) < 3]


def test_business_rules_are_in_suite():
    pairs = {
        (e["kwargs"]["column_A"], e["kwargs"]["column_B"])
        for e in committed_suite()
        if e["type"] == "expect_column_pair_values_a_to_be_greater_than_b"
    }
    assert pairs == {tuple(p) for p in load_rules()["column_pairs"]}


@needs_data
def test_suite_is_built_from_train_only():
    """Pas de fuite : régénérer la suite depuis train.csv redonne exactement la suite commitée."""
    rebuilt = build_expectations(CFG, pd.read_csv(REFERENCE_CSV), load_rules())
    rebuilt_kwargs = [json.loads(json.dumps(e.configuration.kwargs)) for e in rebuilt]
    assert rebuilt_kwargs == [e["kwargs"] for e in committed_suite()]


@needs_data
def test_train_and_test_are_disjoint():
    id_col = load_rules()["id_column"]
    train, test = pd.read_csv(REFERENCE_CSV), pd.read_csv(TEST_CSV)
    assert not set(train[id_col]) & set(test[id_col])


@needs_data
def test_raw_data_passes_contract():
    checks = run_checks(CFG, pd.read_csv(CFG.raw_path))
    assert all(checks.values()), [k for k, ok in checks.items() if not ok]


@needs_data
def test_unknown_ordinal_code_is_rejected():
    """« 2: Level 2 » recodé en « 2 » : le one-hot l'ignorerait en silence, le contrat non."""
    df = pd.read_csv(CFG.raw_path)
    col = next(c for c in CFG.categorical if df[c].astype(str).str.contains(":").all())
    df[col] = df[col].str.split(":").str[0]
    failed = [k for k, ok in run_checks(CFG, df).items() if not ok]
    assert any(f"({col})" in name for name in failed), failed


@needs_data
def test_business_rule_violation_is_rejected():
    a, b = load_rules()["column_pairs"][0]
    df = pd.read_csv(CFG.raw_path)
    df[b] = df[a] + 1
    failed = [k for k, ok in run_checks(CFG, df).items() if not ok]
    assert any(f"({a}, {b})" in name for name in failed), failed
