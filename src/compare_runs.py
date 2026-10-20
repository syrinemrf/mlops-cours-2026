"""Verify and export the 22 pedagogical runs without selecting a champion."""

import csv
import hashlib
import json
import os
from pathlib import Path

import mlflow
from mlflow import MlflowClient

from src.dataset_config import load_config
from src.grid_search import CONFIGS, REPORT, reusable, run_identity
from src.train import compute_metrics

OUTPUT = Path("reports/m1")


def main():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    client = MlflowClient()
    manifest = json.loads(REPORT.read_text())
    assert not manifest["failures"] and len(manifest["runs"]) == len(CONFIGS) == 22
    rows = []
    starts, ends = [], []
    for entry, (model, options) in zip(manifest["runs"], CONFIGS, strict=True):
        identity, details = run_identity(model, options)
        run = client.get_run(entry["run_id"])
        assert entry["identity"] == identity
        assert reusable(client, run, identity, details["parameters"]), run.info.run_id
        starts.append(run.info.start_time)
        ends.append(run.info.end_time)
        params, metrics, tags = run.data.params, run.data.metrics, run.data.tags
        assert (
            tags["data_sha256"]
            == hashlib.sha256(Path("data/raw/dataset.csv").read_bytes()).hexdigest()
        )
        assert tags["evaluation_role"] == "pedagogical_grid_search"
        assert params["random_state"] == "42"
        assert sum(metrics[k] for k in ("tn", "fp", "fn", "tp")) == 294
        assert metrics["fn"] + metrics["tp"] == 47
        assert metrics["business_cost"] == metrics["fn"] + metrics["fp"]
        rows.append(
            {
                "index": entry["index"],
                "model": model,
                "hyperparameters": json.dumps(
                    {k: v for k, v in params.items() if k not in {"model", "decision_threshold"}},
                    sort_keys=True,
                ),
                **{
                    k: metrics[k]
                    for k in (
                        "roc_auc",
                        "average_precision",
                        "pr_auc_trapezoidal",
                        "precision",
                        "recall",
                        "f1",
                        "accuracy",
                        "business_cost",
                        "fit_seconds",
                        "tn",
                        "fp",
                        "fn",
                        "tp",
                        "brier_score",
                        "log_loss",
                    )
                },
                "run_seconds": (run.info.end_time - run.info.start_time) / 1000,
                "decision_threshold": params["decision_threshold"],
                "run_id": run.info.run_id,
                "data_version": tags["data_version"],
                "data_md5": tags["data_md5"],
                "data_sha256": tags["data_sha256"],
                "status": run.info.status,
            }
        )
    assert len({r["run_id"] for r in rows}) == 22
    # One model per family is enough to verify serialization without copying all 22.
    X, y = load_config().read_xy("data/processed/test.csv")
    reload_checks = []
    for family in ("dummy", "logistic_regression", "random_forest", "gradient_boosting"):
        best = max((r for r in rows if r["model"] == family), key=lambda r: r["roc_auc"])
        run = client.get_run(best["run_id"])
        model_id = run.outputs.model_outputs[0].model_id
        loaded = mlflow.sklearn.load_model(f"models:/{model_id}")
        assert list(loaded.feature_names_in_) == load_config().features
        calculated = compute_metrics(
            load_config(), y, loaded.predict_proba(X)[:, 1], float(best["decision_threshold"])
        )
        for metric, value in calculated.items():
            assert abs(value - best[metric]) < 1e-12, (family, metric)
        reload_checks.append(
            {"model": family, "run_id": best["run_id"], "model_id": model_id, "metrics_match": True}
        )
    previous = json.loads((OUTPUT / "smoke-validation.json").read_text())
    smoke_lr = next(r for r in previous["runs"] if r["model"] == "logistic_regression")
    grid_lr = next(
        r
        for r in rows
        if r["model"] == "logistic_regression"
        and json.loads(r["hyperparameters"])["C"] == "0.1"
        and json.loads(r["hyperparameters"])["class_weight"] == "balanced"
    )
    for metric, value in smoke_lr["metrics"].items():
        assert abs(grid_lr[metric] - value) < 1e-12, metric
    experiment = client.get_experiment_by_name("scoring")
    all_runs = client.search_runs([experiment.experiment_id], max_results=1000)
    models = list(client.search_registered_models())
    summary = {
        "runs": rows,
        "model_reload_checks": reload_checks,
        "experiment_id": experiment.experiment_id,
        "smoke_lr_reproduction": "all previous metrics match within 1e-12",
        "experiment_total_runs": len(all_runs),
        "grid_elapsed_seconds": (max(ends) - min(starts)) / 1000,
        "registered_models": [m.name for m in models],
        "verification": (
            "22 FINISHED runs, matching content identities, parameters, metrics and READY models"
        ),
    }
    (OUTPUT / "grid-comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (OUTPUT / "grid-comparison.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    columns = [
        "index",
        "model",
        "hyperparameters",
        "roc_auc",
        "average_precision",
        "pr_auc_trapezoidal",
        "precision",
        "recall",
        "f1",
        "accuracy",
        "business_cost",
        "decision_threshold",
        "fit_seconds",
        "run_id",
    ]
    lines = [
        "# Grille M1 — protocole A, comparaison exploratoire",
        "",
        "Scores test répétés : aucune estimation finale indépendante, aucun champion désigné.",
        "",
        "AP = average_precision ; PR-AUC trapézoïdale conservée séparément. "
        "Temps = fit pipeline uniquement.",
        "",
        "Version Kaggle 1 ; toutes les lignes ont le même export MD5 `"
        + rows[0]["data_md5"]
        + "`.",
        "SHA-256 et paramètres complets dans grid-comparison.csv/json.",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                f"{row[c]:.6f}" if isinstance(row[c], float) else str(row[c]) for c in columns
            )
            + " |"
        )
    lines += ["", "## Candidats descriptifs, sans promotion", ""]
    for family in ["dummy", "logistic_regression", "random_forest", "gradient_boosting"]:
        best = max((r for r in rows if r["model"] == family), key=lambda r: r["roc_auc"])
        lines.append(
            f"- {family} : meilleur ROC AUC observé {best['roc_auc']:.6f}, "
            f"configuration {best['index']}, run {best['run_id']}."
        )
    for metric, minimize in [
        ("average_precision", False),
        ("f1", False),
        ("business_cost", True),
        ("brier_score", True),
        ("log_loss", True),
    ]:
        value = (min if minimize else max)(r[metric] for r in rows)
        winners = [str(r["index"]) for r in rows if r[metric] == value]
        lines.append(f"- {metric} : {value:.6f}, configuration(s) {', '.join(winners)}.")
    lines += [
        "",
        "## Effet des poids LR à C constant",
        "",
        "Différences balanced moins None, à leurs seuils respectifs 0.838435 et 0.5 :",
        "",
        "| C | delta AUC | delta AP | delta coût | delta rappel |",
        "|---|---|---|---|---|",
    ]
    for c in ("0.01", "0.1", "1.0", "10.0"):
        pair = {
            json.loads(r["hyperparameters"])["class_weight"]: r
            for r in rows
            if r["model"] == "logistic_regression" and json.loads(r["hyperparameters"])["C"] == c
        }
        a, b = pair["None"], pair["balanced"]
        lines.append(
            f"| {c} | {b['roc_auc'] - a['roc_auc']:+.6f} | "
            f"{b['average_precision'] - a['average_precision']:+.6f} | "
            f"{b['business_cost'] - a['business_cost']:+.0f} | "
            f"{b['recall'] - a['recall']:+.6f} |"
        )
    (OUTPUT / "grid-comparison.md").write_text("\n".join(lines) + "\n")
    print(summary["verification"])
    print(f"Experiment runs: {len(all_runs)}; registered models: {summary['registered_models']}")


if __name__ == "__main__":
    main()
