# Preuves du Lab 3 — Validation (2026-11-08)

Exportées depuis le stockage d'artefacts KFP (bucket `mlpipeline`, voir `kfp/manifest.json`).
Seuls les rapports et les journaux d'exécution sont commités : aucune donnée ni aucun modèle.
La clé secrète du stockage KFP est absente des journaux. La clé d'accès, valeur par défaut
`minio`, n'y apparaît que comme nom de fournisseur.

| Run KFP | Id | État | Verdict |
|---|---|---|---|
| `m3-scoring-pipeline` (`scoring-pipeline`, `challenger_only=True`) | `2e33d31b-8dca-4269-ab82-42194ef57094` | SUCCEEDED | 8/8 étapes ; contrat 103/103 ; drift train/test 0/31 ; modèle 18/18 (ROC AUC 0,8369, AP 0,647, taux de base 0,1599, seuil 0,5) ; v8 enregistrée |
| `m3-scoring-bad-data-test` | `f45e8973-1780-4285-9730-95443f141681` | FAILED (attendu) | `validate-data` refuse les 3 bugs injectés (MonthlyIncome, Department, Attrition) ; `prepare-features` jamais exécuté |
| `m3-scoring-drift-demo` | `d73fd533-9b35-4fdf-b304-5b5a564bd8b3` | SUCCEEDED | drift détecté 4/31 (DistanceFromHome, Age, MonthlyIncome, OverTime), signalé sans bloquer |

Le run refusé n'a pas de rapport HTML : l'étape s'arrête avant de copier ses sorties. Son
résumé JSON (`"success": false`, 3 échecs) se trouve dans
`kfp/scoring-bad-data-test/validate-data-executor-logs.log`.

Registre `scoring-model` (lecture seule avant et après le run principal) :
`registry-before.json` (@champion v7, @challenger v7) puis `registry-after.json` (@champion v7
inchangé, @challenger v8 créée par le run 2e33d31b, `launched_by=kfp`).
