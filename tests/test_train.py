"""Tests de l'entraînement (src/train.py) : sans serveur MLflow, sur le split réel."""

from pathlib import Path

import numpy as np
import pytest

from src import train
from src.dataset_config import load_config

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "dataset.yaml")
TRAIN = ROOT / "data" / "processed" / "train.csv"

pytestmark = pytest.mark.skipif(not TRAIN.exists(), reason="lancer python -m src.prepare")

HYPERPARAMS = {
    "logistic_regression": {"C": 1.0, "class_weight": None},
    "random_forest": {"n_estimators": 20, "max_depth": 3, "class_weight": None},
    "gradient_boosting": {"n_estimators": 20, "max_depth": 2, "learning_rate": 0.1},
    "dummy": {},
}


@pytest.fixture(scope="module")
def data():
    return CFG.read_xy(TRAIN)


def test_seuil_sans_poids_de_classes(data):
    _, y = data
    assert train.decision_threshold(CFG, None, y) == pytest.approx(CFG.cost_threshold())


def test_seuil_avec_poids_de_classes(data):
    _, y = data
    k = (y == 0).sum() / (y == 1).sum()
    balanced = train.decision_threshold(CFG, "balanced", y)
    assert balanced == pytest.approx(CFG.cost_threshold(k))
    assert balanced > train.decision_threshold(CFG, None, y)


def test_metriques_d_un_classement_parfait():
    y = np.array([0, 0, 1, 1])
    metrics = train.compute_metrics(CFG, y, np.array([0.1, 0.2, 0.8, 0.9]), 0.5)
    assert metrics["roc_auc"] == 1.0
    assert metrics["average_precision"] == 1.0
    assert metrics["business_cost"] == 0.0


@pytest.mark.parametrize("model_type", list(train.MODELS))
def test_chaque_modele_s_entraine(data, model_type):
    X, y = data
    model = train.build_model(CFG, model_type, HYPERPARAMS[model_type], 42)
    model.fit(X.iloc[:300], y.iloc[:300])
    proba = model.predict_proba(X.iloc[300:320])[:, 1]
    assert proba.shape == (20,)
    assert ((proba >= 0) & (proba <= 1)).all()


def test_validation_croisee_reproductible(data):
    X, y = data
    model = train.build_model(CFG, "logistic_regression", HYPERPARAMS["logistic_regression"], 42)
    first = train.cross_validate_ranking(model, X, y, 42)
    assert first == train.cross_validate_ranking(model, X, y, 42)
    assert set(first) == {
        "cv_roc_auc",
        "cv_roc_auc_std",
        "cv_average_precision",
        "cv_average_precision_std",
    }


def test_pretraitement_ajuste_sur_les_donnees_d_entrainement_seules(data):
    X, y = data
    model = train.build_model(CFG, "logistic_regression", HYPERPARAMS["logistic_regression"], 42)
    model.fit(X, y)
    scaler = model.named_steps["preprocess"].named_transformers_["num"].named_steps["scale"]
    assert scaler.mean_ == pytest.approx(X[CFG.numeric].mean().to_numpy())
