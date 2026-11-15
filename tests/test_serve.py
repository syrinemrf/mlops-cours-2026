"""API de scoring (packaging/app/serve.py, Lab 4) : contrat d'entrée et parité avec ONNX."""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.dataset_config import load_config

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "packaging" / "model" / "model.onnx"
TEST_CSV = ROOT / "data" / "processed" / "test.csv"
CFG = load_config(ROOT / "dataset.yaml")

pytestmark = pytest.mark.skipif(
    not (MODEL.exists() and TEST_CSV.exists()),
    reason="modèle ONNX absent : python packaging/app/export_onnx.py",
)


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    sys.path.insert(0, str(ROOT / "packaging"))
    from app.serve import app

    return TestClient(app)


def rows(n: int) -> list[dict]:
    df = pd.read_csv(TEST_CSV)[CFG.features].head(n)
    return df.astype(object).where(df.notna(), None).to_dict("records")


def test_health_and_metadata(client):
    assert client.get("/health").json()["status"] == "ok"
    meta = client.get("/metadata").json()
    exported = json.loads(MODEL.with_name("metadata.json").read_text())
    assert meta["model"]["model_version"] == exported["model_version"]
    assert meta["threshold"] == pytest.approx(exported["threshold"])


def test_predict_batch(client):
    resp = client.post("/predict", json={"instances": rows(3)})
    assert resp.status_code == 200
    preds = resp.json()["predictions"]
    assert len(preds) == 3
    for p in preds:
        assert 0.0 <= p["probability"] <= 1.0
        assert p["prediction"] == int(p["probability"] >= resp.json()["threshold"])


def test_missing_column_is_422(client):
    row = rows(1)[0]
    row.pop(CFG.numeric[0])
    assert client.post("/predict", json={"instances": [row]}).status_code == 422


def test_wrong_types_are_422(client):
    row = rows(1)[0]
    row[CFG.numeric[0]] = "12"  # chaîne pour une numérique
    assert client.post("/predict", json={"instances": [row]}).status_code == 422
    row = rows(1)[0]
    row[CFG.categorical[0]] = 3  # nombre pour une catégorielle
    assert client.post("/predict", json={"instances": [row]}).status_code == 422


def test_unknown_column_is_422(client):
    row = rows(1)[0] | {"colonne_inconnue": 1.0}
    assert client.post("/predict", json={"instances": [row]}).status_code == 422


def test_null_is_imputed(client):
    row = rows(1)[0] | {CFG.numeric[0]: None, CFG.categorical[0]: None}
    assert client.post("/predict", json={"instances": [row]}).status_code == 200


def test_version_defaults_to_lab4_image(client):
    """Sans APP_VERSION (image 1.0.0 du Lab 4, tests locaux) : version 1.0.0."""
    exported = json.loads(MODEL.with_name("metadata.json").read_text())
    body = client.get("/version").json()
    assert body == {"version": "1.0.0", "model_version": exported["model_version"]}
    assert client.get("/metadata").json()["api_version"] == "1.0.0"


def test_version_reads_app_version(monkeypatch):
    """APP_VERSION (posée par ENV dans l'image) est la version servie par /version."""
    import importlib

    from fastapi.testclient import TestClient

    sys.path.insert(0, str(ROOT / "packaging"))
    import app.serve as serve

    monkeypatch.setenv("APP_VERSION", "2.0.0")
    try:
        reloaded = importlib.reload(serve)
        assert TestClient(reloaded.app).get("/version").json()["version"] == "2.0.0"
    finally:
        monkeypatch.delenv("APP_VERSION")
        importlib.reload(serve)
