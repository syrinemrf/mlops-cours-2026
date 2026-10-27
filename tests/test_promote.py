"""Gate boundaries, rejected inputs and sequential registry idempotence, offline."""

from types import SimpleNamespace as NS

import pytest

from src import promote
from src.dataset_config import load_config


@pytest.fixture
def registry(monkeypatch):
    versions, aliases = [], {}
    run = NS(
        info=NS(run_id="run1", status="FINISHED", experiment_id="2"),
        data=NS(
            tags={
                "protocol": "A",
                "protocol_id": "mlops_A_v1",
                "dataset": load_config().name,
                "data_md5": "dataset-hash",
            },
            metrics={"roc_auc": 0.8},
            params={"decision_threshold": ".5", "model": "logistic_regression"},
        ),
        outputs=NS(model_outputs=[NS(model_id="model1")]),
    )
    logged = NS(model_id="model1", source_run_id="run1", status="READY")

    def register(uri, name):
        version = NS(version=str(len(versions) + 1), run_id="run1", status="READY", tags={})
        versions.append(version)
        return version

    client = NS(
        get_experiment_by_name=lambda _: NS(experiment_id="2"),
        get_logged_model=lambda _: logged,
        search_model_versions=lambda _: versions,
        set_model_version_tag=lambda name, version, k, v: versions[int(version) - 1].tags.update(
            {k: v}
        ),
        set_registered_model_alias=lambda name, alias, version: aliases.update({alias: version}),
    )
    monkeypatch.setattr(promote, "file_md5", lambda _: "dataset-hash")
    monkeypatch.setattr(promote.mlflow, "register_model", register)
    return client, run, versions, aliases, logged


@pytest.mark.parametrize(
    "score,passed", [(0.5, False), (0.699999, False), (0.7, True), (0.8, True)]
)
def test_gate_boundary_and_negative_control(registry, score, passed):
    client, run, versions, aliases, _ = registry
    run.data.metrics["roc_auc"] = score
    if score == 0.5:
        run.data.params["model"] = "dummy"
    aliases["champion"] = "previous"
    result = promote.promote_run(client, load_config(), run)
    assert result["champion_updated"] is passed
    assert aliases["champion"] == ("1" if passed else "previous")
    assert aliases["challenger"] == "1"
    assert versions[0].tags["validation_status"] == ("passed" if passed else "failed")
    assert versions[0].tags["promotion_threshold"] == "0.7"


def test_idempotence_and_explicit_challenger_only(registry):
    client, run, versions, aliases, _ = registry
    first = promote.promote_run(client, load_config(), run)
    aliases["champion"] = "agreed-champion"
    second = promote.promote_run(client, load_config(), run, challenger_only=True)
    assert first["created"] and not second["created"]
    assert len(versions) == 1
    assert aliases == {"champion": "agreed-champion", "challenger": "1"}


@pytest.mark.parametrize(
    "defect", ["failed", "protocol", "hash", "nan", "model", "output", "threshold"]
)
def test_invalid_inputs_never_mutate_registry(registry, defect):
    client, run, versions, aliases, logged = registry
    if defect == "failed":
        run.info.status = "FAILED"
    elif defect == "protocol":
        run.data.tags["protocol"] = "B1"
    elif defect == "hash":
        run.data.tags["data_md5"] = "wrong"
    elif defect == "nan":
        run.data.metrics["roc_auc"] = float("nan")
    elif defect == "model":
        logged.status = "FAILED"
    elif defect == "output":
        run.outputs.model_outputs = []
    else:
        run.data.params["decision_threshold"] = "nan"
    with pytest.raises(ValueError):
        promote.promote_run(client, load_config(), run)
    assert versions == [] and aliases == {}
