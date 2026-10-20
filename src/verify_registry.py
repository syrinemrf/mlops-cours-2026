"""Read-only checks for the agreed pedagogical aliases and remote predictions."""

import json
import os
from pathlib import Path

import mlflow
import numpy as np
from mlflow import MlflowClient

from src.dataset_config import load_config
from src.promote import MODEL_NAME
from src.train import TEST_CSV

CHAMPION_RUN = "5ef49fc5f3e740f28c523b0dcc1ae8c1"
CHALLENGER_RUN = "139ae364aa6e4166b2bd19ef533f48e7"
DUMMY_RUN = "0c42486a18f340ddb2db995d8797c70d"


def main():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    client = MlflowClient()
    cfg = load_config()
    assert cfg.primary_metric == "roc_auc" and cfg.promotion_threshold == 0.70
    versions = list(client.search_model_versions(f"name = '{MODEL_NAME}'"))
    assert len(versions) >= 3
    expected = {"champion": CHAMPION_RUN, "challenger": CHALLENGER_RUN}
    aliases = {}
    for alias, run_id in expected.items():
        version = client.get_model_version_by_alias(MODEL_NAME, alias)
        assert version.run_id == run_id
        run = client.get_run(run_id)
        assert run.data.metrics[cfg.primary_metric] >= cfg.promotion_threshold
        assert version.tags["validation_status"] == "passed"
        assert version.tags["source_run_id"] == run_id
        assert version.tags["data_md5"] == run.data.tags["data_md5"]
        assert version.tags["protocol"] == "A"
        assert float(version.tags["promotion_threshold"]) == 0.7
        aliases[alias] = {
            "version": version.version,
            "run_id": run_id,
            "roc_auc": run.data.metrics["roc_auc"],
        }
    dummy = next(v for v in versions if v.run_id == DUMMY_RUN)
    assert dummy.tags["validation_status"] == "failed"
    assert float(dummy.tags["roc_auc"]) == 0.5
    assert dummy.version != aliases["champion"]["version"]
    uri = f"models:/{MODEL_NAME}@champion"
    model = mlflow.sklearn.load_model(uri)
    metadata = mlflow.models.get_model_info(uri).metadata
    threshold = float(metadata["decision_threshold"])
    run = client.get_run(CHAMPION_RUN)
    assert threshold == float(run.data.params["decision_threshold"]) == 0.5
    assert model.named_steps["model"].C == 1.0
    assert model.named_steps["model"].class_weight is None
    assert list(model.feature_names_in_) == cfg.features
    X, _ = cfg.read_xy(TEST_CSV)
    probabilities = model.predict_proba(X.head(5))[:, 1]
    decisions = (probabilities >= threshold).astype(int)
    assert len(probabilities) == 5 and np.isfinite(probabilities).all()
    np.testing.assert_array_equal(model.predict(X.head(5)), decisions)
    served = mlflow.pyfunc.load_model(uri).predict(X.head(5))
    np.testing.assert_array_equal(served, decisions)
    report = {
        "model_name": MODEL_NAME,
        "versions_count": len(versions),
        "aliases": aliases,
        "dummy_rejected": True,
        "uri": uri,
        "decision_threshold": threshold,
        "decision_threshold_matches_run": True,
        "feature_count": len(cfg.features),
        "probabilities_first_five": probabilities.tolist(),
        "predictions_first_five": decisions.tolist(),
        "pyfunc_predictions_match": True,
    }
    Path("reports/m1/registry-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
