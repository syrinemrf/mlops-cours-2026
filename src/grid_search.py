"""Lance 22 runs d'entraînement (un sous-processus par run) dans l'expérience « scoring »."""

# Identity is based on bytes and effective parameters, not a run name or test score.
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
from importlib.metadata import version
from itertools import product
from pathlib import Path

import mlflow
import yaml
from mlflow import MlflowClient

from src.train import EXPERIMENT, MODELS, parse_args

CONFIGS = [
    # Référence naïve : tout modèle utile doit faire mieux (ROC AUC = 0,5)
    ("dummy", []),
    # Régression logistique : 4 x 2 = 8 runs
    *[
        ("logistic_regression", ["--C", str(c), "--class_weight", w])
        for c, w in product([0.01, 0.1, 1.0, 10.0], ["none", "balanced"])
    ],
    # Random Forest : 3 x 3 = 9 runs
    *[
        ("random_forest", ["--n_estimators", str(n), "--max_depth", str(d)])
        for n, d in product([100, 200, 400], [4, 8, "none"])
    ],
    # Gradient Boosting : 2 x 2 = 4 runs
    *[
        ("gradient_boosting", ["--n_estimators", str(n), "--max_depth", str(d)])
        for n, d in product([100, 200], [2, 3])
    ],
]


IDENTITY_FILES = [
    "src/train.py",
    "src/grid_search.py",
    "src/dataset_config.py",
    "dataset.yaml",
    "params.yaml",
    "uv.lock",
    "dvc.lock",
    "data/raw/dataset.csv",
    "data/processed/train.csv",
    "data/processed/test.csv",
]
METRICS = {
    "roc_auc",
    "average_precision",
    "pr_auc_trapezoidal",
    "precision",
    "recall",
    "f1",
    "accuracy",
    "business_cost",
    "tn",
    "fp",
    "fn",
    "tp",
    "fit_seconds",
    "brier_score",
    "log_loss",
}
REPORT = Path("reports/m1/grid-search-manifest.json")


def run_identity(model, options):
    args = parse_args(["--model", model, *options])
    params = {
        "model": model,
        "random_state": args.random_state,
        **{k: getattr(args, k) for k in MODELS[model][1]},
    }
    identity = {
        "protocol": "A",
        "evaluation_role": "pedagogical_grid_search",
        "parameters": params,
        "files": {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in IDENTITY_FILES},
        "python": platform.python_version(),
        "packages": {p: version(p) for p in ("scikit-learn", "numpy", "pandas", "mlflow", "skops")},
        "threads": {k: "1" for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
    }
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return key, identity


def reusable(client, run, key, params):
    """Only completed, fully measured runs with a READY logged model can be reused."""
    if (
        run.info.status != "FINISHED"
        or run.data.tags.get("grid_identity") != key
        or run.data.tags.get("protocol") != "A"
        or run.data.tags.get("launched_by") != "grid_search"
    ):
        return False
    if any(run.data.params.get(k) != str(v) for k, v in params.items()):
        return False
    if not run.data.metrics.keys() >= METRICS:
        return False
    if not all(math.isfinite(run.data.metrics[k]) for k in METRICS):
        return False
    outputs = run.outputs.model_outputs if run.outputs else []
    return len(outputs) == 1 and str(client.get_logged_model(outputs[0].model_id).status) == "READY"


def main() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    experiment = mlflow.set_experiment(EXPERIMENT)
    client = MlflowClient()
    source = yaml.safe_load(Path("dataset.yaml").read_text())
    env = {**os.environ, "LAUNCHED_BY": "grid_search"}
    env.pop("DVC_STAGE", None)
    env.pop("MLFLOW_RUN_ID", None)
    env.update({k: "1" for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")})
    results = []
    failures = []
    print(f"Lancement de {len(CONFIGS)} configurations séquentielles", flush=True)
    for i, (model, options) in enumerate(CONFIGS, 1):
        key, identity = run_identity(model, options)
        candidates = client.search_runs([experiment.experiment_id], f"tags.grid_identity = '{key}'")
        completed = next(
            (r for r in candidates if reusable(client, r, key, identity["parameters"])), None
        )
        if completed is not None:
            run_id, action = completed.info.run_id, "reused"
            print(f"[{i}/22] reused {model} {run_id}", flush=True)
        else:
            run = client.create_run(
                experiment.experiment_id,
                tags={
                    "grid_identity": key,
                    "protocol": "A",
                    "protocol_id": "mlops_A_v1",
                    "launched_by": "grid_search",
                    "evaluation_role": "pedagogical_grid_search",
                    "mlflow.source.git.commit": subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], text=True
                    ).strip(),
                    "dataset": source["name"],
                    "data_version": str(source["source"]["version"]),
                    "data_sha256": identity["files"]["data/raw/dataset.csv"],
                },
            )
            run_id, action = run.info.run_id, "trained"
            client.log_dict(run_id, identity, "grid-identity.json")
            command = [sys.executable, "-m", "src.train", "--model", model, *options]
            print(f"[{i}/22] {' '.join(command[1:])} run_id={run_id}", flush=True)
            try:
                subprocess.run(command, check=True, env={**env, "MLFLOW_RUN_ID": run_id})
            except Exception as error:
                client.set_tag(run_id, "grid_error", str(error)[:2000])
                client.set_terminated(run_id, status="FAILED")
                failures.append({"run_id": run_id, "error": str(error)})
        run = client.get_run(run_id)
        if not reusable(client, run, key, identity["parameters"]):
            failures.append({"run_id": run_id, "error": "incomplete or unverifiable run"})
        results.append(
            {
                "index": i,
                "model": model,
                "options": options,
                "run_id": run_id,
                "action": action,
                "identity": key,
                "status": run.info.status,
                "params": run.data.params,
                "metrics": run.data.metrics,
                "tags": run.data.tags,
            }
        )
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        temporary = REPORT.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"protocol": "A", "runs": results, "failures": failures}, indent=2) + "\n"
        )
        temporary.replace(REPORT)
    if failures:
        raise SystemExit(f"Grid has {len(failures)} errors: see {REPORT}")
    print("✓ 22 configurations verified; no model promoted.", flush=True)


if __name__ == "__main__":
    main()
