"""Official grid coverage and conservative content-based resumption."""

from collections import Counter
from types import SimpleNamespace as NS

import pandas as pd
import pytest
import yaml

from src import grid_search as grid
from src.dataset_config import load_config
from src.train import decision_threshold, parse_args


@pytest.mark.parametrize("dvc_weight", ["none", "balanced"])
def test_grid_preserves_family_parameters_when_dvc_defaults_change(
    tmp_path, monkeypatch, dvc_weight
):
    # Deliberately different defaults expose accidental inheritance by a grid family.
    defaults = {
        "model": "logistic_regression",
        "C": 123.0,
        "class_weight": dvc_weight,
        "n_estimators": 3,
        "max_depth": 1,
        "learning_rate": 0.1,
        "random_state": 42,
    }
    (tmp_path / "params.yaml").write_text(yaml.safe_dump({"train": defaults}))
    monkeypatch.chdir(tmp_path)
    logistic = set()
    forest = set()
    boosting = set()
    for family, options in grid.CONFIGS:
        args = parse_args(["--model", family, *options])
        effective = {key: getattr(args, key) for key in grid.MODELS[family][1]}
        if family == "logistic_regression":
            assert set(effective) == {"C", "class_weight"}
            logistic.add((effective["C"], effective["class_weight"]))
        elif family == "random_forest":
            assert set(effective) == {"n_estimators", "max_depth", "class_weight"}
            assert effective["class_weight"] == "balanced"
            forest.add((effective["n_estimators"], effective["max_depth"]))
        elif family == "gradient_boosting":
            assert set(effective) == {"n_estimators", "max_depth", "learning_rate"}
            assert effective["learning_rate"] == 0.1
            boosting.add((effective["n_estimators"], effective["max_depth"]))
        else:
            assert family == "dummy" and effective == {}
    assert logistic == {(c, w) for c in (0.01, 0.1, 1.0, 10.0) for w in (None, "balanced")}
    assert forest == {(n, d) for n in (100, 200, 400) for d in (4, 8, None)}
    assert boosting == {(n, d) for n in (100, 200) for d in (2, 3)}


def test_official_grid_and_family_thresholds():
    assert len(grid.CONFIGS) == 22
    assert Counter(m for m, _ in grid.CONFIGS) == {
        "dummy": 1,
        "logistic_regression": 8,
        "random_forest": 9,
        "gradient_boosting": 4,
    }
    assert len({(m, tuple(options)) for m, options in grid.CONFIGS}) == 22
    y = pd.Series([0] * 986 + [1] * 190)
    for model, options in grid.CONFIGS:
        args = parse_args(["--model", model, *options])
        params = {k: getattr(args, k) for k in grid.MODELS[model][1]}
        threshold = decision_threshold(load_config(), params.get("class_weight"), y)
        expected = 986 / 1176 if params.get("class_weight") == "balanced" else 0.5
        assert threshold == pytest.approx(expected)
        if model in {"gradient_boosting", "dummy"}:
            assert "class_weight" not in params


def test_identity_changes_with_data_and_parameters(tmp_path, monkeypatch):
    data = tmp_path / "train.csv"
    data.write_text("version-one")
    monkeypatch.setattr(grid, "IDENTITY_FILES", [str(data)])
    first, manifest = grid.run_identity("dummy", [])
    assert first == grid.run_identity("dummy", [])[0]
    assert manifest["parameters"]["random_state"] == 42
    data.write_text("version-two")
    assert first != grid.run_identity("dummy", [])[0]
    assert (
        grid.run_identity("logistic_regression", ["--C", "0.1"])[0]
        != (grid.run_identity("logistic_regression", ["--C", "1"])[0])
    )


@pytest.mark.parametrize("defect", [None, "failed", "params", "metric", "nan", "model", "identity"])
def test_reuse_requires_complete_verified_run(defect):
    run = NS(
        info=NS(status="FINISHED"),
        data=NS(
            tags={"grid_identity": "abc", "protocol": "A", "launched_by": "grid_search"},
            params={"model": "dummy", "random_state": "42"},
            metrics=dict.fromkeys(grid.METRICS, 0.5),
        ),
        outputs=NS(model_outputs=[NS(model_id="model-id")]),
    )
    client = NS(get_logged_model=lambda model_id: NS(status="READY"))
    if defect == "failed":
        run.info.status = "FAILED"
    elif defect == "params":
        run.data.params["random_state"] = "1"
    elif defect == "metric":
        del run.data.metrics["fit_seconds"]
    elif defect == "nan":
        run.data.metrics["roc_auc"] = float("nan")
    elif defect == "model":
        client.get_logged_model = lambda _: NS(status="FAILED")
    elif defect == "identity":
        run.data.tags["grid_identity"] = "different"
    assert grid.reusable(client, run, "abc", {"model": "dummy", "random_state": 42}) == (
        defect is None
    )
