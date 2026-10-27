"""Tests de l'analyse de sensibilité (src/sensitivity.py) : sur des probabilités simulées."""

import json

import numpy as np
import pytest

from src import sensitivity


def test_un_rapport_de_cout_eleve_abaisse_le_seuil():
    y = np.array([0, 0, 1, 1])
    proba = np.array([0.5, 0.6, 0.4, 0.9])
    assert sensitivity.best_threshold(y, proba, 1) == 0.9
    assert sensitivity.best_threshold(y, proba, 5) <= 0.4  # tous les positifs signalés


def test_le_rappel_ne_baisse_jamais_quand_le_rapport_augmente():
    rng = np.random.default_rng(42)
    y = (rng.random(300) < 0.16).astype(int)
    proba = np.clip(0.16 + 0.3 * y + rng.normal(0, 0.2, 300), 0, 1)
    recalls = [sensitivity.evaluate_ratio(y, proba, r)["recall"] for r in (1, 2, 3, 5, 10)]
    assert recalls == sorted(recalls)


def test_ne_signaler_personne_vaut_un():
    y = np.array([0, 1, 0, 1])
    proba = np.array([0.1, 0.2, 0.3, 0.4])
    out = sensitivity.summarize(y, proba, np.inf, 3)
    assert out["cost_vs_nobody"] == 1.0
    assert out["recall"] == 0.0


def test_resume_coherent():
    y = np.array([0, 0, 1, 1, 1])
    proba = np.array([0.2, 0.7, 0.8, 0.6, 0.1])
    out = sensitivity.summarize(y, proba, 0.5, 2)
    assert (out["fn"], out["fp"], out["flagged"]) == (1, 1, 3)
    assert out["recall"] == 2 / 3


@pytest.mark.parametrize("ratio", [0, -1, np.inf, np.nan])
def test_invalid_cost_ratios_are_rejected(ratio):
    with pytest.raises(ValueError):
        sensitivity.best_threshold(np.array([0, 1]), np.array([0.2, 0.8]), ratio)
    with pytest.raises(ValueError):
        sensitivity.summarize(np.array([0, 1]), np.array([0.2, 0.8]), 0.5, ratio)


def test_tie_break_and_explicit_no_alert_rule():
    assert sensitivity.best_threshold(np.array([0, 1]), np.array([0.5, 0.5]), 1) == 0
    y, proba = np.array([0, 0, 0, 1]), np.array([0.9, 0.8, 0.7, 0.1])
    assert sensitivity.best_threshold(y, proba, 1) == np.inf
    assert sensitivity.summarize(y, proba, np.inf, 1)["cost"] == 1


@pytest.mark.parametrize("threshold", [-0.1, 1.1, np.nan, -np.inf])
def test_invalid_thresholds_are_rejected(threshold):
    with pytest.raises(ValueError):
        sensitivity.summarize(np.array([0, 1]), np.array([0.2, 0.8]), threshold, 1)


def test_cli_exports_aggregates_without_changing_official_threshold(tmp_path, monkeypatch):
    y, proba = np.array([0, 0, 0, 1]), np.array([0.9, 0.8, 0.7, 0.1])
    monkeypatch.setattr(
        sensitivity, "evaluate_training", lambda model: ({"summary": {}}, y, proba, 0.5)
    )
    output = tmp_path / "summary.json"
    sensitivity.main(["--output", str(output)])
    result = json.loads(output.read_text())
    assert result["official_threshold_changed"] is False
    assert result["official_decision_threshold"] == 0.5
    row = next(row for row in result["sensitivity"] if row["scenario"] == "hypothetical_FN_FP_1_1")
    assert row["threshold"] is None and row["decision_rule"] == "no_alerts"
    assert {"precision", "recall", "fn", "fp", "cost"} <= row.keys()
    assert "proba" not in result and "labels" not in result
