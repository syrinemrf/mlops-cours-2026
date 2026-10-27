"""Verify the DVC champion and remote predictions without changing the registry."""

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import mlflow
import numpy as np
import yaml
from mlflow import MlflowClient
from mlflow.models import Model

from src.dataset_config import load_config
from src.promote import MODEL_NAME
from src.train import MODEL_DIR, MODELS, TEST_CSV, compute_metrics, file_md5, parse_args


def validate_run_lineage(run, cfg, data_md5, expected_run_id=None, require_dvc=False):
    """Reject wrong run/data/protocol identities before trusting model metrics."""
    if expected_run_id is not None and run.info.run_id != expected_run_id:
        raise ValueError("Unexpected source run")
    tags = run.data.tags
    if (
        run.info.status != "FINISHED"
        or tags.get("protocol") != "A"
        or tags.get("protocol_id") != "mlops_A_v1"
        or tags.get("dataset") != cfg.name
        or tags.get("data_md5") != data_md5
        or (require_dvc and tags.get("launched_by") != "dvc")
    ):
        raise ValueError("Invalid protocol A dataset/DVC lineage")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--champion-run-id")
    parser.add_argument("--challenger-run-id")
    parser.add_argument("--challenger-version")
    parser.add_argument("--output", type=Path, default=Path("reports/m1/registry-current.json"))
    options = parser.parse_args(argv)
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    client = MlflowClient()
    cfg = load_config()
    defaults = parse_args([])
    local_info = Model.load(str(MODEL_DIR / "MLmodel"))
    local_run_id = local_info.metadata["mlflow_run_id"]
    if options.champion_run_id:
        assert local_run_id == options.champion_run_id
    lock = yaml.safe_load(Path("dvc.lock").read_text())
    data_md5 = next(
        output["md5"]
        for stage in lock["stages"].values()
        for output in stage.get("outs", [])
        if output["path"] == cfg.raw_path
    )
    assert data_md5 == file_md5(cfg.raw_path)
    data_sha256 = hashlib.sha256(Path(cfg.raw_path).read_bytes()).hexdigest()
    versions = list(client.search_model_versions(f"name = '{MODEL_NAME}'"))
    assert len(versions) >= 3
    assert len({version.run_id for version in versions}) == len(versions)
    aliases = {}
    for alias in ("champion", "challenger"):
        version = client.get_model_version_by_alias(MODEL_NAME, alias)
        run = client.get_run(version.run_id)
        validate_run_lineage(
            run,
            cfg,
            data_md5,
            local_run_id if alias == "champion" else options.challenger_run_id,
            require_dvc=alias == "champion",
        )
        assert run.data.metrics[cfg.primary_metric] >= cfg.promotion_threshold
        assert version.tags["validation_status"] == "passed"
        assert version.tags["source_run_id"] == version.run_id
        assert version.tags["data_md5"] == data_md5
        assert version.tags["protocol"] == "A"
        assert float(version.tags["promotion_threshold"]) == cfg.promotion_threshold
        if alias == "challenger" and options.challenger_version:
            assert version.version == options.challenger_version
        aliases[alias] = {
            "version": version.version,
            "run_id": version.run_id,
            "roc_auc": run.data.metrics["roc_auc"],
        }
    assert aliases["champion"]["run_id"] != aliases["challenger"]["run_id"]
    dummy_versions = [
        version
        for version in versions
        if client.get_run(version.run_id).data.params.get("model") == "dummy"
    ]
    assert dummy_versions
    for dummy in dummy_versions:
        assert dummy.tags["validation_status"] == "failed"
        assert float(dummy.tags["roc_auc"]) == 0.5
        assert dummy.version != aliases["champion"]["version"]

    champion = client.get_model_version_by_alias(MODEL_NAME, "champion")
    run = client.get_run(champion.run_id)
    assert run.data.tags["data_sha256"] == data_sha256
    assert champion.tags["data_sha256"] == data_sha256
    assert run.data.params["model"] == defaults.model
    assert run.data.params["random_state"] == str(defaults.random_state)
    threshold = float(run.data.params["decision_threshold"])
    assert threshold == float(local_info.metadata["decision_threshold"])
    outputs = run.outputs.model_outputs
    assert len(outputs) == 1
    logged = client.get_logged_model(outputs[0].model_id)
    assert logged.source_run_id == local_run_id and str(logged.status) == "READY"
    uri = f"models:/{MODEL_NAME}@champion"
    X, y = cfg.read_xy(TEST_CSV)
    with tempfile.TemporaryDirectory(prefix="m1-champion-") as directory:
        remote_path = Path(mlflow.artifacts.download_artifacts(uri, dst_path=directory))
        remote_info = Model.load(str(remote_path / "MLmodel"))
        assert remote_info.signature.to_dict() == local_info.signature.to_dict()
        assert remote_info.signature.inputs.input_names() == cfg.features
        assert float(remote_info.metadata["decision_threshold"]) == threshold
        model = mlflow.sklearn.load_model(str(remote_path))
        local_model = mlflow.sklearn.load_model(str(MODEL_DIR))
        assert list(model.feature_names_in_) == cfg.features
        assert model.named_steps["model"].random_state == defaults.random_state
        assert local_model.named_steps["model"].random_state == defaults.random_state
        for name in MODELS[defaults.model][1]:
            expected = getattr(defaults, name)
            assert getattr(model.named_steps["model"], name) == expected
            assert getattr(local_model.named_steps["model"], name) == expected
            assert run.data.params[name] == str(expected)
        probabilities = model.predict_proba(X)[:, 1]
        np.testing.assert_allclose(
            probabilities, local_model.predict_proba(X)[:, 1], rtol=0, atol=0
        )
        metrics = compute_metrics(cfg, y, probabilities, threshold)
        evaluation = json.loads(Path("reports/metrics.json").read_text())
        for name, value in metrics.items():
            assert abs(value - run.data.metrics[name]) < 1e-12, name
            assert evaluation[name] == round(value, 4), name
        decisions = (probabilities[:5] >= threshold).astype(int)
        np.testing.assert_array_equal(model.predict(X.head(5)), decisions)
        served = mlflow.pyfunc.load_model(str(remote_path)).predict(X.head(5))
        np.testing.assert_array_equal(served, decisions)
        filename = local_info.flavors["sklearn"]["pickled_model"]
        serialized_hashes = {
            "dvc_local": hashlib.sha256((MODEL_DIR / filename).read_bytes()).hexdigest(),
            "registry": hashlib.sha256((remote_path / filename).read_bytes()).hexdigest(),
        }
    report = {
        "model_name": MODEL_NAME,
        "versions_count": len(versions),
        "aliases": aliases,
        "dummy_rejected": True,
        "uri": uri,
        "dvc_run_id": local_run_id,
        "data_md5": data_md5,
        "data_sha256": data_sha256,
        "decision_threshold": threshold,
        "parameters": run.data.params,
        "signature_matches_dvc_model": True,
        "all_test_probabilities_exactly_match_local": True,
        "metrics_match_run_and_rounded_report": True,
        "serialized_model_sha256": serialized_hashes,
        "feature_count": len(cfg.features),
        "probabilities_first_five": probabilities[:5].tolist(),
        "predictions_first_five": decisions.tolist(),
        "pyfunc_predictions_match": True,
    }
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
