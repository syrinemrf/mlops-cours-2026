"""Analyse de sensibilité du seuil de décision au rapport de coûts (scénarios HYPOTHÉTIQUES).

Le dataset ne fournit aucune matrice de coûts : dataset.yaml garde 1 / 1. Ce script montre,
sur les probabilités hors-pli du TRAIN (validation croisée, jamais le test), quel seuil et
quel rappel donneraient différents rapports « coût d'un départ raté / coût d'une alerte
inutile ». Ce sont des scénarios, pas des coûts réels : le choix d'un rapport appartient au
métier. Aucun artefact n'est écrit ; le résultat s'affiche.

Usage ::  python -m src.sensitivity
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from src.dataset_config import load_config
from src.train import CV_FOLDS, MODELS, TRAIN_CSV, build_model, decision_threshold, none_or

RATIOS = (1, 2, 3, 5, 10)
CASTS = {
    "C": float,
    "class_weight": none_or(str),
    "n_estimators": int,
    "max_depth": none_or(int),
    "learning_rate": float,
}


def summarize(y: np.ndarray, proba: np.ndarray, threshold: float, ratio: float) -> dict:
    """Rappel, précision et coût (ratio x faux négatifs + faux positifs) à un seuil donné."""
    flagged = proba >= threshold
    positives = int((y == 1).sum())
    tp = int(((y == 1) & flagged).sum())
    fn = positives - tp
    fp = int(((y == 0) & flagged).sum())
    cost = ratio * fn + fp
    return {
        "ratio": ratio,
        "threshold": threshold,
        "recall": tp / positives,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "fn": fn,
        "fp": fp,
        "flagged": int(flagged.sum()),
        "cost_vs_nobody": cost / (ratio * positives),  # 1,0 = ne signaler personne
    }


def best_threshold(y: np.ndarray, proba: np.ndarray, ratio: float) -> float:
    """Seuil qui minimise ratio x FN + FP sur les probabilités fournies (ex æquo : le plus bas)."""
    candidates = np.unique(np.concatenate([proba, [0.0, np.inf]]))
    costs = []
    for threshold in candidates:
        flagged = proba >= threshold
        fn = int(((y == 1) & ~flagged).sum())
        fp = int(((y == 0) & flagged).sum())
        costs.append(ratio * fn + fp)
    return float(candidates[int(np.argmin(costs))])


def evaluate_ratio(y: np.ndarray, proba: np.ndarray, ratio: float) -> dict:
    return summarize(y, proba, best_threshold(y, proba, ratio), ratio)


def main() -> None:
    cfg = load_config()
    params = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))["train"]
    model_type = params["model"]
    hyperparams = {name: CASTS[name](params[name]) for name in MODELS[model_type][1]}
    seed = params["random_state"]

    X, y = cfg.read_xy(TRAIN_CSV)
    model = build_model(cfg, model_type, hyperparams, seed)
    folds = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=seed)
    proba = cross_val_predict(model, X, y, cv=folds, method="predict_proba")[:, 1]

    y_arr = y.to_numpy()
    current = decision_threshold(cfg, hyperparams.get("class_weight"), y)
    rows = [{"scénario": "seuil actuel (coûts 1/1)", **summarize(y_arr, proba, current, 1)}]
    rows += [{"scénario": f"coût FN = {r} x FP", **evaluate_ratio(y_arr, proba, r)} for r in RATIOS]
    table = pd.DataFrame(rows).drop(columns="ratio").round(3)
    print(f"Modèle : {model_type} {hyperparams} · {len(y_arr)} lignes du train, hors-pli")
    print("Scénarios HYPOTHÉTIQUES : aucun coût réel n'est connu.\n")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
