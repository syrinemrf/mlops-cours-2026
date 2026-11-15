### Validation du modèle : 0 échec(s) sur 18

ROC AUC 0.8369 ; AP 0.647 (taux de base 0.1599) ; seuil 0.5

| Famille | Test | Statut |
|---|---|---|
| evidently | RocAuc metric: Equal 0.894 ± 0.179 | OK |
| evidently | RocAuc metric: Greater or Equal 0.700 | OK |
| behavior | test_metrique_primaire_au_gate | OK |
| behavior | test_precision_moyenne_au_dessus_du_taux_de_base | OK |
| behavior | test_seuil_de_decision_documente | OK |
| behavior | test_cout_metier_inferieur_aux_politiques_naives | OK |
| behavior | test_performance_par_sous_groupe[Age] | OK |
| behavior | test_performance_par_sous_groupe[Gender] | OK |
| behavior | test_performance_par_sous_groupe[MaritalStatus] | OK |
| behavior | test_invariance[HourlyRate] | OK |
| behavior | test_invariance[MonthlyRate] | OK |
| behavior | test_directionnel[OverTime:No->Yes] | OK |
| behavior | test_directionnel[BusinessTravel:Non-Travel->Travel_Frequently] | OK |
| behavior | test_directionnel[EnvironmentSatisfaction:1: Low->4: Very High] | OK |
| behavior | test_directionnel[JobSatisfaction:1: Low->4: Very High] | OK |
| behavior | test_directionnel[MonthlyIncome:x1.5] | OK |
| behavior | test_directionnel[TotalWorkingYears:x1.5] | OK |
| behavior | test_directionnel[DistanceFromHome:x2.0] | OK |
