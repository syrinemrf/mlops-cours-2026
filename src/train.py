"""Entraîne un modèle de classification et trace le run dans MLflow (expérience « scoring »).

Hyper-paramètres par défaut : params.yaml (section train) ; les options de la ligne de
commande les surchargent (utilisé par src/grid_search.py). Le modèle enregistré est un
Pipeline scikit-learn complet (prétraitement décrit par dataset.yaml + estimateur) : il
prend en entrée les colonnes brutes, et son prétraitement est ajusté sur le train seul.

Sélection et test : les métriques `cv_*` (validation croisée stratifiée sur le train) servent
à CHOISIR le modèle ; les métriques de test (roc_auc, average_precision...) servent au contrôle
officiel et au rapport. Choisir sur le seul test biaiserait l'estimation (petit test).

Les métriques de décision (F1, précision, rappel, coût métier) sont calculées au seuil
`decision_threshold` (cfg.cost_threshold), loggé en paramètre et rangé dans les métadonnées
du modèle.

Sorties : un run MLflow (params, métriques, tags, modèle) et une copie locale du modèle
au format MLflow dans models/model/ (sortie DVC, relue par src/evaluate.py).
"""

import argparse
import hashlib
import os
import shutil
from importlib.metadata import version
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
import yaml
from mlflow.models import infer_signature
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from src.dataset_config import DatasetConfig, load_config

EXPERIMENT = "scoring"
TRAIN_CSV = Path("data/processed/train.csv")
TEST_CSV = Path("data/processed/test.csv")
MODEL_DIR = Path("models/model")
CV_FOLDS = 5
CV_METRICS = ("roc_auc", "average_precision")  # métriques de classement, sans seuil

# Type de modèle -> (classe scikit-learn, hyper-paramètres pris dans params.yaml / la CLI)
MODELS = {
    "logistic_regression": (LogisticRegression, ["C", "class_weight"]),
    "random_forest": (RandomForestClassifier, ["n_estimators", "max_depth", "class_weight"]),
    "gradient_boosting": (
        GradientBoostingClassifier,
        ["n_estimators", "max_depth", "learning_rate"],
    ),
    "dummy": (DummyClassifier, []),  # référence naïve : probabilité = taux de la classe
}
# MLflow 3 sérialise en skops (pas en pickle) : seuls les types déclarés « de confiance »
# peuvent être rechargés.
SKOPS_TRUSTED_TYPES = ["numpy.dtype", "sklearn.tree._tree.Tree"]
# Dépendances nécessaires pour recharger le modèle (images de serving des labs 4-5).
PIP_REQUIREMENTS = [f"{p}=={version(p)}" for p in ("scikit-learn", "skops", "pandas", "numpy")]


def none_or(cast):
    """Convertisseur argparse acceptant « none » (ex. --max_depth none)."""
    return lambda value: None if str(value).lower() == "none" else cast(value)


def parse_args() -> argparse.Namespace:
    defaults = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))["train"]
    parser = argparse.ArgumentParser(description="Entraîne un modèle et le trace dans MLflow")
    parser.add_argument("--model", choices=list(MODELS), default=defaults["model"])
    parser.add_argument("--C", type=float, default=defaults["C"])
    parser.add_argument("--class_weight", type=none_or(str), default=defaults["class_weight"])
    parser.add_argument("--n_estimators", type=int, default=defaults["n_estimators"])
    parser.add_argument("--max_depth", type=none_or(int), default=defaults["max_depth"])
    parser.add_argument("--learning_rate", type=float, default=defaults["learning_rate"])
    parser.add_argument("--random_state", type=int, default=defaults["random_state"])
    return parser.parse_args()


def build_model(cfg: DatasetConfig, model_type: str, hyperparams: dict, seed: int) -> Pipeline:
    """Pipeline complet : prétraitement de dataset.yaml + estimateur."""
    cls, _ = MODELS[model_type]
    extra = {"random_state": seed} if model_type != "dummy" else {"strategy": "prior"}
    if model_type == "logistic_regression":
        extra["max_iter"] = 1000
    return Pipeline(
        [("preprocess", cfg.build_preprocessor()), ("model", cls(**hyperparams, **extra))]
    )


def decision_threshold(cfg: DatasetConfig, class_weight, y_train: pd.Series) -> float:
    """Seuil qui minimise le coût métier de dataset.yaml (et non 0,5).

    class_weight="balanced" donne aux positifs un poids n_neg/n_pos fois plus grand :
    les probabilités du modèle sont gonflées d'autant, le seuil remonte en conséquence.
    """
    k = (y_train == 0).sum() / (y_train == 1).sum() if class_weight == "balanced" else 1.0
    return cfg.cost_threshold(float(k))


def compute_metrics(cfg: DatasetConfig, y_true, proba, threshold: float) -> dict:
    """Métriques de classement (proba) et de décision au seuil donné, dont le coût métier."""
    y_pred = (np.asarray(proba) >= threshold).astype(int)
    return {
        "roc_auc": roc_auc_score(y_true, proba),
        "average_precision": average_precision_score(y_true, proba),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "business_cost": cfg.business_cost(y_true, y_pred),
    }


def cross_validate_ranking(model: Pipeline, X: pd.DataFrame, y: pd.Series, seed: int) -> dict:
    """Validation croisée stratifiée sur le TRAIN : le prétraitement est réajusté à chaque pli."""
    folds = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=seed)
    out = {}
    for metric in CV_METRICS:
        scores = cross_val_score(model, X, y, cv=folds, scoring=metric)
        out[f"cv_{metric}"] = float(scores.mean())
        out[f"cv_{metric}_std"] = float(scores.std())
    return out


def file_md5(path: str | Path) -> str:
    """Empreinte MD5 du fichier brut : la même que celle que DVC écrit dans dvc.lock."""
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    cfg = load_config()
    # Numériques en float64 : la signature MLflow les déclare `double` (cfg.read_xy)
    X_train, y_train = cfg.read_xy(TRAIN_CSV)
    X_test, y_test = cfg.read_xy(TEST_CSV)

    hyperparams = {name: getattr(args, name) for name in MODELS[args.model][1]}
    threshold = decision_threshold(cfg, hyperparams.get("class_weight"), y_train)
    run_name = "-".join([args.model, *(f"{k}={v}" for k, v in hyperparams.items())])
    # Qui a lancé le run ? DVC définit DVC_STAGE ; grid_search.py définit LAUNCHED_BY.
    launched_by = "dvc" if os.getenv("DVC_STAGE") else os.getenv("LAUNCHED_BY", "manual")

    # Serveur MLflow du cours (MLFLOW_TRACKING_URI dans .env) : aucun identifiant S3 ici,
    # le serveur fait proxy des artefacts vers s3://mlflow-artifacts.
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(EXPERIMENT)

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(
            {
                "model_type": args.model,
                "dataset": cfg.name,
                "data_md5": file_md5(cfg.raw_path),
                "launched_by": launched_by,
            }
        )
        mlflow.log_params({"model": args.model, "random_state": args.random_state, **hyperparams})
        mlflow.log_param("decision_threshold", round(threshold, 4))
        mlflow.log_param("cv_folds", CV_FOLDS)

        model = build_model(cfg, args.model, hyperparams, args.random_state)
        cv = cross_validate_ranking(model, X_train, y_train, args.random_state)
        model.fit(X_train, y_train)

        metrics = compute_metrics(cfg, y_test, model.predict_proba(X_test)[:, 1], threshold)
        mlflow.log_metrics({**metrics, **cv})

        # Signature = contrat d'entrée/sortie du modèle, vérifié au chargement / au serving
        signature = infer_signature(X_test, model.predict(X_test))
        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            signature=signature,
            input_example=X_test.head(3),
            pip_requirements=PIP_REQUIREMENTS,
            skops_trusted_types=SKOPS_TRUSTED_TYPES,
            metadata={"decision_threshold": threshold},  # le seuil voyage avec le modèle
        )

        # Copie locale (sortie du stage DVC train, relue par src/evaluate.py)
        shutil.rmtree(MODEL_DIR, ignore_errors=True)
        mlflow.sklearn.save_model(
            model,
            MODEL_DIR,
            signature=signature,
            pip_requirements=PIP_REQUIREMENTS,
            skops_trusted_types=SKOPS_TRUSTED_TYPES,
            metadata={"mlflow_run_id": run.info.run_id, "decision_threshold": threshold},
        )

        shown = ("roc_auc", "average_precision", "f1", "precision", "recall")
        summary = ", ".join(f"{k}={metrics[k]:.3f}" for k in shown)
        cost = metrics["business_cost"]
        print(f"{run_name}: seuil={threshold:.3f}, {summary}, business_cost={cost:.0f}")
        print(
            f"  cv_average_precision={cv['cv_average_precision']:.3f} "
            f"(± {cv['cv_average_precision_std']:.3f}), cv_roc_auc={cv['cv_roc_auc']:.3f}"
        )
        print(f"run_id : {run.info.run_id}")


if __name__ == "__main__":
    main()
