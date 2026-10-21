"""Télécharge le jeu de données brut décrit par dataset.yaml (IBM HR Attrition).

Source automatique : OpenML (data_id 43696), copie publique, sans compte, du jeu Kaggle
« IBM HR Analytics Employee Attrition & Performance ». Source de référence : le CSV
officiel de Kaggle (compte requis, téléchargement manuel), utilisable avec --from-file.

Usage ::

    python -m src.download                          # OpenML, sans identifiants
    python -m src.download --from-file WA_Fn-UseC_-HR-Employee-Attrition.csv

Sortie : data/raw/dataset.csv (raw_path de dataset.yaml) : seulement les colonnes déclarées
dans dataset.yaml, dans cet ordre, avec une mise en forme déterministe. Le SHA-256 est
comparé à source.sha256 s'il est renseigné. Aucun identifiant n'est lu ni stocké.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd

from src.dataset_config import DatasetConfig, load_config

OPENML_DATA_ID = 43696  # miroir OpenML du jeu Kaggle (accès public)


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Retire le BOM éventuel et les espaces des noms de colonnes."""
    out = df.copy()
    out.columns = [str(c).replace("\ufeff", "").replace("ï»¿", "").strip() for c in out.columns]
    return out


def check_reference(raw: pd.DataFrame, cfg: DatasetConfig) -> list[str]:
    """Écarts entre les données brutes et les repères de dataset.yaml (source.expected)."""
    expected = (cfg.raw.get("source") or {}).get("expected") or {}
    positives = raw[cfg.target].astype(str).str.strip() == str(cfg.positive_class)
    measured = {
        "rows": len(raw),
        "raw_columns": raw.shape[1],
        "positive_count": int(positives.sum()),
        "missing_values": int(raw.isna().sum().sum()),
        "duplicate_rows": int(raw.duplicated().sum()),
    }
    problems = [
        f"{key} : {measured[key]} mesuré, {value} attendu"
        for key, value in expected.items()
        if key in measured and measured[key] != value
    ]
    for col in expected.get("constant_columns", []):
        if col not in raw.columns or raw[col].nunique() != 1:
            problems.append(f"{col} devrait être constante")
    for col in expected.get("identifier_columns", []):
        if col not in raw.columns or not raw[col].is_unique:
            problems.append(f"{col} devrait être un identifiant unique")
    return problems


def to_clean_frame(raw: pd.DataFrame, cfg: DatasetConfig) -> pd.DataFrame:
    """Colonnes déclarées uniquement, dans l'ordre de dataset.yaml, types déterministes."""
    raw = clean_columns(raw)
    cfg.validate_columns(raw)
    df = raw[cfg.columns].copy()
    numeric = set(cfg.numeric) | {s.column for s in cfg.sensitive if s.bins}
    for col in df.columns:
        if col in numeric:
            values = pd.to_numeric(df[col])
            if values.notna().all() and (values % 1 == 0).all():
                values = values.astype("int64")  # 41.0 et 41 donnent le même CSV
            df[col] = values
        else:
            df[col] = df[col].astype(str).str.strip()
    return df.reset_index(drop=True)


def csv_bytes(df: pd.DataFrame) -> bytes:
    """CSV déterministe (UTF-8, fins de ligne \\n, sans index)."""
    return df.to_csv(index=False, lineterminator="\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def from_openml() -> pd.DataFrame:
    from sklearn.datasets import fetch_openml

    return fetch_openml(data_id=OPENML_DATA_ID, as_frame=True, n_retries=3, delay=2.0).frame


def from_file(path: str) -> pd.DataFrame:
    """Lit le CSV officiel de Kaggle (UTF-8 avec BOM possible)."""
    return pd.read_csv(path, encoding="utf-8-sig")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-file", help="CSV Kaggle téléchargé à la main (compte requis)")
    args = parser.parse_args(argv)

    cfg = load_config()
    if args.from_file:
        raw, origin = from_file(args.from_file), args.from_file
    else:
        raw, origin = from_openml(), "OpenML"

    raw = clean_columns(raw)
    cfg.validate_columns(raw)
    problems = check_reference(raw, cfg)
    if problems:
        print("Données brutes non conformes aux repères de dataset.yaml :", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    df = to_clean_frame(raw, cfg)
    payload = csv_bytes(df)
    digest = sha256_hex(payload)
    pinned = (cfg.raw.get("source") or {}).get("sha256")
    if pinned and pinned != digest:
        print(f"SHA-256 inattendu : {digest} (épinglé : {pinned}).", file=sys.stderr)
        return 1

    out = Path(cfg.raw_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    share = (df[cfg.target] == str(cfg.positive_class)).mean()
    print(f"{len(df)} lignes ({origin}) -> {out} · classe '{cfg.positive_class}' : {share:.1%}")
    print(f"sha256 : {digest}")
    if not pinned:
        print(
            "sha256 non épinglé : après comparaison avec le CSV Kaggle (--from-file), "
            "ajoutez-le sous `source` dans dataset.yaml.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
