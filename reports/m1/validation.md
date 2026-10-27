# Validation du premier incrément IBM HR — 2026-10-19

## Périmètre

Base : fusion M0 `7606b83` sur origin/main ; branche personnelle `work/syrine/m1`.
Arbre initial propre, aucun AGENTS.md applicable trouvé. Aucun push, PR ou fusion
à cette étape. Les anciens commits restent intacts. M1 complet non validé.

## Commandes réellement exécutées

| Vérification | Résultat |
|---|---|
| API publique Kaggle view et téléchargement version 1 | Réussis sans authentification ni miroir |
| `uv run --no-sync python -m src.download` | Réussi : empreinte épinglée identique, source 1470 × 35, export 1470 × 32 |
| `uv run --no-sync python -m src.download --from-file /tmp/ibm-hr-v1.zip` | Réussi : même empreinte export `27e7bebda91c7e6d0b77e80128c2d9383d70a19a185b51ecfe3bb90f761d2a78` |
| `load_config()`, `validate_columns`, `split_xy`, `sensitive_frame` sur l’export réel | Réussis ; 27 features, 237 positifs ; sensibles disponibles sans groupe nan |
| Contrôles source et export | 0 valeur manquante, 0 doublon ; ID unique ; trois constantes attendues ; types/domaines vérifiés |
| Split en mémoire avec la formule stratifiée de l’énoncé | 1176/294 lignes, 190/47 positifs, 0 ID commun |
| `pytest -q tests/test_hr_download.py tests/test_dataset_config.py` | **31 passed, 1 failed** ; détail ci-dessous |
| `pytest -q tests/test_hr_download.py` | **23 passed** ; log conservé dans targeted-tests.log |
| `ruff check src/download.py tests/test_hr_download.py` | Réussi |
| `ruff format --check src/download.py tests/test_hr_download.py` | Réussi : 2 fichiers formatés |
| `yamllint -c .yamllint.yaml dataset.yaml` | Réussi |
| `git diff --check`, exclusions Git des données et secrets | Réussis |

Commandes Python exécutées dans le venv Python 3.12 du cours (`uv run --no-sync`,
cache uv temporaire) ; aucune dépendance/version modifiée.
Le script d’audit temporaire a produit `ingestion-validation.json` à partir du CSV
réel, sans entraîner de modèle ni écrire de train/test persistants.

## Échec officiel conservé et expliqué

`tests/test_dataset_config.py::test_sensible_hors_features` exécute :

```python
data["features"]["categorical"].remove("personal_status")
```

Ce nom appartient au German Credit, pas à IBM HR ; l’erreur est
`ValueError: list.remove(x): x not in list`. Le test officiel est inchangé, sans
skip ni xfail, et la suite complète n’est pas annoncée verte. Les 8 autres tests
existants passent. Le test ciblé `test_export_separates_predictors_sensitive_and_identifier`
vérifie la même propriété sur les trois sensibles RH réels, leur présence hors
features, le lecteur d’équité et l’absence d’identifiant dans X.
À signaler au professeur : rendre à terme ce test générique via une fixture dédiée
ou une colonne sensible du contrat, dans un correctif séparé et autorisé.

## Limites et suite

L’empreinte source est une ancre calculée au premier téléchargement, puis épinglée
et revérifiée ; aucune preuve indépendante d’authenticité revendiquée.
Les coûts 1:1, la gate 0.70 et les choix de groupes/exclusion sont proposés pour
validation métier. Aucun grid search, promotion, Kubeflow, modification de cluster,
configuration DVC ou `make check-m1` complet à cette étape.

Étape suivante : DVC avec remote `s3://dvc-store/scoring`, dépendance du download à
la section `source` de dataset.yaml, puis params/prepare avec EmployeeNumber comme
identifiant, split stratifié et prétraitements ajustés exclusivement sur le train.
