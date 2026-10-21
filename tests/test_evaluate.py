"""Tests de l'évaluation (src/evaluate.py) sur le modèle local et le jeu de test réels."""

import json
import shutil
from pathlib import Path

import pytest
from mlflow.models import Model

from src import evaluate
from src.dataset_config import load_config

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "dataset.yaml")
MODEL = ROOT / "models" / "model"
TEST = ROOT / "data" / "processed" / "test.csv"

pytestmark = pytest.mark.skipif(
    not (MODEL.exists() and TEST.exists()), reason="lancer dvc repro (modèle et jeu de test)"
)


@pytest.fixture
def report(tmp_path, monkeypatch):
    """Lance evaluate.main() dans un dossier isolé (copies du contrat, du test, du modèle)."""
    shutil.copy(ROOT / "dataset.yaml", tmp_path / "dataset.yaml")
    (tmp_path / "data" / "processed").mkdir(parents=True)
    shutil.copy(TEST, tmp_path / "data" / "processed" / "test.csv")
    shutil.copytree(MODEL, tmp_path / "models" / "model")
    monkeypatch.chdir(tmp_path)
    evaluate.main()
    return tmp_path / "reports" / "metrics.json"


def test_rapport_coherent(report):
    data = json.loads(report.read_text(encoding="utf-8"))
    c = data["confusion"]
    assert c["tn"] + c["fp"] + c["fn"] + c["tp"] == data["n_test"]
    expected = c["fn"] * CFG.cost_false_negative + c["fp"] * CFG.cost_false_positive
    assert data["business_cost"] == pytest.approx(expected)


def test_metrique_primaire_presente(report):
    assert CFG.primary_metric in json.loads(report.read_text(encoding="utf-8"))


def test_seuil_lu_dans_le_modele(report):
    threshold = Model.load(str(MODEL)).metadata["decision_threshold"]
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["decision_threshold"] == pytest.approx(round(threshold, 4))


def test_evaluation_reproductible(report):
    first = report.read_bytes()
    evaluate.main()
    assert report.read_bytes() == first
