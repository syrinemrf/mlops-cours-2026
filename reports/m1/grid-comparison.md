# Grille M1 — protocole A, comparaison exploratoire

Scores test répétés : aucune estimation finale indépendante, aucun champion désigné.

AP = average_precision ; PR-AUC trapézoïdale conservée séparément. Temps = fit pipeline uniquement.

Version Kaggle 1 ; toutes les lignes ont le même export MD5 `16e6acc1f69d648c4ec1d3b44efc0179`.
SHA-256 et paramètres complets dans grid-comparison.csv/json.

| index | model | hyperparameters | roc_auc | average_precision | pr_auc_trapezoidal | precision | recall | f1 | accuracy | business_cost | decision_threshold | fit_seconds | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | dummy | {"random_state": "42"} | 0.500000 | 0.159864 | 0.579932 | 0.000000 | 0.000000 | 0.000000 | 0.840136 | 47.000000 | 0.5 | 0.184158 | 0c42486a18f340ddb2db995d8797c70d |
| 2 | logistic_regression | {"C": "0.01", "class_weight": "None", "random_state": "42"} | 0.811439 | 0.632719 | 0.630055 | 1.000000 | 0.042553 | 0.081633 | 0.846939 | 45.000000 | 0.5 | 0.157579 | 143c10a416e7465baceaa9a744e47719 |
| 3 | logistic_regression | {"C": "0.01", "class_weight": "balanced", "random_state": "42"} | 0.823068 | 0.654889 | 0.652394 | 1.000000 | 0.063830 | 0.120000 | 0.850340 | 44.000000 | 0.8384353741496599 | 0.247011 | 0d56caf189dd4735ac4d599ce038d9ea |
| 4 | logistic_regression | {"C": "0.1", "class_weight": "None", "random_state": "42"} | 0.836075 | 0.667472 | 0.665013 | 0.809524 | 0.361702 | 0.500000 | 0.884354 | 34.000000 | 0.5 | 0.294421 | 139ae364aa6e4166b2bd19ef533f48e7 |
| 5 | logistic_regression | {"C": "0.1", "class_weight": "balanced", "random_state": "42"} | 0.832974 | 0.639213 | 0.636335 | 0.823529 | 0.297872 | 0.437500 | 0.877551 | 36.000000 | 0.8384353741496599 | 0.627916 | c154f9026ebc49598a87a93dc858e927 |
| 6 | logistic_regression | {"C": "1.0", "class_weight": "None", "random_state": "42"} | 0.836851 | 0.647036 | 0.644389 | 0.714286 | 0.425532 | 0.533333 | 0.880952 | 35.000000 | 0.5 | 0.461460 | 5ef49fc5f3e740f28c523b0dcc1ae8c1 |
| 7 | logistic_regression | {"C": "1.0", "class_weight": "balanced", "random_state": "42"} | 0.828064 | 0.613069 | 0.610052 | 0.692308 | 0.382979 | 0.493151 | 0.874150 | 37.000000 | 0.8384353741496599 | 0.264806 | 2fcbbda9ff3149868c671854209ff2ab |
| 8 | logistic_regression | {"C": "10.0", "class_weight": "None", "random_state": "42"} | 0.833061 | 0.635722 | 0.632993 | 0.666667 | 0.425532 | 0.519481 | 0.874150 | 37.000000 | 0.5 | 0.237197 | d001c6ceab184505b583a32c8286ad71 |
| 9 | logistic_regression | {"C": "10.0", "class_weight": "balanced", "random_state": "42"} | 0.822810 | 0.597210 | 0.594109 | 0.642857 | 0.382979 | 0.480000 | 0.867347 | 39.000000 | 0.8384353741496599 | 0.428119 | 7c2b0f8fba6645fc8405069817597dbc |
| 10 | random_forest | {"class_weight": "balanced", "max_depth": "4", "n_estimators": "100", "random_state": "42"} | 0.776380 | 0.412128 | 0.405278 | 1.000000 | 0.042553 | 0.081633 | 0.846939 | 45.000000 | 0.8384353741496599 | 9.025964 | 4c76aa0956cf4c5bbe9747f8329532c2 |
| 11 | random_forest | {"class_weight": "balanced", "max_depth": "8", "n_estimators": "100", "random_state": "42"} | 0.793436 | 0.463470 | 0.455770 | 1.000000 | 0.042553 | 0.081633 | 0.846939 | 45.000000 | 0.8384353741496599 | 0.714732 | 9a21733765164a74ba36ad3e766ee3ed |
| 12 | random_forest | {"class_weight": "balanced", "max_depth": "None", "n_estimators": "100", "random_state": "42"} | 0.798131 | 0.466194 | 0.459260 | 0.750000 | 0.063830 | 0.117647 | 0.846939 | 45.000000 | 0.8384353741496599 | 0.531603 | b1308f7cda524fa7b3e8c4dcacf9a562 |
| 13 | random_forest | {"class_weight": "balanced", "max_depth": "4", "n_estimators": "200", "random_state": "42"} | 0.781807 | 0.426820 | 0.419830 | 1.000000 | 0.042553 | 0.081633 | 0.846939 | 45.000000 | 0.8384353741496599 | 0.722351 | b3a9ed172b2e432abf84b2e84842b2cc |
| 14 | random_forest | {"class_weight": "balanced", "max_depth": "8", "n_estimators": "200", "random_state": "42"} | 0.798777 | 0.469854 | 0.462015 | 0.666667 | 0.042553 | 0.080000 | 0.843537 | 46.000000 | 0.8384353741496599 | 0.948593 | 1e37e362a928430c864f16e2fde27cf1 |
| 15 | random_forest | {"class_weight": "balanced", "max_depth": "None", "n_estimators": "200", "random_state": "42"} | 0.796236 | 0.466194 | 0.461671 | 0.666667 | 0.042553 | 0.080000 | 0.843537 | 46.000000 | 0.8384353741496599 | 0.979502 | 37df33057d294770b4342ec0e65435b0 |
| 16 | random_forest | {"class_weight": "balanced", "max_depth": "4", "n_estimators": "400", "random_state": "42"} | 0.783616 | 0.424753 | 0.416872 | 1.000000 | 0.042553 | 0.081633 | 0.846939 | 45.000000 | 0.8384353741496599 | 1.302004 | a8b78d8dd2db46b99980a31c1de5be35 |
| 17 | random_forest | {"class_weight": "balanced", "max_depth": "8", "n_estimators": "400", "random_state": "42"} | 0.799897 | 0.473152 | 0.465438 | 1.000000 | 0.042553 | 0.081633 | 0.846939 | 45.000000 | 0.8384353741496599 | 1.499227 | 2fdfff9cdb934b4985e211d7e6613a59 |
| 18 | random_forest | {"class_weight": "balanced", "max_depth": "None", "n_estimators": "400", "random_state": "42"} | 0.798475 | 0.472376 | 0.465688 | 1.000000 | 0.042553 | 0.081633 | 0.846939 | 45.000000 | 0.8384353741496599 | 1.748056 | d1c17a8d81f943879a6a707401d3e5a0 |
| 19 | gradient_boosting | {"learning_rate": "0.1", "max_depth": "2", "n_estimators": "100", "random_state": "42"} | 0.814282 | 0.505288 | 0.497498 | 0.642857 | 0.191489 | 0.295082 | 0.853741 | 43.000000 | 0.5 | 0.760500 | 756efdfce5114e6a9b1b1613cbb217e1 |
| 20 | gradient_boosting | {"learning_rate": "0.1", "max_depth": "3", "n_estimators": "100", "random_state": "42"} | 0.812904 | 0.497053 | 0.489551 | 0.611111 | 0.234043 | 0.338462 | 0.853741 | 43.000000 | 0.5 | 0.732296 | ffa7277146d04927a9248ac5506c7e73 |
| 21 | gradient_boosting | {"learning_rate": "0.1", "max_depth": "2", "n_estimators": "200", "random_state": "42"} | 0.813593 | 0.530093 | 0.522792 | 0.764706 | 0.276596 | 0.406250 | 0.870748 | 38.000000 | 0.5 | 1.119710 | ce38de16ba6943aba4ddb1b460c7f82c |
| 22 | gradient_boosting | {"learning_rate": "0.1", "max_depth": "3", "n_estimators": "200", "random_state": "42"} | 0.804720 | 0.513621 | 0.507731 | 0.652174 | 0.319149 | 0.428571 | 0.863946 | 40.000000 | 0.5 | 1.305695 | 4fb0586f12c94b15a24ba00a42501c6b |

## Candidats descriptifs, sans promotion

- dummy : meilleur ROC AUC observé 0.500000, configuration 1, run 0c42486a18f340ddb2db995d8797c70d.
- logistic_regression : meilleur ROC AUC observé 0.836851, configuration 6, run 5ef49fc5f3e740f28c523b0dcc1ae8c1.
- random_forest : meilleur ROC AUC observé 0.799897, configuration 17, run 2fdfff9cdb934b4985e211d7e6613a59.
- gradient_boosting : meilleur ROC AUC observé 0.814282, configuration 19, run 756efdfce5114e6a9b1b1613cbb217e1.
- average_precision : 0.667472, configuration(s) 4.
- f1 : 0.533333, configuration(s) 6.
- business_cost : 34.000000, configuration(s) 4.
- brier_score : 0.090283, configuration(s) 4.
- log_loss : 0.321146, configuration(s) 4.

## Effet des poids LR à C constant

Différences balanced moins None, à leurs seuils respectifs 0.838435 et 0.5 :

| C | delta AUC | delta AP | delta coût | delta rappel |
|---|---|---|---|---|
| 0.01 | +0.011629 | +0.022170 | -1 | +0.021277 |
| 0.1 | -0.003101 | -0.028259 | +2 | -0.063830 |
| 1.0 | -0.008786 | -0.033967 | +2 | -0.042553 |
| 10.0 | -0.010251 | -0.038512 | +2 | -0.042553 |
