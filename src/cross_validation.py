"""Train-only ranking CV extracted from MohamedAzizKouch's M1 contribution.

Source: 7f9d1ede88f277f6bdcb513c5db4f28c3b4bd59d, src/train.py:125-133.
The original helper is extracted without changing the official training module.
"""

import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

CV_FOLDS = 5
CV_METRICS = ("roc_auc", "average_precision")


def cross_validate_ranking(model: Pipeline, X: pd.DataFrame, y: pd.Series, seed: int) -> dict:
    """Validation croisée stratifiée sur le TRAIN : le prétraitement est réajusté à chaque pli."""
    folds = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=seed)
    out = {}
    for metric in CV_METRICS:
        scores = cross_val_score(model, X, y, cv=folds, scoring=metric)
        out[f"cv_{metric}"] = float(scores.mean())
        out[f"cv_{metric}_std"] = float(scores.std())
    return out
