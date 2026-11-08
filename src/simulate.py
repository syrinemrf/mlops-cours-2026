"""Fabrique des lots de test à partir des vraies données IBM HR (Lab 3).

    python -m src.simulate clean entree.csv sortie.csv     # lot sain (échantillon réel)
    python -m src.simulate corrupt entree.csv sortie.csv   # bugs de données silencieux
    python -m src.simulate drift entree.csv sortie.csv     # population déplacée

Tous les scénarios sont dans params.yaml (aucun nom de colonne dans ce code) :
- clean (simulation.sample_frac) : salariés réels tirés sans remise ; doit passer le contrat ;
- corrupt (simulation.corrupt) : unité changée (salaire mensuel -> annuel), code
  catégoriel inconnu sur une part des lignes, cible manquante sur une part des lignes ;
  doit être REFUSÉ par src/validate_data.py ;
- drift (drift.simulation) : facteurs (scale), décalages bornés au domaine (shift) et
  réaffectation d'une modalité (reassign) ; données valides mais population différente,
  que src/detect_drift.py doit signaler.
Tirages aléatoires déterministes : graine split.random_state de dataset.yaml.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.dataset_config import DatasetConfig, load_config

PARAMS = Path("params.yaml")


def load_params(path: Path = PARAMS) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def clean(cfg: DatasetConfig, df: pd.DataFrame, frac: float | None = None) -> pd.DataFrame:
    """Un lot sain : une partie des salariés réels, sans remise (identifiants uniques)."""
    frac = load_params()["simulation"]["sample_frac"] if frac is None else frac
    return df.sample(frac=frac, random_state=cfg.random_state).reset_index(drop=True)


def corrupt(cfg: DatasetConfig, df: pd.DataFrame, scenario: dict | None = None) -> pd.DataFrame:
    """Les bugs typiques d'un fournisseur de données : unité, nouveau code, trous."""
    scenario = scenario or load_params()["simulation"]["corrupt"]
    df = df.copy()
    seed = cfg.random_state
    for col, factor in (scenario.get("unit_scale") or {}).items():
        df[col] = df[col] * factor
    unknown = scenario.get("unknown_code")
    if unknown:
        rows = df.sample(frac=unknown["rate"], random_state=seed).index
        df.loc[rows, unknown["column"]] = unknown["value"]
    rate = scenario.get("missing_target_rate", 0)
    if rate:
        df.loc[df.sample(frac=rate, random_state=seed + 1).index, cfg.target] = None
    return df


def drift(df: pd.DataFrame, scenario: dict, seed: int = 42) -> pd.DataFrame:
    """Population déplacée : x facteur, + décalage borné, modalité réaffectée."""
    out = df.copy()
    for col, factor in (scenario.get("scale") or {}).items():
        out[col] = df[col] * factor
    for col, delta in (scenario.get("shift") or {}).items():
        out[col] = (out[col] + delta).clip(df[col].min(), df[col].max())
    rng = np.random.default_rng(seed)
    for col, spec in (scenario.get("reassign") or {}).items():
        mask = rng.random(len(out)) < spec["rate"]
        out.loc[mask, col] = spec["value"]
    for col in out.columns:  # les entiers restent entiers (âge, années, distance…)
        if pd.api.types.is_integer_dtype(df[col]) and not pd.api.types.is_integer_dtype(out[col]):
            out[col] = out[col].round().astype(df[col].dtype)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("kind", choices=["clean", "corrupt", "drift"])
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    cfg = load_config()
    df = pd.read_csv(args.input)
    if args.kind == "clean":
        out = clean(cfg, df)
    elif args.kind == "corrupt":
        out = corrupt(cfg, df)
    else:
        out = drift(df, load_params()["drift"]["simulation"], seed=cfg.random_state)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"{args.kind} : {len(out)} lignes -> {args.output}")


if __name__ == "__main__":
    main()
