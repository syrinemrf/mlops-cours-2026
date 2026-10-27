"""Train-only CV: fold preprocessing, coverage, determinism and side effects."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted

from src import cross_validation as cv


def example():
    X = pd.DataFrame(
        {"x": np.arange(60, dtype=float) ** 2, "category": [f"row-{i}" for i in range(60)]},
        index=np.arange(60) * 3 + 1000,
    )
    y = pd.Series([0, 1] * 30, index=X.index)
    preprocessing = ColumnTransformer(
        [
            ("num", StandardScaler(), ["x"]),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["category"]),
        ]
    )
    model = Pipeline(
        [("preprocess", preprocessing), ("model", LogisticRegression(random_state=42))]
    )
    return X, y, model


def test_five_fits_refit_preprocessing_and_cover_each_row_once(monkeypatch):
    X, y, model = example()
    fitted_rows = []
    real_clone = cv.clone

    def observed_clone(original):
        fitted = real_clone(original)
        fit = fitted.fit

        def observed_fit(frame, labels):
            result = fit(frame, labels)
            transform = fitted.named_steps["preprocess"]
            assert transform.named_transformers_["num"].mean_[0] == pytest.approx(frame.x.mean())
            assert set(transform.named_transformers_["cat"].categories_[0]) == set(frame.category)
            fitted_rows.append(set(frame.index))
            return result

        fitted.fit = observed_fit
        return fitted

    monkeypatch.setattr(cv, "clone", observed_clone)
    report, proba = cv.cross_validate_oof(model, X, y, 42)
    assert len(fitted_rows) == report["fits"] == 5
    held_out = [set(X.index) - rows for rows in fitted_rows]
    assert set.union(*held_out) == set(X.index)
    assert all(sum(row in fold for fold in held_out) == 1 for row in X.index)
    assert proba.shape == (60,) and np.isfinite(proba).all()
    assert report["oof_predictions_per_row"] == 1
    assert all(row["validation_rows"] == 12 for row in report["folds"])
    with pytest.raises(NotFittedError):
        check_is_fitted(model)


def test_cv_reproducibility_and_original_metric_interface():
    X, y, model = example()
    first, probabilities = cv.cross_validate_oof(model, X, y, 42)
    second, repeated = cv.cross_validate_oof(model, X, y, 42)
    assert first == second
    np.testing.assert_array_equal(probabilities, repeated)
    assert cv.cross_validate_ranking(model, X, y, 42) == first["summary"]
    assert set(first["summary"]) == {
        "cv_roc_auc",
        "cv_roc_auc_std",
        "cv_average_precision",
        "cv_average_precision_std",
    }
    for metric in cv.CV_METRICS:
        scores = [row[metric] for row in first["folds"]]
        assert first["summary"][f"cv_{metric}"] == pytest.approx(np.mean(scores))
        assert first["summary"][f"cv_{metric}_std"] == pytest.approx(np.std(scores, ddof=0))
    assert (
        first["fold_assignments_sha256"]
        != cv.cross_validate_oof(model, X, y, 43)[0]["fold_assignments_sha256"]
    )


@pytest.mark.parametrize(
    "labels,probabilities",
    [
        ([0, 1], [0.2]),
        ([0, 0], [0.2, 0.3]),
        ([0, 2], [0.2, 0.3]),
        ([0, 1], [np.nan, 0.3]),
        ([0, 1], [-0.1, 0.3]),
        ([0, 1], [0.2, 1.1]),
        ([], []),
        ([[0, 1]], [[0.2, 0.3]]),
    ],
)
def test_reject_invalid_predictions(labels, probabilities):
    with pytest.raises(ValueError):
        cv.validate_predictions(labels, probabilities)


def test_reject_insufficient_class_counts_and_misaligned_frame():
    X, _, model = example()
    with pytest.raises(ValueError, match="five"):
        cv.cross_validate_oof(model, X.iloc[:8], [0, 1] * 4, 42)
    with pytest.raises(ValueError, match="aligned"):
        cv.cross_validate_oof(model, X.iloc[:10], [0, 1] * 10, 42)


def test_fold_fit_error_is_not_hidden(monkeypatch):
    X, y, model = example()

    def failed_fit(*args):
        raise RuntimeError("intentional fit failure")

    monkeypatch.setattr(
        cv,
        "clone",
        lambda original: SimpleNamespace(
            get_params=lambda: {}, set_params=lambda **kwargs: None, fit=failed_fit
        ),
    )
    with pytest.raises(RuntimeError, match="intentional"):
        cv.cross_validate_oof(model, X, y, 42)


def test_analysis_reads_train_only_and_never_starts_mlflow(tmp_path, monkeypatch):
    X, y, model = example()
    train = tmp_path / "train.csv"
    train.write_text("synthetic training fingerprint")
    reads = []

    def read_xy(path):
        assert path == train
        reads.append(path)
        return X, y

    cfg = SimpleNamespace(
        name="synthetic", features=list(X), read_xy=read_xy, cost_threshold=lambda k: 0.5
    )
    monkeypatch.setattr(cv, "TRAIN_CSV", train)
    monkeypatch.setattr(cv, "load_config", lambda: cfg)
    monkeypatch.setattr(cv, "build_model", lambda *args: model)

    def forbidden(*args, **kwargs):
        raise AssertionError("MLflow must not be used by train diagnostics")

    monkeypatch.setattr("mlflow.start_run", forbidden)
    report, labels, probabilities, threshold = cv.evaluate_training()
    assert reads == [train]
    assert len(labels) == len(probabilities) == 60
    assert threshold == 0.5
    assert report["promotion_eligible"] is False
    assert report["test_used"] is False
    assert report["official_model_modified"] is False
