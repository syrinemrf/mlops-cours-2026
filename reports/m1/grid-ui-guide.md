# Comparaison MLflow — étape 6, sans promotion

Ouvrir http://localhost:5000, expérience **scoring** (ID 2).
Filtrer avec `tags.launched_by = 'grid_search' AND tags.protocol = 'A'`.
Attendu : 22 configurations terminées, plus 2 smoke tests hors filtre.

Afficher les colonnes model, C, class_weight, n_estimators, max_depth, learning_rate,
random_state, decision_threshold ; métriques roc_auc, average_precision,
pr_auc_trapezoidal, precision, recall, f1, accuracy, business_cost, fit_seconds ;
tags protocol, data_version, data_md5, grid_identity, evaluation_role, launched_by.

Trier par roc_auc pour explorer, puis cocher une LR, une RF et un GB ; ouvrir
**Compare** et examiner Parameters, Metrics et Parallel Coordinates. Ajouter Dummy
pour situer le niveau naïf. Les runs exacts sont dans grid-comparison.csv/json/md.
Une capture peut montrer le filtre, les 22 résultats et les colonnes principales ;
une seconde peut montrer les trois familles comparées. Aucune capture réalisée
automatiquement ni revue d’Aziz prétendue.

Ces tris sont exploratoires : ils ne valident pas une amélioration scientifique et
n'autorisent pas encore un champion. Ne cliquer sur aucun enregistrement/promotion.
Le script `python -m src.compare_runs` vérifie les résultats et régénère les tableaux,
sans entraîner ni modifier le registre. Charger .env dans le shell avant son lancement.
