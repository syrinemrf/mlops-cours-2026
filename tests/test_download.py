"""Tests de l'ingestion (src/download.py) : hors ligne, sans Kaggle ni OpenML."""

import hashlib
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src import download
from src.dataset_config import load_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cfg():
    return load_config(ROOT / "dataset.yaml")


def synthetic_raw(cfg, *, as_float=False, bom=False) -> pd.DataFrame:
    """Jeu brut synthétique respectant les repères de dataset.yaml (source.expected)."""
    expected = cfg.raw["source"]["expected"]
    n, n_pos = expected["rows"], expected["positive_count"]
    numeric = set(cfg.numeric) | {s.column for s in cfg.sensitive if s.bins}
    data = {}
    for i, col in enumerate(cfg.columns):
        if col == cfg.target:
            data[col] = [str(cfg.positive_class)] * n_pos + ["No"] * (n - n_pos)
        elif col in numeric:
            data[col] = [18 + (r + i) % 7 for r in range(n)]
        else:
            data[col] = [f"v{(r + i) % 3}" for r in range(n)]
    for col in expected["constant_columns"]:
        data[col] = [1] * n
    for col in expected["identifier_columns"]:
        data[col] = list(range(1, n + 1))
    df = pd.DataFrame(data)
    if as_float:
        df[sorted(numeric)] = df[sorted(numeric)].astype("float64")
    if bom:
        df = df.rename(columns={df.columns[0]: "\ufeff" + df.columns[0]})
    return df


def test_contrat_hr(cfg):
    assert isinstance(cfg.positive_class, str)
    assert cfg.positive_class == "Yes"  # guillemets obligatoires dans le YAML
    assert set(cfg.extra_sensitive) == {"Age", "Gender", "MaritalStatus"}
    excluded = set(cfg.raw["excluded_columns"])
    assert excluded.isdisjoint(cfg.columns)
    assert len(cfg.columns) + len(excluded) == cfg.raw["source"]["expected"]["raw_columns"]


def test_references_conformes(cfg):
    assert download.check_reference(synthetic_raw(cfg), cfg) == []


def test_ligne_manquante_detectee(cfg):
    problems = download.check_reference(synthetic_raw(cfg).iloc[1:], cfg)
    assert any(p.startswith("rows") for p in problems)


def test_doublon_detecte(cfg):
    raw = synthetic_raw(cfg)
    raw.iloc[1] = raw.iloc[0]
    problems = download.check_reference(raw, cfg)
    assert any(p.startswith("duplicate_rows") for p in problems)


def test_valeur_manquante_detectee(cfg):
    raw = synthetic_raw(cfg)
    raw.loc[0, cfg.numeric[0]] = None
    problems = download.check_reference(raw, cfg)
    assert any(p.startswith("missing_values") for p in problems)


def test_sources_equivalentes(cfg):
    """Même contenu, mises en forme différentes (BOM, entiers en float) : mêmes octets."""
    a = download.to_clean_frame(synthetic_raw(cfg), cfg)
    b = download.to_clean_frame(synthetic_raw(cfg, as_float=True, bom=True), cfg)
    assert download.csv_bytes(a) == download.csv_bytes(b)
    assert list(a.columns) == cfg.columns
    assert set(cfg.raw["excluded_columns"]).isdisjoint(a.columns)


def test_from_file_lit_le_bom(cfg, tmp_path):
    path = tmp_path / "kaggle.csv"
    raw = synthetic_raw(cfg)
    raw.to_csv(path, index=False, encoding="utf-8-sig")
    cols = download.clean_columns(download.from_file(str(path))).columns
    assert list(cols) == list(raw.columns)


@pytest.fixture
def workdir(tmp_path, monkeypatch, cfg):
    """Dossier isolé : dataset.yaml sans empreinte épinglée, source réseau simulée."""
    data = yaml.safe_load((ROOT / "dataset.yaml").read_text(encoding="utf-8"))
    data["source"]["sha256"] = None
    text = yaml.safe_dump(data, allow_unicode=True)
    (tmp_path / "dataset.yaml").write_text(text, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(download, "from_openml", lambda: synthetic_raw(cfg))
    return tmp_path


def test_telechargement_reproductible(workdir, capsys):
    assert download.main([]) == 0
    first = (workdir / "data/raw/dataset.csv").read_bytes()
    assert download.main([]) == 0
    assert (workdir / "data/raw/dataset.csv").read_bytes() == first
    assert hashlib.sha256(first).hexdigest() in capsys.readouterr().out


def test_empreinte_epinglee_refuse_un_ecart(workdir):
    path = workdir / "dataset.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["source"]["sha256"] = "0" * 64
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    assert download.main([]) == 1
    assert not (workdir / "data/raw/dataset.csv").exists()
