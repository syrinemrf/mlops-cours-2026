# M1 — intégration collaborative, validation et préparation de J0

Date : 2026-10-27, Africa/Lagos. Branche commune : lab/m1-versioning.
Base Syrine d740ca5 ; branche Aziz auditée 336964f ; main 7606b83 préservée.
Code des modules intégrés : **2fdc4f5298a301f6a49bdc06eb3bcd7b0665ae47**.
Ce rapport et ses preuves sont ajoutés par un commit documentaire ultérieur.
Les deux branches personnelles ne sont ni modifiées, ni réécrites.

## Contributions réelles et attribution

Syrine : les 18 commits M1 depuis main portent son auteur Git et construisent
l’ingestion Kaggle version1, le contrat 27 features, les tests/ADR, la préparation,
les quatre stages DVC, les deux smoke tests et 22 configurations historiques,
le registre/sa gate et le modèle DVC champion, Feast et les preuves de reproductibilité.
L’intégration et ses adaptations/tests sont réalisées par Syrine avec assistance Codex.

Aziz : contributions identifiées dans sa branche publiée, sans présumer de revue
humaine. Trois cherry-picks -x conservent l’auteur MohamedAzizKouch et les références
originales : sensibilité 104cf5c, ADR ea37452 et 39596be. La fonction CV de 7f9d1ed
est extraite initialement sans modifier son corps dans 20bd582, auteur source Aziz ;
les adaptations apparaissent séparément dans le commit Syrine 2fdc4f5.
Il n’y a pas de merge global d’Aziz, ni reprise de son contrat/pipeline incompatibles.

| Commit d’intégration technique | Auteur | Message |
|---|---|---|
| 31d458a | MohamedAzizKouch | feat(m1): add decision threshold sensitivity analysis |
| 7b7d101 | MohamedAzizKouch | docs(m1): add ADR-0001 on dataset and sensitive attributes |
| 45d0b73 | MohamedAzizKouch | docs(m1): add ADR-0002 on metric, threshold and model selection |
| 20bd582 | MohamedAzizKouch | feat(validation): extract train-only cross-validation from Aziz |
| 2fdc4f5 | syrinemrf | feat(validation): integrate isolated train-only CV and threshold diagnostics |

Les ADR sont renumérotés dans le commit documentaire : ADR0001 Syrine préservé,
ADR0002/0003 Aziz avec encadrés de contexte et provenance, ADR0004 sur les analyses
indépendantes. Les auteurs d’origine et le caractère proposé des variantes restent
explicites. La relecture GitHub d’Aziz n’est pas encore observée.

## Décisions conservées

- IBM HR Kaggle v1, source1470×35, export1470×32 ; 27 prédicteurs, sensibles
  Age/Gender/MaritalStatus et identifiant EmployeeNumber exclus des prédicteurs.
- Split80/20 stratifié seed 42 : train 1176 (190 positifs), test 294 (47 positifs).
- roc_auc primaire, gate 0,70 ; LR C=1 sans poids, seed 42 ; seuil décision0,5.
- Groupes de référence <30, 30–44, >=45 ; coûts FN/FP1:1 expérimentaux neutres.
- Quatre stages DVC, expérience scoring, registre scoring-model,
  remote storage s3://dvc-store/scoring ; aucun critère de checker changé.

Les variantes Aziz AP/gate 0,32, âge40 en deux groupes, traitement numérique de neuf
échelles et règle one-SE sont documentées, sans substitution au contrat commun.
Les 27 noms de prédicteurs coïncident entre branches, mais leurs encodages diffèrent.
Ne pas affirmer une amélioration en comparant leurs scores comme s’ils avaient
les mêmes conditions expérimentales.

## CV et sensibilité réellement exécutées

Commande : uv run --no-sync python -m src.sensitivity.
Source : src/cross_validation.py et src/sensitivity.py, hors DAG DVC.
Cinq plis stratifiés sur TRAIN_CSV seulement, seed 42 ; clone du Pipeline complet
par pli, cinq fits LR séquentiels pour produire deux métriques et les probabilités
OOF. Aucun prétraitement appris sur validation/test. Chaque ligne train reçoit
exactement une prédiction OOF. Les OOF individuelles restent en mémoire.

| Métrique train CV | Moyenne | Écart-type des cinq plis (ddof=0) |
|---|---:|---:|
| ROC AUC | 0.854679982 | 0.029784770 |
| Average Precision | 0.672947514 | 0.053510568 |

Cette dispersion n’est pas un IC95%. Les moyennes CV ne sont pas le score du test
final, ni un résultat Jia. Aucun hyperparamètre ou champion sélectionné par ces
nouveaux diagnostics. Chaque famille peut être diagnostiquée séparément avec --model,
avec ses paramètres exportés ; seules les analyses LR fixée sont exécutées ici.

| Scénario OOF hypothétique | Seuil | Précision | Rappel | FP | FN | Coût |
|---|---:|---:|---:|---:|---:|---:|
| official_threshold_FN_FP_1_1 | 0.500000 | 0.760684 | 0.468421 | 28 | 101 | 129 |
| hypothetical_FN_FP_1_1 | 0.534894 | 0.792453 | 0.442105 | 22 | 106 | 128 |
| hypothetical_FN_FP_2_1 | 0.343287 | 0.610837 | 0.652632 | 79 | 66 | 211 |
| hypothetical_FN_FP_3_1 | 0.327888 | 0.600000 | 0.663158 | 84 | 64 | 276 |
| hypothetical_FN_FP_5_1 | 0.222496 | 0.480000 | 0.757895 | 156 | 46 | 386 |
| hypothetical_FN_FP_10_1 | 0.222496 | 0.480000 | 0.757895 | 156 | 46 | 616 |

Coût = ratio×FN + FP. Les scénarios ne sont pas des coûts économiques RH établis.
Le seuil optimisé est choisi et évalué sur les mêmes OOF : coût optimiste, pas une
estimation indépendante. Le seuil opérationnel **reste 0,5** ; aucun nouveau seuil
n’est enregistré dans le modèle ou promu. Les agrégats complets, scores de chaque pli,
hash des affectations, versions Python packages, paramètres et empreintes train/
contrat/params sont dans [train-diagnostics.json](train-diagnostics.json).
Le rejeu réel retrouve le JSON **octet pour octet**, sans nouveau run MLflow.

## Préservation DVC et Model Registry

18 fichiers protégés de code/contrat/DVC/Feast/recherche/dépendances sont identiques
à d740ca5. Source Kaggle SHA256 a5c31e38bd7fafc9bc333884eb181b06b41b8e5e488e8f7ccb27199fb3be7659
inchangée ; l’empreinte observée initialement n’est pas une authentification indépendante.
CSV export MD5 16e6acc1f69d648c4ec1d3b44efc0179, SHA256
27e7bebda91c7e6d0b77e80128c2d9383d70a19a185b51ecfe3bb90f761d2a78.
Les quatre fichiers de données et tous les membres du modèle sont conformes au lock,
au cache et au dépôt personnel, octet pour octet. Hash modèle DVC :
46cf394ffbe298bf1e653379449c8f8f.dir. dvc.lock inchangé.

DVC checkout a restauré les sorties depuis le cache existant. dvc status à jour,
status --cloud synchronisé ; dvc repro a ignoré download, prepare, train et evaluate.
Aucun fit du pipeline ni dvc push supplémentaire nécessaire. Les analyses ne sont
pas importées par train.py et n’invalident pas le DAG. Les données/modèles/secrets
et bases locales ne sont pas ajoutés à Git.

Registre distant réellement vérifié : **4 versions**, alias
champion v4/run ef2d3f85ebe3432f9172275c34bbd6ac (issu de DVC), challenger v3/run
139ae364aa6e4166b2bd19ef533f48e7 ; Dummy v2 failed et v1 conservées.
Le modèle source reste celui du code 49533e3 ; aucun nouveau commit Git d’analyse ne
réattribue son entraînement. Signature27features, paramètres, seuil, probabilités
local/distant sur294lignes et métriques concordent. Chargements sklearn/pyfunc et
cinq prédictions vérifiés. Les différences de sérialisation skops local/distant
étaient déjà expliquées dans alignment-validation.md ; pas d’identité binaire revendiquée.

Métriques du champion sur le **test pédagogique déjà réutilisé**, inchangées :
ROC AUC 0,8368507193 ; AP 0,6470361871 ; precision 0,714286 ; recall 0,425532 ;
F1 0,533333 ; accuracy 0,880952 ; TN239 FP8 FN27 TP20 ; coût expérimental 35.
Ce n’est pas une nouvelle performance indépendante et aucune supériorité statistique
n’est revendiquée. Les **29 runs** restent FINISHED ; les 22IDs/paramètres/métriques
de grille sont revérifiés inchangés. Aucun nouveau run ou modèle MLflow créé.

## Feast et infrastructure

Les seules bases ignorées du nouveau worktree sont reconstruites par feast apply
et materialize-incremental jusqu’au2026-10-27T23:59:59Z. L’entité employee/EmployeeNumber,
request_features et scoring_v1 sont préservés ; Parquet1470×29, offline1176×30,
27 features comparées exactement à train ; online un salarié/27 features conformes.
Les trois requêtes avant snapshot sont manquantes comme attendu. Ce snapshot
synthétique ne démontre aucune propriété temporelle RH de production.

Docker Desktop était arrêté/inaccessible depuis WSL. Il a été démarré ; seuls les
3 conteneurs kind existants ont été redémarrés, sans cluster/PVC/volume recréé.
SeaweedFS et MLflow sont redevenus Ready, les PVC Bound. Les tunnels lancés en
arrière-plan n’ont pas persisté dans cette session ; leur maintien en sessions
actives a rétabli les accès. La première tentative DVC a rencontré un problème
d’accès à sa base cache ; cache utilisateur temporaire/config locale résolvent
ce point. Le diagnostic lancé avant la restauration data a échoué sans fit ;
les logs initiaux restent conservés au lieu de masquer ces incidents.
Mémoire limitée : exécution séquentielle, cinq fits LR uniquement par diagnostic.
Aucune installation de paquet, nouvelle grille, promotion ou expérience B1/B2/M2.

## Tests et preuves

- **112 tests réussis**, aucun skip/xfail ajouté ;27 tests couvrent les modules nouveaux.
  Un warning Feast/NumPy déjà connu, sans masquage de l’échec éventuel.
- **make lint réussi** : Ruff check/format et yamllint ;71 fichiers déjà formatés.
- **make check-m1 :18/18, code retour0**, réellement exécuté sur l’intégration technique.
- Scaler/encodage propres à chaque pli,5 fits/5validations disjointes, base non ajustée,
  déterminisme, erreurs propagées, classes/ratios/probabilités invalides rejetés,
  train seul, absence de démarrage MLflow et seuil officiel inchangé testés.

[Tests](tests.log), [lint](lint.log), [18 contrôles](check-m1.log),
[DVC local](dvc-status.log), [cloud](dvc-cloud.log), [repro sans fit](dvc-repro.log),
[registre](registry.json), [Feast](feast.json), [préservation](preservation.json).

Critère de publication : relancer le checker sur le HEAD documentaire final et
comparer sa sortie octet pour octet à check-m1.log. Le SHA final et ce résultat
sont explicités dans la PR, sans introduire un hash Git circulaire dans ce rapport.
La PR reste brouillon ; aucune approbation humaine n’est fabriquée.

## Limites et actions Aziz avant fusion/J0

Le test pédagogique a été consulté à répétition. CV pour sélection et seuils OOF
optimisés ne sont pas des estimations finales indépendantes ; une évaluation
scientifique nécessitera une validation supplémentaire/nichée, sans fuite.
Données synthétiques, aucun historique temporel RH réel, coût 1:1 hypothétique,
gate 0,70 provisoire ; originalité de recherche non démontrée. B1/B2 et XP-Cube intacts.

L’accord dataset est confirmé par courriel selon Syrine, référence/date encore à
consigner. Le journal Aziz décrit un check personnel18/18 sur son autre contrat ;
aucune reproduction §10.4 du **contrat commun** n’est démontrée ici.
Aziz doit rejouer sur son cluster existant avec sa configuration ignorée, vérifier
source et splits/hashes, ses vrais runs/versions/alias, Feast, tests/lint/check18/18,
et consigner les écarts. Ne pas copier bases MLflow/Feast ni écraser le lock commun
avec ses seuls nouveaux IDs/dates. Les anciens runs à encodage différent ne doivent
pas être réétiquetés comme des entraînements du contrat commun.

Restent : vraie revue du dernier SHA, corrections éventuelles, capture réelle des
18 contrôles, preuve §10.4 et remise demandée, puis autorisation de fusion vers main
et seulement ensuite décision du tag j0. Aucun merge ni tag effectué.
