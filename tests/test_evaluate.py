"""Evaluation uses stored thresholds and requires no tracking server or new fit."""

import json
from types import SimpleNamespace as NS

import numpy as np
import pandas as pd
import pytest

from src import evaluate
from src.dataset_config import load_config


@pytest.mark.parametrize("threshold", [0.5, 0.85])
def test_local_evaluation_uses_metadata_threshold(monkeypatch, tmp_path, threshold):
    cfg = load_config()
    X = pd.DataFrame({"synthetic": [1, 2, 3, 4]})
    y = pd.Series([0, 0, 1, 1])
    model = NS(predict_proba=lambda _: np.array([[0.9, 0.1], [0.2, 0.8], [0.6, 0.4], [0.1, 0.9]]))
    monkeypatch.setattr(
        evaluate,
        "load_config",
        lambda: NS(
            read_xy=lambda _: (X, y),
            primary_metric=cfg.primary_metric,
            business_cost=cfg.business_cost,
        ),
    )
    monkeypatch.setattr(evaluate, "mlflow", NS(sklearn=NS(load_model=lambda _: model)))
    monkeypatch.setattr(
        evaluate.Model, "load", lambda _: NS(metadata={"decision_threshold": threshold})
    )
    monkeypatch.setattr(evaluate, "METRICS_JSON", tmp_path / "metrics.json")
    evaluate.main()
    report = json.loads((tmp_path / "metrics.json").read_text())
    assert report["roc_auc"] == 0.75 and report["n_test"] == 4
    expected = (
        {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
        if threshold == 0.5
        else {"tn": 2, "fp": 0, "fn": 1, "tp": 1}
    )
    assert report["confusion"] == expected
    assert report["decision_threshold"] == threshold
    first = (tmp_path / "metrics.json").read_bytes()
    evaluate.main()
    assert first == (tmp_path / "metrics.json").read_bytes()


def test_rejects_nonfinite_threshold(monkeypatch, tmp_path):
    monkeypatch.setattr(evaluate, "load_config", lambda: NS(read_xy=lambda _: (None, None)))
    monkeypatch.setattr(evaluate, "mlflow", NS(sklearn=NS(load_model=lambda _: None)))
    monkeypatch.setattr(
        evaluate.Model, "load", lambda _: NS(metadata={"decision_threshold": float("nan")})
    )
    monkeypatch.setattr(evaluate, "METRICS_JSON", tmp_path / "metrics.json")
    with pytest.raises(ValueError, match="threshold"):
        evaluate.main()
    assert not (tmp_path / "metrics.json").exists()
