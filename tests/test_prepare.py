"""Tests de la préparation (src/prepare.py) sur une copie du jeu brut réel."""

import math
import shutil
from pathlib import Path

import pandas as pd
import pytest

from src import prepare
from src.dataset_config import load_config

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "dataset.yaml")
RAW = ROOT / CFG.raw_path

pytestmark = pytest.mark.skipif(not RAW.exists(), reason="lancer python -m src.download")


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    """Lance prepare.main() dans un dossier isolé (copies de dataset.yaml, params.yaml, brut)."""
    for name in ("dataset.yaml", "params.yaml"):
        shutil.copy(ROOT / name, tmp_path / name)
    raw = tmp_path / CFG.raw_path
    raw.parent.mkdir(parents=True)
    shutil.copy(RAW, raw)
    monkeypatch.chdir(tmp_path)
    prepare.main()
    return tmp_path / "data" / "processed"


def test_taille_du_split(prepared):
    train, test = pd.read_csv(prepared / "train.csv"), pd.read_csv(prepared / "test.csv")
    n = len(pd.read_csv(RAW))
    assert len(test) == math.ceil(n * CFG.test_size)
    assert len(train) + len(test) == n


def test_pas_de_fuite_entre_train_et_test(prepared):
    train, test = pd.read_csv(prepared / "train.csv"), pd.read_csv(prepared / "test.csv")
    assert set(train["request_id"]).isdisjoint(test["request_id"])
    assert sorted([*train["request_id"], *test["request_id"]]) == list(
        range(1, len(train) + len(test) + 1)
    )


def test_stratification(prepared):
    train, test = pd.read_csv(prepared / "train.csv"), pd.read_csv(prepared / "test.csv")
    overall = CFG.encode_target(pd.read_csv(RAW)[CFG.target]).mean()
    for part in (train, test):
        assert abs(CFG.encode_target(part[CFG.target]).mean() - overall) < 0.01


def test_split_reproductible(prepared):
    first = {f: (prepared / f).read_bytes() for f in ("train.csv", "test.csv", "features.parquet")}
    prepare.main()
    assert {f: (prepared / f).read_bytes() for f in first} == first


def test_source_feast_sans_cible_ni_sensibles(prepared):
    feats = pd.read_parquet(prepared / "features.parquet")
    assert list(feats.columns) == ["request_id", *CFG.features, "event_timestamp"]
    assert CFG.target not in feats.columns
    assert set(CFG.extra_sensitive).isdisjoint(feats.columns)
    assert all(feats[c].dtype == "float64" for c in CFG.numeric)
    assert feats["event_timestamp"].nunique() == 1


def test_le_modele_ne_voit_ni_la_cible_ni_les_sensibles(prepared):
    train = pd.read_csv(prepared / "train.csv")
    X, y = CFG.split_xy(train)
    assert list(X.columns) == CFG.features
    assert set(y) == {0, 1}
