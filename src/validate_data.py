"""Valide un fichier de données contre le contrat Great Expectations du projet (gx/).

Gate du pipeline (Labs 2 et 3) : si une expectation échoue, le script sort avec le code 1
et l'orchestrateur (DVC, Kubeflow, Airflow, CI) s'arrête AVANT la préparation. Le Lab 3
remplace les contrôles simples du Lab 2 par une suite Great Expectations, sans changer la
façon de lancer le script :

    python -m src.validate_data [fichier.csv]     (défaut : raw_path de dataset.yaml)
    python -m src.validate_data --build-suite     ((ré)écrit la suite dans gx/)

Contrat IBM HR (fiche : docs/dataset-card.md) :
- la suite est GÉNÉRÉE depuis dataset.yaml (rôles des colonnes) et data/processed/train.csv
  (domaines observés) : split d'abord, statistiques ensuite, rien n'est appris sur le test ;
- le rôle d'une colonne vient du contrat, pas de son dtype : les ordinales IBM HR
  (« 3: Bachelor », « 2: Level 2 »…) sont contrôlées par ensemble de modalités ;
- règles métier d'ancienneté (A >= B) et unicité de l'identifiant : section validation de
  params.yaml. La suite est versionnée : elle ne change que si on la régénère.
Sorties : résumé JSON (sortie standard et reports/validation.json), rapport HTML autonome
(reports/validation.html) et Data Docs (gx/uncommitted/data_docs/local_site/index.html).
"""

import argparse
import html
import json
import sys
from pathlib import Path

import great_expectations as gx
import pandas as pd
import yaml
from great_expectations.data_context.types.base import ProgressBarsConfig

from src.dataset_config import DatasetConfig, load_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # gx/ est à la racine du projet
SUITE = "scoring_contract"  # gx/expectations/scoring_contract.json
CHECKPOINT = "scoring_gate"  # gx/checkpoints/scoring_gate.json
REFERENCE_CSV = Path("data/processed/train.csv")  # train uniquement (src/prepare.py)
REPORT_JSON = Path("reports/validation.json")
REPORT_HTML = Path("reports/validation.html")
NUMERIC_TYPES = ["int64", "int32", "float64", "float32", "Int64", "Float64"]
TEXT_TYPES = ["object", "str", "string", "category"]


def load_rules(path: Path = Path("params.yaml")) -> dict:
    """Section validation de params.yaml, et l'identifiant technique (section prepare)."""
    params = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = dict(params.get("validation") or {})
    rules.setdefault("mostly", 0.99)
    rules.setdefault("column_pairs", [])
    rules["id_column"] = (params.get("prepare") or {}).get("id_column")
    return rules


def column_roles(cfg: DatasetConfig, ref: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Numériques et catégorielles selon le CONTRAT (sensibles : selon leurs données)."""
    numeric = [*cfg.numeric]
    numeric += [c for c in cfg.extra_sensitive if pd.api.types.is_numeric_dtype(ref[c])]
    categorical = [c for c in cfg.columns if c not in numeric and c != cfg.target]
    return numeric, categorical


# --------------------------------------------------------------- construire la suite
def build_expectations(cfg: DatasetConfig, ref: pd.DataFrame, rules: dict) -> list:
    """Le contrat de données, déduit de dataset.yaml, de params.yaml et de train.csv."""
    E = gx.expectations
    expectations = []
    add = expectations.append
    mostly = float(rules["mostly"])
    numeric, categorical = column_roles(cfg, ref)

    # 1. Structure : colonnes du contrat présentes ; lot non tronqué
    add(E.ExpectTableColumnsToMatchSet(column_set=cfg.columns, exact_match=False))
    add(E.ExpectTableRowCountToBeBetween(min_value=max(1, len(ref) // 10)))
    id_col = rules.get("id_column")
    if id_col and id_col in ref.columns:  # identifiant technique : une ligne par salarié
        add(E.ExpectColumnValuesToBeUnique(column=id_col))

    # 2. Chaque colonne : remplie comme à l'entraînement, et du type attendu par son rôle
    for col in cfg.columns:
        null_rate = float(ref[col].isna().mean())  # 0 : aucune valeur manquante tolérée
        kwargs = {"mostly": round(max(0.0, 1 - 2 * null_rate), 3)} if null_rate else {}
        add(E.ExpectColumnValuesToNotBeNull(column=col, **kwargs))
        types = NUMERIC_TYPES if col in numeric else TEXT_TYPES
        add(E.ExpectColumnValuesToBeInTypeList(column=col, type_list=types))

    # 3. Numériques : bornes larges (même signe, au plus deux fois l'étendue observée).
    #    Elles attrapent les erreurs grossières (unité, signe) ; les variations naturelles
    #    relèvent de la détection de drift (src/detect_drift.py), pas du contrat.
    for col in numeric:
        lo, hi = float(ref[col].min()), float(ref[col].max())
        span = hi - lo
        add(
            E.ExpectColumnValuesToBeBetween(
                column=col,
                min_value=0.0 if lo >= 0 else lo - span,
                max_value=hi + span,
                mostly=mostly,
            )
        )

    # 4. Catégorielles et ordinales : modalités vues à l'entraînement (une autre serait
    #    ignorée en silence par le OneHotEncoder(handle_unknown="ignore") du modèle)
    for col in categorical:
        observed = sorted(ref[col].dropna().unique().tolist(), key=str)
        add(E.ExpectColumnValuesToBeInSet(column=col, value_set=observed, mostly=mostly))

    # 5. Règles métier (params.yaml) : A >= B, ex. ancienneté totale >= ancienneté maison
    for a, b in rules["column_pairs"]:
        add(
            E.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=a, column_B=b, or_equal=True, mostly=mostly,
                description=f"Règle métier : {a} >= {b}",
            )
        )  # fmt: skip

    # 6. Cible : classes connues ; part de la classe positive entre la moitié et le double
    #    de celle de l'entraînement (classes déséquilibrées : ~16 % de départs)
    classes = sorted(ref[cfg.target].dropna().unique().tolist(), key=str)
    positive = [c for c in classes if str(c) == str(cfg.positive_class)]
    others = [c for c in classes if str(c) != str(cfg.positive_class)]
    rate = float(cfg.encode_target(ref[cfg.target]).mean())
    add(E.ExpectColumnValuesToBeInSet(column=cfg.target, value_set=classes))
    add(
        E.ExpectColumnValuesToBeInSet(
            column=cfg.target,
            value_set=positive,
            mostly=round(rate / 2, 3),
            description=f"Au moins {rate / 2:.1%} de « {cfg.positive_class} »",
        )
    )
    add(
        E.ExpectColumnValuesToBeInSet(
            column=cfg.target,
            value_set=others,
            mostly=round(max(0.0, 1 - 2 * rate), 3),
            description=f"Au plus {min(1.0, 2 * rate):.1%} de « {cfg.positive_class} »",
        )
    )
    return expectations


def save_suite(expectations: list) -> gx.ExpectationSuite:
    """Écrit dans gx/ la suite, sa source (pandas), la validation et le checkpoint."""
    context = gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)  # crée gx/
    context.enable_analytics(False)  # aucune télémétrie envoyée à GX
    context.variables.progress_bars = ProgressBarsConfig(globally=False)
    context.variables.save()
    # Source « pandas » : le DataFrame est fourni à chaque exécution (batch_parameters)
    batch = (
        context.data_sources.add_or_update_pandas("scoring")
        .add_dataframe_asset("dataframe")
        .add_batch_definition_whole_dataframe("full")
    )
    suite = context.suites.add_or_update(gx.ExpectationSuite(name=SUITE, expectations=expectations))
    definition = context.validation_definitions.add_or_update(
        gx.ValidationDefinition(name=SUITE, data=batch, suite=suite)
    )
    context.checkpoints.add_or_update(
        gx.Checkpoint(
            name=CHECKPOINT,
            validation_definitions=[definition],
            actions=[gx.checkpoint.UpdateDataDocsAction(name="data_docs")],
            result_format={"result_format": "SUMMARY"},
        )
    )
    return suite


# --------------------------------------------------------------------- valider
def validate(cfg: DatasetConfig, df: pd.DataFrame):
    """Lance le checkpoint versionné sur df ; renvoie le résultat de la validation."""
    if not (PROJECT_ROOT / "gx" / "checkpoints" / f"{CHECKPOINT}.json").exists():
        raise SystemExit("Suite absente : lancez python -m src.validate_data --build-suite")
    missing = [c for c in cfg.columns if c not in df.columns]
    if missing:
        print(f"Colonnes déclarées dans dataset.yaml absentes : {missing}", file=sys.stderr)
    context = gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)
    result = context.checkpoints.get(CHECKPOINT).run(batch_parameters={"dataframe": df})
    return next(iter(result.run_results.values()))


def check_name(r) -> str:
    """Nom lisible : type(colonne ou colonnes), et la description s'il y en a une."""
    config = r.expectation_config
    kw = config.kwargs
    cols = kw.get("column") or ", ".join(filter(None, [kw.get("column_A"), kw.get("column_B")]))
    name = config.type + (f"({cols})" if cols else "")
    return f"{name} : {config.description}" if config.description else name


def run_checks(cfg: DatasetConfig, df: pd.DataFrame) -> dict[str, bool]:
    """Un booléen par expectation de la suite (True = conforme au contrat)."""
    return {check_name(r): bool(r.success) for r in validate(cfg, df).results}


def expected(r) -> str:
    """Les paramètres de l'expectation : bornes, ensemble de valeurs, tolérance…"""
    skip = ("column", "column_A", "column_B", "batch_id")
    kwargs = r.expectation_config.kwargs
    return ", ".join(f"{k}={str(v)[:80]}" for k, v in kwargs.items() if k not in skip)


def observed(r) -> str:
    """Ce que GX a observé : valeur, ou nombre et exemples de valeurs hors contrat."""
    if not r.success and r.exception_info.get("raised_exception"):
        return "erreur : " + str(r.exception_info.get("exception_message"))[:150]
    res = r.result or {}
    if "unexpected_count" in res:
        sample = ", ".join(map(str, (res.get("partial_unexpected_list") or [])[:5]))
        text = f"{res['unexpected_count']} hors contrat ({res['unexpected_percent']:.1f} %)"
        return f"{text} : {sample}…" if sample and not r.success else text
    return str(res.get("observed_value", ""))


def write_html(results, summary: dict, path: Path) -> None:
    """Rapport HTML autonome (un seul fichier) : affiché par l'UI Kubeflow."""
    rows = "".join(
        f"<tr class='{'ok' if r.success else 'ko'}'><td>{html.escape(check_name(r))}</td>"
        f"<td>{html.escape(expected(r))}</td><td>{html.escape(observed(r))}</td>"
        f"<td>{'OK' if r.success else 'ÉCHEC'}</td></tr>\n"
        for r in sorted(results, key=lambda r: r.success)  # les échecs en premier
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Validation des données</title>
<style>body{{font-family:sans-serif;margin:2em}} table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:4px 8px;text-align:left}}
.ok td:last-child{{color:#1a7f37}} .ko td:last-child{{color:#cf222e;font-weight:bold}}</style>
</head><body><h1>Suite {SUITE} : {summary["n_failed"]} échec(s) sur {summary["n_checks"]}</h1>
<p>{summary["rows"]} lignes, part de la classe positive : {summary["positive_rate"]}</p>
<table><tr><th>Expectation</th><th>Attendu</th><th>Observé</th><th>Statut</th></tr>
{rows}</table>
</body></html>
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", nargs="?", help="fichier à valider (défaut : raw_path)")
    parser.add_argument(
        "--build-suite",
        action="store_true",
        help=f"(ré)écrit la suite depuis dataset.yaml et csv (défaut : {REFERENCE_CSV})",
    )
    args = parser.parse_args()
    cfg = load_config()

    if args.build_suite:
        ref = pd.read_csv(args.csv or REFERENCE_CSV)
        suite = save_suite(build_expectations(cfg, ref, load_rules()))
        print(f"Suite {SUITE} : {len(suite.expectations)} expectations -> gx/expectations/")
        return 0

    df = pd.read_csv(args.csv or cfg.raw_path)
    results = validate(cfg, df).results
    failed = [check_name(r) for r in results if not r.success]
    has_target = cfg.target in df.columns and len(df) > 0
    summary = {
        "success": not failed,
        "n_checks": len(results),
        "n_failed": len(failed),
        "failed": failed,
        "rows": len(df),
        "positive_rate": round(float(cfg.encode_target(df[cfg.target]).mean()), 4)
        if has_target
        else None,
        "suite": SUITE,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", "utf-8")
    write_html(results, summary, REPORT_HTML)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
