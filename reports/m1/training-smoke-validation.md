# M1 — deux smoke tests du protocole A

Date : 2026-10-20. Branche work/syrine/m1. Code exécuté : `48c354e734e773dc88302f2906875566bc6b45a6`.

## Périmètre et commandes réellement exécutées

Après validation de la séparation A/B1/B2 et documentation des quatre constats Jia,
exécution séquentielle des deux commandes de §4.5, via `uv run --no-sync`, avec .env
chargé localement et OPENBLAS_NUM_THREADS/OMP_NUM_THREADS/MKL_NUM_THREADS=1 :

```bash
python -m src.train
python -m src.train --model random_forest --n_estimators 50 --max_depth 5
```

Expérience scoring (ID 2), tags protocol_id=mlops_A_v1 et
evaluation_role=pedagogical_smoke_test. Les deux runs sont FINISHED.
Train/test stratifiés existants : 1176/294 ; 190/47 positifs. 27 prédicteurs.
Aucune ingestion rejouée ni préparation modifiée. Les cinq commits M1 sont conservés.

## Mesures réellement enregistrées

| Modèle | ROC AUC | AP | Precision | Recall | F1 | Accuracy | Coût FN+FP | TN/FP/FN/TP |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| logistic_regression | 0.832974 | 0.639213 | 0.823529 | 0.297872 | 0.437500 | 0.877551 | 36 | 244/3/33/14 |
| random_forest | 0.784564 | 0.442840 | 0.500000 | 0.021277 | 0.040816 | 0.840136 | 47 | 246/1/46/1 |

AP désigne average_precision_score, pas une intégrale trapézoïdale PR-AUC.
Seuil de décision conservé : **0.8384353741496599**, calculé sur train :
k=986/190, C_FN=C_FP=1, seuil=k/(k+1). Les coûts sont expérimentaux neutres.
Cette heuristique balanced du cours ne prouve pas la calibration des modèles.
Elle donne ici un rappel particulièrement faible pour RF : 1 départ détecté sur 47.
Aucun seuil ajusté sur le test. La gate ROC AUC 0.70 reste inchangée ; la dépasser
sur ces smoke tests ne constitue ni une promotion ni une validation complète M1.

Ces évaluations exposent le test A et restent pédagogiques/exploratoires. Pas de
comparaison d’amélioration avec Jia : split et variables différents. Tests B1/B2
non évalués. Aucun entraînement auteur, calibration, grid search ou promotion.

## Runs et artefacts

- logistic_regression : run `aa859327feef485ebad8d4992f558a3e`, modèle `m-c5336dddd46942ed92b6d84d302da8b0`.
- random_forest : run `c944848ce3b44a2da935c28156f0abc6`, modèle `m-cbdd6e2f66724e658480f93ca0e24989`.

Pipeline sklearn complet enregistré en skops sur MLflow, signature 27 entrées,
exemple issu du train. Rechargement des deux modèles depuis MLflow réussi ; toutes
les métriques recalculées identiques à 1e-12 près. Métadonnée du seuil concordante.
Rechargement des deux copies locales également réussi : RF dans models/model,
LR préservée dans models/smoke-history. Aucun artefact précédent supprimé.
Identifiant, cible et Age/Gender/MaritalStatus vérifiés absents des entrées.
Hashes des contrats, lockfiles et splits, paramètres, tags et résultats complets :
[smoke-validation.json](smoke-validation.json). Aucune ligne de donnée dans ce JSON.

## Tests, qualité et écarts explicites au modèle de l’énoncé

- `uv run --no-sync pytest -q` : **51 passed in 11.51s** (45 existants + 6 cas nouveaux).
- `make lint` : ruff check, ruff format (39 fichiers), yamllint réussis.
- Tests synthétiques : seuil train uniquement, métriques/confusion connues et zéro
  prédiction positive, quatre familles de pipelines, catégories test inconnues,
  stabilité du prétraitement après prédiction et séparation des colonnes.
- Diff et exclusions Git vérifiés : seuls les .gitignore sont suivis sous data/models ;
  .env et .dvc/config.local restent ignorés. Aucun vérificateur officiel modifié.
- Diff par rapport au code §4.3 : tags de protocole et hashes supplémentaires ;
  confusion enregistrée ; seuil loggé en précision complète ; exemple/signature du
  train plutôt que du test ; conservation de l’ancien modèle local plutôt que suppression.
  Les conventions scoring/scoring-model/s3://dvc-store/scoring sont préservées.
- Warning réel MLflow : pip absent de la venv uv ; pip non épinglé dans conda.yaml
  généré. Pas bloquant pour les rechargements testés. Les quatre dépendances du modèle
  sont épinglées ; reconstruction complète via conda non testée. Aucun changement de uv.lock.
- Cluster existant accessible, MLflow /health OK ; aucune recréation ni suppression de volume.

Logs : [LR](smoke-logistic.log), [RF](smoke-random-forest.log).

## Arrêt et prochaine étape

Arrêt après ces deux smoke tests, conformément à la demande. Pas de make check-m1
à cette étape : les étapes suivantes du lab restent incomplètes. Prochaine étape,
après revue des résultats par Syrine : cadrer la sélection interne au train et
l’instrumentation de la suite pédagogique avant toute autorisation du grid search.
Les expériences B1/B2 nécessitent encore un environnement/budget séparé autorisé ;
la référence exacte XP-Cube et la revue de littérature restent à compléter.
