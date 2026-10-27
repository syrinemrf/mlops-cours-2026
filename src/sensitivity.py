"""Analyse de sensibilité du seuil de décision au rapport de coûts (scénarios HYPOTHÉTIQUES).

Le dataset ne fournit aucune matrice de coûts : dataset.yaml garde 1 / 1. Ce script montre,
sur les probabilités hors-pli du TRAIN (validation croisée, jamais le test), quel seuil et
quel rappel donneraient différents rapports « coût d'un départ raté / coût d'une alerte
inutile ». Ce sont des scénarios, pas des coûts réels : le choix d'un rapport appartient au
métier. Seuls les agrégats sont exportés ; aucune prédiction individuelle n’est publiée.

Le seuil optimisé et son coût utilisent les mêmes OOF : ce coût est optimiste,
pas une estimation finale indépendante. Le seuil du modèle officiel reste inchangé.

Usage ::  python -m src.sensitivity
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.cross_validation import evaluate_training, validate_predictions
from src.train import MODELS

RATIOS = (1, 2, 3, 5, 10)


def summarize(y: np.ndarray, proba: np.ndarray, threshold: float, ratio: float) -> dict:
    """Rappel, précision et coût (ratio x faux négatifs + faux positifs) à un seuil donné."""
    y, proba = validate_predictions(y, proba)
    if not np.isfinite(ratio) or ratio <= 0:
        raise ValueError("Cost ratio must be finite and strictly positive")
    if not (threshold == np.inf or np.isfinite(threshold) and 0 <= threshold <= 1):
        raise ValueError("Threshold must be in [0,1], or positive infinity for no alerts")
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
        "cost": float(cost),
        "cost_vs_nobody": cost / (ratio * positives),  # 1,0 = ne signaler personne
    }


def best_threshold(y: np.ndarray, proba: np.ndarray, ratio: float) -> float:
    """Seuil qui minimise ratio x FN + FP sur les probabilités fournies (ex æquo : le plus bas)."""
    y, proba = validate_predictions(y, proba)
    if not np.isfinite(ratio) or ratio <= 0:
        raise ValueError("Cost ratio must be finite and strictly positive")
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


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", choices=list(MODELS))
    parser.add_argument(
        "--output", type=Path, default=Path("reports/m1/integration/train-diagnostics.json")
    )
    args = parser.parse_args(argv)
    report, y_arr, proba, current = evaluate_training(args.model)
    rows = [{"scenario": "official_threshold_FN_FP_1_1", **summarize(y_arr, proba, current, 1)}]
    rows += [
        {"scenario": f"hypothetical_FN_FP_{r}_1", **evaluate_ratio(y_arr, proba, r)} for r in RATIOS
    ]
    for row in rows:
        if np.isinf(row["threshold"]):
            row["threshold"] = None
            row["decision_rule"] = "no_alerts"
    report.update(
        {
            "official_decision_threshold": current,
            "sensitivity": rows,
            "cost_assumption": "experimental scenarios, not established economic HR costs",
            "threshold_selection_bias": "Optimized and evaluated on the same OOF: optimistic cost",
            "official_threshold_changed": False,
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report["summary"], indent=2))
    print("Scénarios HYPOTHÉTIQUES : coûts optimistes sur les mêmes OOF, aucun seuil promu.")
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
