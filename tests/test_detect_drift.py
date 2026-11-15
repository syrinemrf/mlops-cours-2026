"""Tests de la détection de drift (src/detect_drift.py, Lab 3)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.dataset_config import load_config
from src.detect_drift import CURRENT_CSV, REFERENCE_CSV, detect, numeric_columns, psi
from src.simulate import drift

CFG = load_config()
DRIFT = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))["drift"]
needs_data = pytest.mark.skipif(
    not (REFERENCE_CSV.exists() and CURRENT_CSV.exists()), reason="dvc pull"
)


def test_psi_is_zero_on_identical_and_large_on_shifted():
    rng = np.random.default_rng(0)
    ref = pd.Series(rng.normal(size=2000))
    assert psi(ref, ref, numeric=True) == pytest.approx(0.0, abs=1e-9)
    assert psi(ref, ref + 1.0, numeric=True) > DRIFT["psi_threshold"]


def test_psi_categorical_handles_new_category():
    ref = pd.Series(["No"] * 70 + ["Yes"] * 30)
    cur = pd.Series(["No"] * 40 + ["Yes"] * 40 + ["Other"] * 20)
    assert np.isfinite(psi(ref, cur, numeric=False))
    assert psi(ref, cur, numeric=False) > DRIFT["psi_threshold"]


def test_ordinals_are_tested_as_categories():
    ref = pd.DataFrame({c: [1, 2] for c in CFG.columns})
    numeric = numeric_columns(CFG, ref)
    assert not set(CFG.categorical) & set(numeric)
    assert CFG.target not in numeric


def detected(ref, cur) -> list[str]:
    rows = detect(CFG, ref, cur, DRIFT["ks_alpha"], DRIFT["psi_threshold"])
    return [r["column"] for r in rows if r["drift"]]


@needs_data
def test_no_drift_between_train_and_test():
    """Split stratifié aléatoire : aucune colonne ne doit dériver (constat du 2026-11-08)."""
    assert detected(pd.read_csv(REFERENCE_CSV), pd.read_csv(CURRENT_CSV)) == []


@needs_data
def test_simulated_scenario_is_detected_on_its_columns():
    scenario = DRIFT["simulation"]
    moved = {*scenario.get("scale", {}), *scenario.get("shift", {}), *scenario.get("reassign", {})}
    cur = drift(pd.read_csv(CURRENT_CSV), scenario, seed=CFG.random_state)
    found = detected(pd.read_csv(REFERENCE_CSV), cur)
    assert set(found) == moved
    assert len(found) / len(CFG.columns) >= DRIFT["drift_share"]
