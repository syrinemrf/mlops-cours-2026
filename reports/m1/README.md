# Lire les preuves M1

Tous les résultats sont des observations datées, pas des états perpétuellement
actuels de MLflow ou d’un autre cluster. Ne pas remplacer les logs des phases
précédentes par les résultats ultérieurs.

| Rapport | Portée et snapshot |
|---|---|
| [Intégration collaborative](integration/final-integration.md) | Ajouts CV/OOF/ADR Aziz, validation propre et limites §10.4 ; voir preuves datées |
| [Alignement et reproductibilité](alignment-validation.md) | Snapshot personnel avant intégration : 85 tests, 18/18, DVC et champion v4 alignés ; exercices 8.5/10.3 vérifiés, 10.4 Aziz en attente |
| [Audit avant publication](pre-publication-audit.md) | État d2ea3ca, écarts au guide, décisions encore requises |
| [Revue/publication/J0](binome-review-publication.md) | Procédure historique ; branches personnelles publiées depuis, voir rapport d’intégration |
| [Finalisation technique](final-validation.md) | Pipeline/Feast, 25 runs, trois versions, limites de reproduction ; preuves à ccf031f, checker reconfirmé à d2ea3ca |
| [Checker final](check-m1-final.log), [tests](final-tests.log), [lint](final-lint.log) | 18/18 réels, 77 tests, lint valide lors de la finalisation |
| [Registre](registry-validation.md) | Phase7 : 24 runs, v1/v2/v3, 72 tests, checkpoint14/18 ; état historique avant DVC/Feast |
| [Grille](grid-analysis.md), [comparaison](grid-comparison.md) | Code 9c02057 : 22 configurations, 24 runs au total, registre encore vide à cette date |
| [Smoke](training-smoke-validation.md) | Deux fits A, code 48c354e ; aucun grid search à ce stade historique |
| [Phase2 données](phase2-validation.md) | DVC download/prepare avant train/evaluate et Feast |
| [Ingestion](validation.md) | Premier incrément : résultat de test personal_status encore en échec à cette date, corrigé ensuite sans skip |

Les fichiers `*-initial.log`, `check-m1-after-registry*` et
`check-m1-before-feast.log` conservent les incidents et validations intermédiaires.
Ils ne doivent pas être présentés comme la validation finale ni supprimés pour
masquer un échec. Les JSON/CSV contiennent les valeurs exactes et les manifests ;
les tableaux Markdown peuvent arrondir les métriques.

La divergence du champion avec le modèle DVC était ouverte au snapshot d2ea3ca.
Elle est résolue dans alignment-validation.md, avec ses nouveaux run ID/version/commit,
sans modifier les preuves historiques. Les scripts de diagnostic acceptent un chemin
de sortie explicite pour conserver les anciens rapports.
Les scores A sont pédagogiques/exploratoires sur test consulté à répétition ;
aucune reproduction scientifique Jia ni supériorité statistique revendiquée.
