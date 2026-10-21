"""Tests du feature store Feast : définitions (sans store) et cohérence en ligne / train."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest
import yaml
from feast import FeatureStore

from src.dataset_config import load_config

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "dataset.yaml")
ID = yaml.safe_load((ROOT / "params.yaml").read_text(encoding="utf-8"))["prepare"]["id_column"]
TRAIN = ROOT / "data" / "processed" / "train.csv"
STORE_FILES = [ROOT / "features/data/registry.db", ROOT / "features/data/online_store.db"]


@pytest.fixture(scope="module")
def definitions():
    path = ROOT / "features" / "definitions.py"
    spec = importlib.util.spec_from_file_location("feast_definitions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vue_construite_depuis_dataset_yaml(definitions):
    view = definitions.request_features
    assert view.name == "request_features"
    assert {f.name for f in view.schema} == set(CFG.features)


def test_ni_cible_ni_attribut_sensible_dans_le_store(definitions):
    names = {f.name for f in definitions.request_features.schema}
    assert CFG.target not in names
    assert set(CFG.extra_sensitive).isdisjoint(names)


def test_entite_et_service(definitions):
    assert definitions.request.join_key == ID
    assert definitions.scoring_v1.name == "scoring_v1"


@pytest.mark.skipif(
    not (TRAIN.exists() and all(p.exists() for p in STORE_FILES)),
    reason="lancer feast apply puis feast materialize-incremental",
)
def test_en_ligne_identique_a_l_entrainement():
    store = FeatureStore(repo_path=str(ROOT / "features"))
    sample = pd.read_csv(TRAIN).head(25)
    rows = [{ID: int(i)} for i in sample[ID]]
    online = store.get_online_features(
        features=store.get_feature_service("scoring_v1"), entity_rows=rows
    ).to_dict()
    for col in CFG.features:
        expected = sample[col].astype("float64") if col in CFG.numeric else sample[col]
        assert list(online[col]) == list(expected), col
