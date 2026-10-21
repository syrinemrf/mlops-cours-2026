"""Enregistre un run dans le Model Registry et le promeut avec des alias MLflow.

  1. choisit un run de l'expérience « scoring » (--run-id, ou parmi les runs filtrés) :
     règle « une erreur-type » (défaut) : parmi les runs dont le score de validation croisée
     est à moins d'une erreur-type du meilleur, on prend le plus simple ; --rule best prend
     simplement le meilleur score ;
  2. l'enregistre comme nouvelle version de « scoring-model » (sauf s'il l'est déjà) ;
  3. pose l'alias @challenger sur cette version ;
  4. pose l'alias @champion SEULEMENT si la métrique de TEST atteint
     metrics.promotion_threshold (le jeu de test ne sert qu'à cette barrière, jamais à choisir).
Les alias remplacent les « stages » (Staging/Production) dépréciés depuis MLflow 2.9.
"""

import argparse
import math
import os

import mlflow
from mlflow import MlflowClient

from src.dataset_config import load_config
from src.train import CV_FOLDS, EXPERIMENT

MODEL_NAME = "scoring-model"
# Métriques loggées par src/train.py pour lesquelles « plus grand = meilleur »
HIGHER_IS_BETTER = {"roc_auc", "average_precision", "f1", "precision", "recall", "accuracy"}
# Complexité croissante des types de modèles (départage des candidats)
MODEL_RANK = {"dummy": 0, "logistic_regression": 1, "random_forest": 2, "gradient_boosting": 3}


def score_of(run, metric: str):
    """Score de sélection : validation croisée si elle existe, sinon la métrique de test."""
    metrics = run.data.metrics
    return metrics.get(f"cv_{metric}", metrics.get(metric))


def std_of(run, metric: str) -> float:
    return run.data.metrics.get(f"cv_{metric}_std", 0.0)


def _number(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default  # « None » (profondeur illimitée) ou paramètre absent


def complexity(run) -> tuple:
    """Plus petit = plus simple : type de modèle, puis régularisation ou taille de l'ensemble."""
    params = run.data.params
    model = params.get("model", "")
    rank = MODEL_RANK.get(model, len(MODEL_RANK))
    if model == "logistic_regression":
        return (rank, _number(params.get("C"), 1.0), 0.0)  # C grand = peu régularisé
    return (
        rank,
        _number(params.get("n_estimators"), 0.0),
        _number(params.get("max_depth"), math.inf),
    )


def select_run(runs, metric: str, rule: str = "one-se"):
    """Renvoie (run choisi, explication) selon la règle demandée."""
    scored = [r for r in runs if score_of(r, metric) is not None]
    if not scored:
        raise ValueError(f"Aucun run avec la métrique « {metric} »")
    best = max(scored, key=lambda r: (score_of(r, metric), r.info.start_time))
    best_score = score_of(best, metric)
    if rule == "best":
        return best, f"meilleur score ({best_score:.4f})"
    floor = best_score - std_of(best, metric) / math.sqrt(CV_FOLDS)
    candidates = [r for r in scored if score_of(r, metric) >= floor]
    chosen = min(
        candidates,
        key=lambda r: (complexity(r), -score_of(r, metric), -r.info.start_time),
    )
    reason = (
        f"le plus simple des {len(candidates)} runs à >= {floor:.4f} "
        f"(meilleur {best_score:.4f} moins une erreur-type)"
    )
    return chosen, reason


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-id", help="run à enregistrer (défaut : choix selon la règle)")
    parser.add_argument(
        "--filter",
        default="",
        help="filtre MLflow sur les runs candidats, ex. \"tags.launched_by = 'dvc'\"",
    )
    parser.add_argument("--rule", choices=["one-se", "best"], default="one-se")
    return parser.parse_args()


def find_runs(client: MlflowClient, extra_filter: str):
    exp = client.get_experiment_by_name(EXPERIMENT)
    if exp is None:
        raise SystemExit(f"Expérience « {EXPERIMENT} » introuvable : lancez d'abord src.train")
    filters = ["attributes.status = 'FINISHED'"] + ([extra_filter] if extra_filter else [])
    return client.search_runs(
        [exp.experiment_id], filter_string=" and ".join(filters), max_results=500
    )


def main() -> None:
    args = parse_args()
    cfg = load_config()
    metric, threshold = cfg.primary_metric, cfg.promotion_threshold
    if metric not in HIGHER_IS_BETTER:
        raise SystemExit(f"metrics.primary doit être l'une de {sorted(HIGHER_IS_BETTER)}")

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    client = MlflowClient()
    if args.run_id:
        run, reason = client.get_run(args.run_id), "run demandé"
    else:
        try:
            run, reason = select_run(find_runs(client, args.filter), metric, args.rule)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    print(f"Run retenu : {run.info.run_name} ({reason})")
    score = run.data.metrics[metric]  # métrique de TEST : sert de barrière uniquement

    # Une seule version par run : relancer le script ne crée pas de doublon
    existing = client.search_model_versions(
        f"name = '{MODEL_NAME}' and run_id = '{run.info.run_id}'"
    )
    if existing:
        version = existing[0].version
        print(f"Run déjà enregistré : version {version}")
    else:
        # MLflow 3 : le modèle loggé par le run est un « LoggedModel » (models:/m-...)
        model_id = run.outputs.model_outputs[0].model_id
        mv = mlflow.register_model(f"models:/{model_id}", MODEL_NAME)
        version = mv.version
        print(f"Enregistré : {MODEL_NAME} version {version}")

    passed = score >= threshold
    tags = {
        metric: f"{score:.4f}",
        "validation_status": "passed" if passed else "failed",
        "data_md5": run.data.tags.get("data_md5", "unknown"),
        "selection_rule": args.rule if not args.run_id else "run-id",
    }
    cv_score = run.data.metrics.get(f"cv_{metric}")
    if cv_score is not None:
        tags[f"cv_{metric}"] = f"{cv_score:.4f}"
    for key, value in tags.items():
        client.set_model_version_tag(MODEL_NAME, version, key, value)

    client.set_registered_model_alias(MODEL_NAME, "challenger", version)
    print(f"  @challenger -> version {version} ({metric} test = {score:.4f})")
    if passed:
        client.set_registered_model_alias(MODEL_NAME, "champion", version)
        print(f"  @champion   -> version {version} ({metric} test >= seuil {threshold})")
    else:
        try:
            current = client.get_model_version_by_alias(MODEL_NAME, "champion").version
        except mlflow.exceptions.MlflowException:
            current = "aucun"
        print(f"  champion inchangé (version {current}) : {metric} test < seuil {threshold}")


if __name__ == "__main__":
    main()
