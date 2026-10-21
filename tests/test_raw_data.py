"""Contrôles du jeu brut réel (data/raw/dataset.csv) : ignorés si le fichier est absent."""

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from src.dataset_config import load_config

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "dataset.yaml")
RAW = ROOT / CFG.raw_path
EXPECTED = CFG.raw["source"]["expected"]

pytestmark = pytest.mark.skipif(not RAW.exists(), reason="lancer python -m src.download")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(RAW)


def test_schema(df):
    assert list(df.columns) == CFG.columns


def test_types(df):
    numeric = [*CFG.numeric, *(s.column for s in CFG.sensitive if s.bins)]
    assert all(pd.api.types.is_numeric_dtype(df[c]) for c in numeric)
    text = [*CFG.categorical, CFG.target]
    assert all(pd.api.types.is_string_dtype(df[c]) for c in text)


def test_cible(df):
    assert df[CFG.target].nunique() == 2
    assert CFG.positive_class in set(df[CFG.target])


def test_pas_de_valeur_manquante(df):
    assert int(df.isna().sum().sum()) == EXPECTED["missing_values"]


def test_pas_de_doublon(df):
    # Mesuré après retrait de l'identifiant : un échec est un constat à documenter
    assert int(df.duplicated().sum()) == 0


def test_repartition_des_classes(df):
    assert len(df) == EXPECTED["rows"]
    positives = int((df[CFG.target] == CFG.positive_class).sum())
    assert positives == EXPECTED["positive_count"]


def test_empreinte_epinglee(df):
    pinned = CFG.raw["source"].get("sha256")
    if not pinned:
        pytest.skip("source.sha256 non épinglé")
    assert hashlib.sha256(RAW.read_bytes()).hexdigest() == pinned
