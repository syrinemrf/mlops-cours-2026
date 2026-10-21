"""Tests de la règle de sélection (src/promote.py) : sans serveur MLflow, runs simulés."""

from types import SimpleNamespace

import pytest

from src import promote

METRIC = "average_precision"


def fake(model, cv, std=0.05, start=0, **params):
    metrics = {
        f"cv_{METRIC}": cv,
        f"cv_{METRIC}_std": std,
        METRIC: cv,
    }
    return SimpleNamespace(
        info=SimpleNamespace(start_time=start, run_name=model),
        data=SimpleNamespace(
            metrics=metrics,
            params={"model": model, **{k: str(v) for k, v in params.items()}},
        ),
    )


@pytest.fixture
def runs():
    return [
        fake("gradient_boosting", 0.64, n_estimators=200, max_depth=3),
        fake("logistic_regression", 0.62, C=1.0),
        fake("logistic_regression", 0.619, C=0.01),
        fake("random_forest", 0.60, n_estimators=100, max_depth=4),
    ]


def test_regle_une_erreur_type_prend_le_plus_simple(runs):
    chosen, reason = promote.select_run(runs, METRIC)
    assert chosen.data.params["model"] == "logistic_regression"
    assert chosen.data.params["C"] == "0.01"  # le plus régularisé des candidats
    assert "3 runs" in reason


def test_regle_best_prend_le_meilleur_score(runs):
    chosen, _ = promote.select_run(runs, METRIC, "best")
    assert chosen.data.params["model"] == "gradient_boosting"


def test_le_modele_naif_n_est_jamais_candidat():
    chosen, _ = promote.select_run(
        [fake("dummy", 0.16), fake("logistic_regression", 0.6, C=1)], METRIC
    )
    assert chosen.data.params["model"] == "logistic_regression"


def test_departage_par_score_puis_recence():
    a = fake("logistic_regression", 0.60, C=1.0, start=1)
    b = fake("logistic_regression", 0.61, C=1.0, start=2)
    assert promote.select_run([a, b], METRIC)[0] is b


def test_repli_sur_la_metrique_de_test():
    run = SimpleNamespace(
        info=SimpleNamespace(start_time=0, run_name="x"),
        data=SimpleNamespace(metrics={METRIC: 0.5}, params={"model": "logistic_regression"}),
    )
    assert promote.score_of(run, METRIC) == 0.5
    assert promote.select_run([run], METRIC)[0] is run


def test_ordre_de_complexite():
    lr_small = fake("logistic_regression", 0.5, C=0.01)
    lr_big = fake("logistic_regression", 0.5, C=10)
    rf_small = fake("random_forest", 0.5, n_estimators=100, max_depth=4)
    rf_deep = fake("random_forest", 0.5, n_estimators=100, max_depth="None")
    gb = fake("gradient_boosting", 0.5, n_estimators=100, max_depth=2)
    ordered = [lr_small, lr_big, rf_small, rf_deep, gb]
    assert sorted(ordered, key=promote.complexity) == ordered


def test_aucun_run_exploitable():
    with pytest.raises(ValueError, match="Aucun run"):
        promote.select_run([], METRIC)
