"""Tests de l'analyse de sensibilité (src/sensitivity.py) : sur des probabilités simulées."""

import numpy as np

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
