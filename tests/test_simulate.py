"""Tests des lots simulés (src/simulate.py, Lab 3) : sain, corrompu, déplacé."""

from pathlib import Path

import pandas as pd
import pytest

from src.dataset_config import load_config
from src.simulate import clean, corrupt, drift, load_params

CFG = load_config()
PARAMS = load_params()
needs_data = pytest.mark.skipif(not Path(CFG.raw_path).exists(), reason="dvc pull")


@pytest.fixture(scope="module")
def raw() -> pd.DataFrame:
    return pd.read_csv(CFG.raw_path)


@needs_data
def test_clean_is_a_real_subsample(raw):
    out = clean(CFG, raw)
    assert len(out) == round(len(raw) * PARAMS["simulation"]["sample_frac"])
    assert out.merge(raw, how="left", indicator=True)["_merge"].eq("both").all()


@needs_data
def test_corrupt_injects_the_three_declared_bugs(raw):
    scenario = PARAMS["simulation"]["corrupt"]
    out = corrupt(CFG, raw)
    col, factor = next(iter(scenario["unit_scale"].items()))
    assert (out[col] == raw[col] * factor).all()
    unknown = scenario["unknown_code"]
    share = (out[unknown["column"]] == unknown["value"]).mean()
    assert share == pytest.approx(unknown["rate"], abs=0.005)
    assert out[CFG.target].isna().mean() == pytest.approx(
        scenario["missing_target_rate"], abs=0.005
    )
    assert raw[CFG.target].notna().all()  # l'entrée n'est pas modifiée


@needs_data
def test_corrupt_is_deterministic(raw):
    pd.testing.assert_frame_equal(corrupt(CFG, raw), corrupt(CFG, raw))


@needs_data
def test_drift_keeps_dtypes_and_domain(raw):
    scenario = PARAMS["drift"]["simulation"]
    out = drift(raw, scenario, seed=CFG.random_state)
    assert (out.dtypes == raw.dtypes).all()
    for col in scenario.get("shift") or {}:
        assert out[col].between(raw[col].min(), raw[col].max()).all()
    for col, spec in (scenario.get("reassign") or {}).items():
        assert (out[col] == spec["value"]).mean() > (raw[col] == spec["value"]).mean()
