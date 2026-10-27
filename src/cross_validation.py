"""Train-only CV/OOF diagnostics derived from MohamedAzizKouch's M1 helper.

Source: 7f9d1ede88f277f6bdcb513c5db4f28c3b4bd59d, src/train.py:125-133.
Integration computes both ranking metrics and OOF probabilities in five sequential
fits. This module never reads the test set, saves a model or contacts MLflow.
"""

import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from src.dataset_config import load_config
from src.train import MODELS, TRAIN_CSV, build_model, decision_threshold, parse_args

CV_FOLDS = 5
CV_METRICS = ("roc_auc", "average_precision")


def validate_predictions(y, proba):
    """Require aligned binary labels and finite positive-class probabilities."""
    y, proba = np.asarray(y), np.asarray(proba, dtype=float)
    if y.ndim != 1 or proba.ndim != 1 or len(y) != len(proba) or not len(y):
        raise ValueError("Expected nonempty aligned one-dimensional labels/probabilities")
    if not np.isin(y, [0, 1]).all() or np.unique(y).size != 2:
        raise ValueError("Both binary classes 0 and 1 are required")
    if not np.isfinite(proba).all() or ((proba < 0) | (proba > 1)).any():
        raise ValueError("Probabilities must be finite and between zero and one")
    return y, proba


def cross_validate_oof(model: Pipeline, X: pd.DataFrame, y, seed: int):
    """Clone/refit the full preprocessing pipeline separately in every train fold."""
    y, _ = validate_predictions(y, np.zeros(len(y)))
    if not isinstance(X, pd.DataFrame) or len(X) != len(y):
        raise ValueError("Expected a DataFrame aligned positionally with labels")
    if min(np.bincount(y.astype(int))) < CV_FOLDS:
        raise ValueError("Each class needs at least five training examples")
    folds = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=seed)
    proba = np.full(len(y), np.nan)
    seen = np.zeros(len(y), dtype=int)
    fold_scores, identities = [], []
    with threadpool_limits(limits=1):
        for fold, (training, validation) in enumerate(folds.split(X, y), 1):
            fitted = clone(model)
            params = fitted.get_params()
            jobs = {}
            for key in params:
                if key == "n_jobs" or key.endswith("__n_jobs"):
                    owner = params.get(key.rsplit("__", 1)[0]) if "__" in key else fitted
                    # LR n_jobs is deprecated/no-op; BLAS is already limited above.
                    if not isinstance(owner, LogisticRegression):
                        jobs[key] = 1
            fitted.set_params(**jobs)
            fitted.fit(X.iloc[training], y[training])
            positive = list(fitted.classes_).index(1)
            predictions = fitted.predict_proba(X.iloc[validation])[:, positive]
            validate_predictions(y[validation], predictions)
            proba[validation] = predictions
            seen[validation] += 1
            fold_scores.append(
                {
                    "fold": fold,
                    "train_rows": len(training),
                    "validation_rows": len(validation),
                    "validation_positives": int(y[validation].sum()),
                    "roc_auc": float(roc_auc_score(y[validation], predictions)),
                    "average_precision": float(average_precision_score(y[validation], predictions)),
                }
            )
            identities.append({"train": training.tolist(), "validation": validation.tolist()})
            del fitted
    if not np.all(seen == 1):
        raise ValueError("Every training row must receive exactly one out-of-fold prediction")
    validate_predictions(y, proba)
    summary = {}
    for metric in CV_METRICS:
        scores = np.array([row[metric] for row in fold_scores])
        if not np.isfinite(scores).all():
            raise ValueError("Nonfinite fold score")
        summary[f"cv_{metric}"] = float(scores.mean())
        summary[f"cv_{metric}_std"] = float(scores.std(ddof=0))
    return {
        "summary": summary,
        "folds": fold_scores,
        "cv_folds": CV_FOLDS,
        "fold_assignments_sha256": hashlib.sha256(
            json.dumps(identities, sort_keys=True).encode()
        ).hexdigest(),
        "std_definition": "population standard deviation of five fold scores (ddof=0), not a CI",
        "oof_rows": len(y),
        "oof_predictions_per_row": 1,
        "fits": CV_FOLDS,
        "n_jobs": 1,
        "blas_threads": 1,
    }, proba


def cross_validate_ranking(model: Pipeline, X: pd.DataFrame, y: pd.Series, seed: int) -> dict:
    """Preserve the original helper's four-metric interface."""
    return cross_validate_oof(model, X, y, seed)[0]["summary"]


def evaluate_training(model_type=None):
    """Read only TRAIN_CSV; return aggregates and temporary in-memory OOF values."""
    cfg = load_config()
    args = parse_args([])
    name = model_type or args.model
    if name not in MODELS:
        raise ValueError("Unsupported diagnostic model")
    hyperparams = {key: getattr(args, key) for key in MODELS[name][1]}
    X, y = cfg.read_xy(TRAIN_CSV)
    model = build_model(cfg, name, hyperparams, args.random_state)
    report, proba = cross_validate_oof(model, X, y, args.random_state)
    report.update(
        {
            "protocol": "A",
            "evaluation_role": "train_cv_diagnostic",
            "promotion_eligible": False,
            "dataset": cfg.name,
            "model": name,
            "hyperparameters": hyperparams,
            "random_state": args.random_state,
            "train_sha256": hashlib.sha256(TRAIN_CSV.read_bytes()).hexdigest(),
            "contract_sha256": hashlib.sha256(Path("dataset.yaml").read_bytes()).hexdigest(),
            "params_sha256": hashlib.sha256(Path("params.yaml").read_bytes()).hexdigest(),
            "packages": {p: version(p) for p in ("scikit-learn", "numpy", "pandas")},
            "predictors": cfg.features,
            "sensitive_and_identifier_used_as_predictors": False,
            "test_used": False,
            "official_model_modified": False,
            "selection_limitation": "CV used for selection is not an independent final estimate",
        }
    )
    threshold = decision_threshold(cfg, hyperparams.get("class_weight"), y)
    return report, y.to_numpy(), proba, threshold


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", choices=list(MODELS))
    parser.add_argument(
        "--output", type=Path, default=Path("reports/m1/integration/cross-validation.json")
    )
    args = parser.parse_args(argv)
    report, _, _, _ = evaluate_training(args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
