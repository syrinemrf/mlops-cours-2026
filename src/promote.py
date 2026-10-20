"""Enregistre un run dans le Model Registry et le promeut avec des alias MLflow.

  1. choisit le meilleur run de l'expérience « scoring » selon metrics.primary
     (dataset.yaml) — ou le run donné par --run-id, ou le meilleur parmi --filter ;
  2. l'enregistre comme nouvelle version de « scoring-model » (sauf s'il l'est déjà) ;
  3. pose l'alias @challenger sur cette version ;
  4. pose l'alias @champion SEULEMENT si la métrique atteint metrics.promotion_threshold.
Les alias remplacent les « stages » (Staging/Production) dépréciés depuis MLflow 2.9.
"""

import argparse
import json
import math
import os

import mlflow
from mlflow import MlflowClient

from src.dataset_config import load_config
from src.train import EXPERIMENT, file_md5

MODEL_NAME = "scoring-model"
# Métriques loggées par src/train.py pour lesquelles « plus grand = meilleur »
HIGHER_IS_BETTER = {"roc_auc", "average_precision", "f1", "precision", "recall", "accuracy"}


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-id", help="run à enregistrer (défaut : le meilleur run)")
    parser.add_argument(
        "--filter",
        default="",
        help="filtre MLflow sur les runs candidats, ex. \"tags.launched_by = 'dvc'\"",
    )
    parser.add_argument(
        "--challenger-only",
        action="store_true",
        help="Affectation explicite du challenger sans déplacer le champion",
    )
    return parser.parse_args(argv)


def find_run(client: MlflowClient, metric: str, run_id: str | None, extra_filter: str):
    """Le run demandé, sinon le meilleur run terminé (à égalité : le plus récent)."""
    if run_id:
        return client.get_run(run_id)
    exp = client.get_experiment_by_name(EXPERIMENT)
    if exp is None:
        raise SystemExit(f"Expérience « {EXPERIMENT} » introuvable : lancez d'abord src.train")
    filters = ["attributes.status = 'FINISHED'", "tags.protocol = 'A'"] + (
        [extra_filter] if extra_filter else []
    )
    runs = client.search_runs(
        [exp.experiment_id],
        filter_string=" and ".join(filters),
        order_by=[f"metrics.{metric} DESC", "attributes.start_time DESC"],
        max_results=1,
    )
    if not runs or metric not in runs[0].data.metrics:
        raise SystemExit(f"Aucun run avec la métrique « {metric} » ({' and '.join(filters)})")
    return runs[0]


def promote_run(client, cfg, run, challenger_only=False):
    """Keep the official gate; challenger-only explicitly preserves the champion.

    Calls must be sequential: run-based idempotence is not a distributed lock.
    A failed gate still permits registration/audit and the challenger alias.
    """
    metric, threshold = cfg.primary_metric, cfg.promotion_threshold
    if metric not in HIGHER_IS_BETTER or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Invalid promotion metric/threshold")
    experiment = client.get_experiment_by_name(EXPERIMENT)
    tags = run.data.tags
    if (
        experiment is None
        or run.info.experiment_id != experiment.experiment_id
        or run.info.status != "FINISHED"
        or tags.get("protocol") != "A"
        or tags.get("protocol_id") != "mlops_A_v1"
        or tags.get("dataset") != cfg.name
    ):
        raise ValueError("Only FINISHED protocol A runs from the scoring dataset are eligible")
    if tags.get("data_md5") != file_md5(cfg.raw_path):
        raise ValueError("Run dataset hash differs from the current contract data")
    score = run.data.metrics.get(metric)
    if score is None or not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("Missing or invalid promotion score")
    decision_threshold = float(run.data.params["decision_threshold"])
    if not math.isfinite(decision_threshold) or not 0 <= decision_threshold <= 1:
        raise ValueError("Invalid model decision threshold")
    outputs = run.outputs.model_outputs if run.outputs else []
    if len(outputs) != 1:
        raise ValueError("Expected one logged model per run")
    logged = client.get_logged_model(outputs[0].model_id)
    if str(logged.status) != "READY" or logged.source_run_id != run.info.run_id:
        raise ValueError("Logged model is not READY or has a different source run")

    existing = client.search_model_versions(
        f"name = '{MODEL_NAME}' and run_id = '{run.info.run_id}'"
    )
    if len(existing) > 1:
        raise ValueError("Duplicate versions already exist; inspect without deleting them")
    if existing:
        registered = existing[0]
        created = False
    else:
        registered = mlflow.register_model(f"models:/{logged.model_id}", MODEL_NAME)
        created = True
    if registered.run_id != run.info.run_id or str(registered.status) != "READY":
        raise ValueError("Registered version does not match the READY source run")
    version = registered.version
    passed = score >= threshold
    version_tags = {
        metric: str(score),
        "primary_metric": metric,
        "promotion_threshold": str(threshold),
        "validation_status": "passed" if passed else "failed",
        "source_run_id": run.info.run_id,
        "data_md5": tags["data_md5"],
        "data_sha256": tags.get("data_sha256", "unknown"),
        "protocol": "A",
        "protocol_id": "mlops_A_v1",
        "dataset": cfg.name,
        "data_version": tags.get("data_version", "unknown"),
        "selection_scope": "pedagogical_test_exploratory",
        "decision_threshold": str(decision_threshold),
    }
    for key, value in version_tags.items():
        client.set_model_version_tag(MODEL_NAME, version, key, value)
    client.set_registered_model_alias(MODEL_NAME, "challenger", version)
    champion_updated = passed and not challenger_only
    if champion_updated:
        client.set_registered_model_alias(MODEL_NAME, "champion", version)
    return {
        "version": str(version),
        "run_id": run.info.run_id,
        "created": created,
        "metric": metric,
        "score": score,
        "promotion_threshold": threshold,
        "validation_status": version_tags["validation_status"],
        "challenger_only": challenger_only,
        "champion_updated": champion_updated,
    }


def main() -> None:
    args = parse_args()
    cfg = load_config()
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    client = MlflowClient()
    run = find_run(client, cfg.primary_metric, args.run_id, args.filter)
    print(json.dumps(promote_run(client, cfg, run, args.challenger_only), indent=2))


if __name__ == "__main__":
    main()
