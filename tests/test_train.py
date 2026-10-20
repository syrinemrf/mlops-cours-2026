"""Protocol A: threshold, decisions and preprocessing must use training data only."""

import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError

from src import train
from src.dataset_config import load_config


def test_threshold_uses_training_prevalence_only():
    cfg = load_config()
    y_train = pd.Series([0] * 986 + [1] * 190)
    assert train.decision_threshold(cfg, "balanced", y_train) == pytest.approx(986 / 1176)
    assert train.decision_threshold(cfg, None, y_train) == 0.5


def test_decisions_and_ranking_metrics_are_distinct():
    cfg = load_config()
    metrics = train.compute_metrics(cfg, [0, 0, 1, 1], [0.1, 0.8, 0.4, 0.9], 0.5)
    assert metrics == pytest.approx(
        dict(
            tn=1,
            fp=1,
            fn=1,
            tp=1,
            roc_auc=0.75,
            average_precision=5 / 6,
            precision=0.5,
            recall=0.5,
            f1=0.5,
            accuracy=0.5,
            business_cost=2,
        )
    )
    higher = train.compute_metrics(cfg, [0, 0, 1, 1], [0.1, 0.8, 0.4, 0.9], 0.95)
    assert higher["roc_auc"] == metrics["roc_auc"]
    assert higher["average_precision"] == metrics["average_precision"]
    assert higher["precision"] == higher["recall"] == higher["f1"] == 0


@pytest.mark.parametrize(
    "model_type,params",
    [
        ("logistic_regression", {"C": 0.1, "class_weight": "balanced"}),
        ("random_forest", {"n_estimators": 2, "max_depth": 2, "class_weight": "balanced"}),
        ("gradient_boosting", {"n_estimators": 2, "max_depth": 2, "learning_rate": 0.1}),
        ("dummy", {}),
    ],
)
def test_pipeline_fits_train_only_and_accepts_unseen_categories(model_type, params):
    cfg = load_config()
    frame = pd.DataFrame({c: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] for c in cfg.numeric})
    for c in cfg.categorical:
        frame[c] = ["a", "b"] * 3
    frame[cfg.target] = ["Yes", "No"] * 3
    frame["Age"] = 30
    frame["Gender"] = "Female"
    frame["MaritalStatus"] = "Single"
    frame["EmployeeNumber"] = range(6)
    X, y = cfg.split_xy(frame)
    assert list(X) == cfg.features
    assert not {cfg.target, "EmployeeNumber", "Age", "Gender", "MaritalStatus"} & set(X)
    model = train.build_model(cfg, model_type, params, 42)
    with pytest.raises(NotFittedError):
        model.predict_proba(X)
    model.fit(X, y)
    test = X.copy()
    test[cfg.numeric[0]] = 10000.0
    test[cfg.categorical[0]] = "unseen-test-only"
    preprocess = model.named_steps["preprocess"]
    before = preprocess.transform(X).copy()
    probabilities = model.predict_proba(test)
    assert probabilities.shape == (6, 2)
    np.testing.assert_allclose(probabilities.sum(axis=1), 1)
    np.testing.assert_array_equal(preprocess.transform(X), before)
    assert "unseen-test-only" not in str(preprocess)
