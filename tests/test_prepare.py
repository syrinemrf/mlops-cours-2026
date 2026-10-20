"""Preparation and Feast schema checks using only synthetic rows."""

import hashlib
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from src import prepare
from src.dataset_config import load_config


@pytest.fixture
def inputs():
    cfg = load_config()
    df = pd.DataFrame({c: range(1, 101) for c in cfg.numeric})
    for c in cfg.categorical:
        df[c] = ["a", "b"] * 50
    df["EmployeeNumber"] = range(1001, 1101)
    df["Age"] = [29, 30, 44, 45] * 25
    df["Gender"] = ["Female", "Male"] * 50
    df["MaritalStatus"] = ["Single", "Married"] * 50
    df[cfg.target] = ["Yes"] * 20 + ["No"] * 80
    params = {"id_column": "EmployeeNumber", "event_timestamp": "2026-01-01T00:00:00+00:00"}
    return cfg, df, params


def test_split_preserves_identity_audit_and_target(inputs):
    cfg, df, params = inputs
    original = df.copy(deep=True)
    train, test, feast = prepare.prepare_frames(df, cfg, params)
    assert (len(train), len(test)) == (80, 20)
    assert (
        cfg.encode_target(train[cfg.target]).sum(),
        cfg.encode_target(test[cfg.target]).sum(),
    ) == (
        16,
        4,
    )
    assert not set(train.EmployeeNumber) & set(test.EmployeeNumber)
    merged = pd.concat([train, test]).sort_index()
    pd.testing.assert_frame_equal(merged, df[["EmployeeNumber", *cfg.columns]])
    assert list(feast) == ["EmployeeNumber", *cfg.features, "event_timestamp"]
    assert not {cfg.target, *cfg.extra_sensitive} & set(feast)
    assert all(feast[c].dtype == "float64" for c in cfg.numeric)
    assert all(feast[c].map(type).eq(str).all() for c in cfg.categorical)
    assert isinstance(feast.event_timestamp.dtype, pd.DatetimeTZDtype)
    assert str(feast.event_timestamp.dt.tz) == "UTC"
    assert feast.event_timestamp.nunique() == 1
    pd.testing.assert_frame_equal(df, original)  # function must not mutate inputs


def test_age_boundaries(inputs):
    cfg, df, _ = inputs
    assert cfg.sensitive_frame(df).Age_group.head(4).tolist() == ["<30", "30-44", "30-44", ">=45"]


@pytest.mark.parametrize("bad_id", ["duplicate", "missing", "negative", "float"])
def test_reject_invalid_identifier(inputs, bad_id):
    cfg, df, params = inputs
    if bad_id == "duplicate":
        df.loc[1, "EmployeeNumber"] = df.loc[0, "EmployeeNumber"]
    elif bad_id == "missing":
        df.loc[0, "EmployeeNumber"] = float("nan")
    elif bad_id == "negative":
        df.loc[0, "EmployeeNumber"] = -1
    else:
        df["EmployeeNumber"] = df.EmployeeNumber.astype(float) + 0.1
    with pytest.raises(ValueError, match="identifiers"):
        prepare.prepare_frames(df, cfg, params)


def test_identifier_fallback_and_feature_leakage_guard(inputs):
    cfg, df, params = inputs
    train, test, _ = prepare.prepare_frames(df.drop(columns="EmployeeNumber"), cfg, params)
    assert set(pd.concat([train, test]).EmployeeNumber) == set(range(1, 101))
    with pytest.raises(ValueError, match="identifier must be separate"):
        prepare.prepare_frames(df, replace(cfg, numeric=[*cfg.numeric, "EmployeeNumber"]), params)
    with pytest.raises(ValueError, match="audit attributes"):
        prepare.prepare_frames(df, replace(cfg, numeric=[*cfg.numeric, "Age"]), params)


@pytest.mark.parametrize("timestamp", ["2026-01-01", "NaT"])
def test_require_explicit_timestamp(inputs, timestamp):
    cfg, df, params = inputs
    with pytest.raises(ValueError, match="timestamp"):
        prepare.prepare_frames(df, cfg, dict(params, event_timestamp=timestamp))


@pytest.mark.parametrize("target", ["missing", "single", "wrong_positive"])
def test_require_valid_binary_target(inputs, target):
    cfg, df, params = inputs
    if target == "missing":
        df.loc[0, cfg.target] = None
    elif target == "single":
        df[cfg.target] = "No"
    else:
        df[cfg.target] = df[cfg.target].replace({"Yes": "Other"})
    with pytest.raises(ValueError):
        prepare.prepare_frames(df, cfg, params)


def test_written_outputs_are_deterministic_and_readable(inputs, monkeypatch, tmp_path):
    cfg, df, params = inputs
    raw = tmp_path / "raw.csv"
    df.to_csv(raw, index=False)
    monkeypatch.setattr(prepare, "load_config", lambda: replace(cfg, raw_path=str(raw)))
    monkeypatch.setattr(prepare, "PROCESSED", tmp_path / "processed")
    (tmp_path / "params.yaml").write_text(
        'prepare:\n  id_column: EmployeeNumber\n  event_timestamp: "2026-01-01T00:00:00+00:00"\n'
    )
    monkeypatch.chdir(tmp_path)
    prepare.main()
    files = sorted((tmp_path / "processed").iterdir())

    def digest(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    first = {p.name: digest(p) for p in files}
    prepare.main()
    assert {p.name: digest(p) for p in files} == first
    feast = pd.read_parquet(tmp_path / "processed/features.parquet")
    assert len(feast) == 100 and cfg.target not in feast
    for name, rows in [("train.csv", 80), ("test.csv", 20)]:
        X, y = cfg.read_xy(tmp_path / "processed" / name)
        assert len(X) == len(y) == rows
        assert list(X) == cfg.features
        assert all(X[c].dtype == "float64" for c in cfg.numeric)
