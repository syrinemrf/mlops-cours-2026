"""Tests comportementaux du modèle IBM HR (Lab 3), à la manière de CheckList (Ribeiro et al.).

On teste ce que fait le modèle, pas seulement sa métrique globale :
- performance minimale (MFT) : métrique primaire au gate de dataset.yaml, précision moyenne
  (AP) au-dessus du taux de base (classes déséquilibrées : ~16 % de départs), coût métier
  inférieur aux politiques naïves, seuil de décision documenté, performance par sous-groupe ;
- invariance (INV) : changer un attribut sans effet attendu ne change pas la décision ;
- directionnels (DIR) : une modification ne déplace le risque que dans le sens attendu.
Modèle testé : models/model (dvc repro, ou step train du pipeline), sur data/processed/test.csv,
au seuil de décision du modèle. Les attentes propres au dataset sont dans tests/behavior.yaml.
Sans modèle local (CI), les tests sont ignorés.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.dataset_config import load_config
from src.train import MODEL_DIR, TEST_CSV, compute_metrics

CFG = load_config()
EXPECT = yaml.safe_load(Path(__file__).with_name("behavior.yaml").read_text(encoding="utf-8"))

pytestmark = pytest.mark.skipif(
    not (MODEL_DIR / "MLmodel").exists() or not TEST_CSV.exists(),
    reason="pas de modèle local : dvc pull ou dvc repro (Lab 1)",
)


@pytest.fixture(scope="module")
def model():
    """Le modèle (Pipeline scikit-learn) et son seuil de décision (métadonnées MLflow)."""
    import mlflow
    from mlflow.models import Model

    threshold = Model.load(str(MODEL_DIR)).metadata["decision_threshold"]
    return mlflow.sklearn.load_model(str(MODEL_DIR)), threshold


@pytest.fixture(scope="module")
def data():
    """Features, cible 0/1 et fichier brut du jeu de test (pour les groupes sensibles)."""
    X, y = CFG.read_xy(TEST_CSV)
    return X, y, pd.read_csv(TEST_CSV)


def risk(model, X: pd.DataFrame) -> np.ndarray:
    """Le risque prédit : probabilité de la classe positive de dataset.yaml."""
    return model[0].predict_proba(X)[:, 1]


# --- Performance minimale (MFT) -------------------------------------------------------------
def test_metrique_primaire_au_gate(model, data):
    X, y, _ = data
    value = compute_metrics(CFG, y, risk(model, X), model[1])[CFG.primary_metric]
    assert value >= CFG.promotion_threshold, (
        f"{CFG.primary_metric} = {value:.3f} < {CFG.promotion_threshold}"
    )


def test_precision_moyenne_au_dessus_du_taux_de_base(model, data):
    """AP d'un classement aléatoire = taux de positifs ; le modèle doit faire mieux."""
    X, y, _ = data
    ap = compute_metrics(CFG, y, risk(model, X), model[1])["average_precision"]
    assert ap > y.mean(), f"AP {ap:.3f} <= taux de base {y.mean():.3f}"


def test_seuil_de_decision_documente(model):
    """Le seuil du modèle est celui de behavior.yaml et de la matrice de coûts 1:1."""
    assert model[1] == pytest.approx(EXPECT["decision_threshold"])
    assert model[1] == pytest.approx(CFG.cost_threshold())


def test_cout_metier_inferieur_aux_politiques_naives(model, data):
    """Mieux que « personne ne part » et que « tout le monde part » (matrice de coûts)."""
    X, y, _ = data
    cost = CFG.business_cost(y, risk(model, X) >= model[1])
    naive = min(CFG.business_cost(y, np.zeros(len(y))), CFG.business_cost(y, np.ones(len(y))))
    assert cost < naive, f"coût {cost:.0f} >= coût de la meilleure politique naïve {naive:.0f}"


@pytest.mark.parametrize("attribute", CFG.sensitive, ids=lambda s: s.column)
def test_performance_par_sous_groupe(model, data, attribute):
    X, y, raw = data
    proba, groups = risk(model, X), attribute.groups(raw).to_numpy()
    scores = {}
    for group in np.unique(groups):
        mask = groups == group
        big_enough = mask.sum() >= EXPECT["min_group_size"]
        if big_enough and y[mask].sum() >= EXPECT["min_positives"] and y[mask].nunique() == 2:
            metrics = compute_metrics(CFG, y[mask], proba[mask], model[1])
            scores[group] = round(metrics[CFG.primary_metric], 3)
    if not scores:
        pytest.skip("aucun groupe assez grand")
    below = {g: s for g, s in scores.items() if s < CFG.promotion_threshold}
    assert not below, f"{CFG.primary_metric} < {CFG.promotion_threshold} : {below}"


# --- Invariance (INV) -----------------------------------------------------------------------
@pytest.mark.parametrize("case", EXPECT.get("invariance") or [], ids=lambda c: c["column"])
def test_invariance(model, data, case):
    X, _, _ = data
    col, decision = case["column"], risk(model, X) >= model[1]
    flips = changed = 0
    for value in X[col].unique():  # chaque salarié reçoit chacune des autres valeurs
        modified = X.assign(**{col: value})
        mask = (X[col] != value).to_numpy()
        flips += int(((risk(model, modified) >= model[1]) != decision)[mask].sum())
        changed += int(mask.sum())
    rate = flips / changed
    assert rate <= case["max_flip_rate"], f"{rate:.1%} des décisions changent avec {col}"


# --- Directionnels (DIR) --------------------------------------------------------------------
def modify(X: pd.DataFrame, case: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(avant, après) : colonne x factor, ou modalité `from` remplacée par `to`."""
    col = case["column"]
    if "factor" in case:
        return X, X.assign(**{col: X[col] * case["factor"]})
    before = X[X[col] == case["from"]]
    return before, before.assign(**{col: case["to"]})


def case_id(case: dict) -> str:
    change = f"x{case['factor']}" if "factor" in case else f"{case['from']}->{case['to']}"
    return f"{case['column']}:{change}"


@pytest.mark.parametrize("case", EXPECT.get("directional") or [], ids=case_id)
def test_directionnel(model, data, case):
    X, _, _ = data
    before, after = modify(X, case)
    assert len(before), f"aucun salarié à modifier pour {case_id(case)}"
    delta = risk(model, after) - risk(model, before)
    sign = 1 if case["expect"] == "increase" else -1
    violations = float(np.mean(sign * delta < -EXPECT["tolerance"]))
    assert violations <= EXPECT["max_violation_rate"], (
        f"{violations:.1%} des salariés : risque dans le mauvais sens"
    )
