"""Valide le modèle entraîné avant son enregistrement (gate du Lab 3).

    python -m src.validate_model      (models/model, data/processed/train.csv et test.csv)

1. Evidently (ClassificationPreset) sur le jeu de test, au seuil de décision du modèle
   (0,5 pour les coûts 1:1), avec le jeu d'entraînement en référence et deux tests :
   - la métrique primaire de dataset.yaml atteint promotion_threshold (gate ROC AUC 0,70) ;
   - la ROC AUC de test ne s'écarte pas de plus de 20 % de celle d'entraînement
     (sur-apprentissage).
2. Les tests comportementaux de tests/test_model_behavior.py (pytest) : AP > taux de base,
   seuil documenté, sous-groupes, invariance, directionnels (tests/behavior.yaml).
Classes déséquilibrées (~16 % de départs) : la précision moyenne (AP) et la courbe
précision-rappel sont rapportées à côté de la ROC AUC (reports/model_validation_pr.html).
Code retour 1 si un test échoue. Sorties : reports/model_validation.json, .md, .html.
"""

import json
from pathlib import Path
from xml.etree import ElementTree

import mlflow
import numpy as np
import pandas as pd
import pytest
from mlflow.models import Model
from sklearn.metrics import precision_recall_curve

from src.dataset_config import DatasetConfig, load_config
from src.train import MODEL_DIR, TEST_CSV, TRAIN_CSV, compute_metrics

ROOT = Path(__file__).resolve().parents[1]
BEHAVIOR_TESTS = ROOT / "tests" / "test_model_behavior.py"
REPORT_JSON = Path("reports/model_validation.json")
REPORT_MD = Path("reports/model_validation.md")
REPORT_HTML = Path("reports/model_validation.html")
REPORT_PR = Path("reports/model_validation_pr.html")
JUNIT_XML = Path("reports/model_behavior.xml")
MAX_TRAIN_TEST_GAP = 0.2  # écart relatif de ROC AUC toléré entre entraînement et test
# Métriques de dataset.yaml que le preset sait tester (nom de l'argument « <x>_tests »)
EVIDENTLY_NAMES = {
    "roc_auc": "rocauc",
    "f1": "f1score",
    "precision": "precision",
    "recall": "recall",
    "accuracy": "accuracy",
}
PRESET_METRICS = ["accuracy", "precision", "recall", "f1score", "rocauc", "logloss",
                  "tpr", "tnr", "fpr", "fnr"]  # fmt: skip


def evidently_checks(cfg: DatasetConfig, model, threshold: float) -> list:
    """Rapport Evidently (HTML) et résultat de ses tests."""
    from evidently import BinaryClassification, DataDefinition, Dataset, Report
    from evidently.presets import ClassificationPreset
    from evidently.tests import Reference, eq, gte

    definition = DataDefinition(
        classification=[BinaryClassification(target="target", prediction_probas="proba",
                                             pos_label=1)]
    )  # fmt: skip

    def dataset(path: Path) -> Dataset:
        X, y = cfg.read_xy(path)
        frame = pd.DataFrame({"target": y.to_numpy(), "proba": model.predict_proba(X)[:, 1]})
        return Dataset.from_pandas(frame, data_definition=definition)

    # Tests explicites seulement : une liste vide désactive les tests par défaut d'Evidently
    # (« mieux qu'un modèle naïf » sur l'accuracy), trompeurs à 84 % de « No » : le modèle
    # qui prédit toujours « No » a déjà 84 % d'accuracy.
    tests = {f"{name}_tests": [] for name in PRESET_METRICS}
    tests["rocauc_tests"] = [eq(Reference(relative=MAX_TRAIN_TEST_GAP))]  # vs entraînement
    if cfg.primary_metric in EVIDENTLY_NAMES:
        name = EVIDENTLY_NAMES[cfg.primary_metric]
        tests[f"{name}_tests"].append(gte(cfg.promotion_threshold))

    report = Report([ClassificationPreset(probas_threshold=threshold, **tests)])
    snapshot = report.run(dataset(TEST_CSV), dataset(TRAIN_CSV))  # courant, référence
    REPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    snapshot.save_html(str(REPORT_HTML))
    return [
        {"name": t["name"], "success": getattr(t["status"], "value", t["status"]) == "SUCCESS"}
        for t in snapshot.dict()["tests"]
    ]


def behavior_checks() -> list:
    """Lance pytest sur les tests comportementaux ; un résultat par test (rapport JUnit)."""
    JUNIT_XML.parent.mkdir(parents=True, exist_ok=True)
    quiet = ["-q", "-p", "no:cacheprovider", "-W", "ignore::pytest.PytestAssertRewriteWarning"]
    code = pytest.main([*quiet, str(BEHAVIOR_TESTS), f"--junitxml={JUNIT_XML}"])
    if code not in (pytest.ExitCode.OK, pytest.ExitCode.TESTS_FAILED):
        return [{"name": f"pytest : code retour {int(code)}", "success": False}]
    return [
        {
            "name": case.get("name"),
            "success": case.find("failure") is None and case.find("error") is None,
            "skipped": case.find("skipped") is not None,
        }
        for case in ElementTree.parse(JUNIT_XML).getroot().iter("testcase")
    ]


def pr_curve_html(y, proba, threshold: float, ap: float, path: Path) -> None:
    """Courbe précision-rappel autonome (SVG inline), avec le taux de base et le seuil."""
    precision, recall, thresholds = precision_recall_curve(y, proba)
    w, h, pad = 420, 320, 40

    def xy(r: float, p: float) -> str:
        return f"{pad + r * (w - 2 * pad):.1f},{h - pad - p * (h - 2 * pad):.1f}"

    points = " ".join(xy(r, p) for r, p in zip(recall, precision, strict=True))
    base = float(np.mean(y))
    i = int(np.argmin(np.abs(thresholds - threshold)))  # point de fonctionnement
    op = xy(recall[i], precision[i]).split(",")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>Courbe précision-rappel</title><style>body{{font-family:sans-serif;margin:2em}}</style>
</head><body><h1>Courbe précision-rappel (test)</h1>
<p>AP = {ap:.4f} ; taux de base (AP d'un classement aléatoire) = {base:.4f} ;
seuil {threshold:g} : précision {precision[i]:.3f}, rappel {recall[i]:.3f}.</p>
<svg width="{w}" height="{h}" role="img" aria-label="Courbe précision-rappel">
<rect x="{pad}" y="{pad}" width="{w - 2 * pad}" height="{h - 2 * pad}" fill="none" stroke="#999"/>
<line x1="{xy(0, base).split(",")[0]}" y1="{xy(0, base).split(",")[1]}"
 x2="{xy(1, base).split(",")[0]}" y2="{xy(1, base).split(",")[1]}"
 stroke="#999" stroke-dasharray="4"/>
<polyline points="{points}" fill="none" stroke="#1f6feb" stroke-width="2"/>
<circle cx="{op[0]}" cy="{op[1]}" r="5" fill="#cf222e"/>
<text x="{w / 2}" y="{h - 8}" text-anchor="middle">rappel</text>
<text x="12" y="{h / 2}" transform="rotate(-90 12 {h / 2})" text-anchor="middle">précision</text>
</svg></body></html>
""",
        encoding="utf-8",
    )


def markdown(summary: dict) -> str:
    """Tableau des tests (affiché par l'UI Kubeflow)."""
    lines = [
        f"### Validation du modèle : {summary['n_failed']} échec(s) sur {summary['n_checks']}",
        "",
        f"ROC AUC {summary['roc_auc']} ; AP {summary['average_precision']} "
        f"(taux de base {summary['base_rate']}) ; seuil {summary['decision_threshold']}",
        "",
        "| Famille | Test | Statut |",
        "|---|---|---|",
    ]
    for family in ("evidently", "behavior"):
        for c in summary[family]:
            status = "ignoré" if c.get("skipped") else ("OK" if c["success"] else "ÉCHEC")
            lines.append(f"| {family} | {c['name']} | {status} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    cfg = load_config()
    model = mlflow.sklearn.load_model(str(MODEL_DIR))
    threshold = Model.load(str(MODEL_DIR)).metadata["decision_threshold"]
    X, y = cfg.read_xy(TEST_CSV)
    proba = model.predict_proba(X)[:, 1]
    metrics = compute_metrics(cfg, y, proba, threshold)
    pr_curve_html(y, proba, threshold, metrics["average_precision"], REPORT_PR)

    evidently, behavior = evidently_checks(cfg, model, threshold), behavior_checks()
    failed = [c["name"] for c in [*evidently, *behavior] if not c["success"]]
    summary = {
        "success": not failed,
        "n_checks": len(evidently) + len(behavior),
        "n_failed": len(failed),
        "failed": failed,
        cfg.primary_metric: round(float(metrics[cfg.primary_metric]), 4),
        "roc_auc": round(float(metrics["roc_auc"]), 4),
        "average_precision": round(float(metrics["average_precision"]), 4),
        "base_rate": round(float(y.mean()), 4),
        "decision_threshold": round(threshold, 4),
        "evidently": evidently,
        "behavior": behavior,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", "utf-8")
    REPORT_MD.write_text(markdown(summary), encoding="utf-8")
    print(markdown(summary))
    print("Modèle VALIDÉ" if not failed else f"Modèle REFUSÉ : {failed}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
