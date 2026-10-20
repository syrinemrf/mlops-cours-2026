"""Feast schema and isolation of identity, sensitive attributes and target."""

from pathlib import Path

import pandas as pd
from feast.types import Float64, String

from features import definitions as d


def test_entity_and_contract_schema():
    assert d.employee.name == "employee"
    assert d.employee.join_key == "EmployeeNumber"
    schema = {field.name: field.dtype for field in d.request_features.schema}
    assert set(schema) == set(d.cfg.features)
    assert all(schema[c] == Float64 for c in d.cfg.numeric)
    assert all(schema[c] == String for c in d.cfg.categorical)
    assert not {"EmployeeNumber", d.cfg.target, "Age", "Gender", "MaritalStatus"} & set(schema)
    assert d.request_features.name == "request_features"
    assert d.scoring_v1.name == "scoring_v1"
    assert d.request_source.timestamp_field == "event_timestamp"
    assert Path(d.request_source.path) == d.ROOT / "data/processed/features.parquet"
    assert d.request_features.ttl.days == 3650


def test_offline_schema_matches_prepared_fixture():
    # Synthetic fixture: no network, registry, real employee rows or learned preprocessing.
    row = {c: [1.0] for c in d.cfg.numeric} | {c: ["label"] for c in d.cfg.categorical}
    row.update(EmployeeNumber=[1], event_timestamp=[pd.Timestamp("2026-01-01", tz="UTC")])
    frame = pd.DataFrame(row)
    assert set(frame) == {"EmployeeNumber", "event_timestamp", *d.cfg.features}
    assert pd.api.types.is_integer_dtype(frame.EmployeeNumber)
    assert all(frame[c].dtype == "float64" for c in d.cfg.numeric)
    assert frame.event_timestamp.dt.tz is not None
