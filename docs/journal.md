# Journal de bord du binôme

<!--
Mode d'emploi (à garder en tête du fichier) :
- Une entrée par séance (et par session de travail importante hors séance), la plus récente en bas.
- 3 à 5 lignes : qui a piloté, ce qui a été fait, ce qui a bloqué ou ce qui a été appris,
  la prochaine étape. Pas de roman : c'est un outil de pilotage, pas un rapport.
- Titre d'entrée au format exact « ## S<n> — AAAA-MM-JJ — <sujet> » (date réelle) :
  le pré-contrôle de rendu (make check-m10) compte les entrées datées.
- Liez les PR, issues et ADR (#12, docs/adr/0003-...). Les problèmes non résolus restent
  visibles : c'est précisément ce qui aide l'enseignant à vous débloquer.
- L'entrée d'exemple ci-dessous (date AAAA-MM-JJ) n'est pas comptée ; supprimez-la
  quand vous aurez écrit la vôtre.
-->

**Binôme :** Syrine (@syrinemrf) et Aziz (@MohamedAzizKouch, collaborateur)
**Repo :** https://github.com/syrinemrf/mlops-cours-2026
**Dataset :** IBM HR Analytics Employee Attrition (validé par courriel du professeur selon Syrine ; référence/date du courriel à consigner, aucune issue identifiée)
**Extensions :** non déclarées à J0 ; déclaration individuelle prévue avant la fin S8.

<!-- Vos entrées commencent ici. Modèle :

## S1 — AAAA-MM-JJ — Lab 0 : setup

- **Pilote / copilote :**
- **Fait :**
- **Bloqué / appris :**
- **Prochaine étape :**

-->

## S1 — 2026-10-18 — Lab 0 : restauration et setup personnel

- **Pilote :** Syrine (@syrinemrf), avec assistance Codex ; travail sur `work/syrine/m0`, à comparer avec Aziz.
- **Fait :** trois conteneurs kind redémarrés sans recréation ; registry, SeaweedFS et MLflow déployés ; environnement uv/Python 3.12 vérifié hors ligne ; test DVC poussé et relu dans S3 (12 octets identiques).
- **Bloqué / appris :** le kubeconfig était correct, mais les nœuds étaient arrêtés ; scripts non exécutables corrigés ; ancien MinIO conservé ; collision S3_PORT corrigée par enableServiceLinks=false ; make pf corrigé pour ne plus tuer son shell.
- **Prochaine étape :** checklist 18/19 (seul commit/push restant), tests MLflow et DVC réussis ; publier après accord de Syrine, relancer la validation, capturer le résultat puis comparer et faire relire la PR par Aziz.

## S2 — 2026-10-19 — Lab 0 : publication et validation finale

- **Pilote :** Syrine (@syrinemrf), avec assistance Codex.
- **Fait :** branche personnelle publiée ; `make check-m0` exécuté avec succès, **19/19** ; preuve dans `reports/m0/check-m0-final.log`.
- **Bloqué / appris :** le push nécessitait un agent SSH avec clé déverrouillée ; Syrine l’a chargé dans son terminal, sans partager sa phrase secrète.
- **Prochaine étape :** capturer le résultat, déposer le livrable, comparer avec Aziz et préparer la PR `lab/m0-setup` relue ; aucune fusion automatique.

## S3 — 2026-10-19 — Lab 0 : préparation locale de la clôture

- **Pilote :** Syrine (@syrinemrf), avec assistance Codex ; Aziz (@MohamedAzizKouch) reste le relecteur à solliciter.
- **Fait :** branches comparées après fetch ; `lab/m0-setup` avancée en fast-forward vers les trois commits validés ; option A déclarée, pseudo renseigné et brouillon de PR préparé.
- **Vérifié :** `make check-m0` 19/19 sur la base `23b452e` ; preuve `reports/m0/check-m0-integration-base.log` ; exclusions et signatures de secrets vérifiées.
- **Prochaine étape :** relire le commit documentaire local, autoriser ultérieurement sa publication, revalider le HEAD publié, capturer et déposer le résultat puis solliciter la revue réelle ; aucun push, PR, fusion ou Lab 1 à cette étape.

## S4 — 2026-10-19 — Lab 1 : premier incrément IBM HR

- **Pilote :** Syrine (@syrinemrf), avec assistance Codex ; aucune contribution ni approbation d’Aziz attestée ici.
- **Préalable M0 :** `git fetch origin` confirme la fusion réelle de PR #1 dans `origin/main`, commit `7606b83` ; main mis à jour en fast-forward, branche personnelle `work/syrine/m1` créée depuis ce commit. Aucune approbation GitHub d’Aziz observée.
- **Fait :** source Kaggle officielle version 1 et licence DbCL/ODbL vérifiées ; ingestion avec SHA-256 épinglé, schéma source 1 470 × 35 validé, export 1 470 × 32, identifiant hors modèle, constantes retirées et sensibles d’audit préservés ; dataset card et ADR-0001 proposé rédigés.
- **Vérifié / appris :** 237 Yes / 1 233 No, zéro manquant/doublon ; split stratifié simulé 1 176/294 (190/47 Yes), sans préparation persistée ni entraînement. Tests ciblés ajoutés ; le test officiel `test_sensible_hors_features` reste spécifique au crédit (`personal_status`) et échoue sur le contrat RH, sans modification du vérificateur.
- **Prochaine étape :** valider avec Syrine les coûts 1:1, gate ROC AUC 0.70 et sensibles/groupes ; configurer DVC (`s3://dvc-store/scoring`) puis préparer les données avec `prepare.id_column: EmployeeNumber`. Pas de push, PR, fusion, grid search, promotion ou Kubeflow dans cet incrément ; M1 non validé intégralement.

## S5 — 2026-10-20 — Lab 1 : tests génériques, DVC et préparation

- **Pilote :** Syrine (@syrinemrf), avec assistance Codex ; commits `b380e15` et `c6541a2` conservés. Choix ROC AUC/gate 0.70 provisoire, coûts neutres 1:1 et exclusion des sensibles validés par Syrine.
- **Phase 1 :** test auparavant spécifique à personal_status rendu générique avec fixture synthétique, sans skip ni suppression ; 32 tests réussis. Reproduction dans cwd/HOME vierges sans credentials Kaggle : mêmes octets ; groupes <30/30–44/>=45 : 326/830/314 profils (91/110/36 Yes).
- **Phase 2 :** DVC initialisé ; remote storage vers s3://dvc-store/scoring, secrets uniquement dans config.local ; download et prepare exécutés, lock vérifié, 4 fichiers poussés et relus dans SeaweedFS ; repro suivante ignorée, cache/remote synchronisés.
- **Préparation :** train/test 1176/294 lignes, 190/47 Yes ; ID préservé, aucun recouvrement ; sensibles et cible hors des 27 features ; source Feast 1470 × 29, float64/chaînes et timestamp UTC technique fixe. Tests globaux : 45 réussis, make lint réussi.
- **Incidents / suite :** Docker Desktop initialement arrêté ; lancé par Syrine, trois conteneurs kind existants redémarrés sans recréation/volume supprimé. Push d’abord refusé faute d’endpoint, puis réussi ; un contrôle DVC simultané a rencontré un verrou, reprise séquentielle réussie. Prochaine étape : src/train.py instrumenté et smoke test limité, sans grid search ni promotion à ce stade. Aucun push Git, fusion ou validation complète M1.


## S6 — 2026-10-20 — Cadrage scientifique et deux smoke tests A

- **Pilote :** Syrine (@syrinemrf), avec assistance Codex ; cinq commits M1 antérieurs conservés, aucune contribution/revue d’Aziz inventée.
- **Cadrage :** séparation A/B1/B2 et RQ1–RQ3 validées par Syrine ; audit Jia avec fichiers/lignes/preuves, deux défauts confirmés (partage des estimateurs, jointure des cohortes), divergence bootstrap et choix de grille réduite distingués. Code auteur non exécuté. Référence XP-Cube et originalité scientifique à approfondir.
- **Fait :** src/train.py implémenté exclusivement A selon §4.3 ; deux commandes §4.5 exécutées successivement sous MLflow scoring, tag mlops_A_v1. LR AUC 0.8329744164 / AP 0.6392128739 ; RF 50 arbres/profondeur5 AUC 0.7845637006 / AP 0.4428401623. Seuil balanced train 0.8384353741, coûts expérimentaux 1:1 ; rappel 14/47 et 1/47, sans correction opportuniste du seuil.
- **Vérifié :** 51 tests réussis, make lint réussi ; deux runs FINISHED, signatures 27 entrées, rechargement distant/local des deux modèles et métriques concordantes ; ancien modèle local conservé. Preuves dans reports/m1/training-smoke-validation.md et smoke-validation.json. Warning pip non épinglé dans conda.yaml généré, sans installation ni changement de lock.
- **Suite :** arrêt pour revue des deux résultats avant la suite pédagogique. Aucun grid search, reproduction Jia, calibration, promotion, push, fusion ou check-m1 intégral ; Lab M1 non déclaré terminé.


## S7 — 2026-10-20 — Grille pédagogique A et comparaison MLflow

- **Fait :** audit mathématique préalable du seuil balanced .838435 (train986/190, coûts expérimentaux1:1), application LR/RF distinguée de GB/Dummy .5, sans ajustement test. Grille officielle 22 configurations séquentielles : 1 Dummy, 8 LR, 9 RF, 4 GB, seed42, protocol=A et hashes tracés. B1/B2 inchangés et non exécutés.
- **Résultats :** 22 FINISHED + 2 smoke, aucun échec de configuration ; LR C=1 sans poids meilleure AUC observée 0.83685072 ; LR C=.1 sans poids meilleur coût34 et AP 0.66747212. RF meilleur AUC 0.79989663 mais rappel2/47. Scores exploratoires sur test répété, aucun champion désigné.
- **Vérifié :** 60 tests réussis, make lint ; relance effective réutilisant les22 mêmes run IDs sans fit ; quatre modèles distants rechargés, métriques concordantes à1e-12 ; LR .1 balanced concorde au smoke ; DVC status à jour. Rapports, tableaux complets et preuves sous reports/m1/grid-*. Registre vide, aucune promotion.
- **Incident :** forte pression mémoire/disque et swap plein, perte du port-forward MLflow rétabli par make pf ; SeaweedFS redémarré avec ancien état Error, cause non établie. Docker info répondait au préflight puis timeout, Kubernetes/MLflow accessibles. Aucun cluster recréé, volume supprimé ou service tiers arrêté.
- **Suite :** Syrine doit examiner les candidats et autoriser séparément l’étape7, en assumant le caractère pédagogique de la sélection sur test. Proposition CV train seule documentée pour la recherche future. Aucun push/merge, reproduction Jia, calibration ou validation complète M1.


## S8 — 2026-10-20 — Registry A et promotion contrôlée

- **Préalable :** diagnostics successifs stables : Docker28.4 répond, nœuds Ready sans MemoryPressure/DiskPressure, pods prêts et PVC Bound ; événements SeaweedFS indiquant liveness en échec puis kill exit137/Error, sans preuve OOMKilled. Aucun redémarrage ou changement d’infrastructure effectué. Snapshots avant/après : restartCount2 inchangé pour les deux pods.
- **Fait :** src/promote.py conserve la gate officielle ROC AUC>=.70 et ajoute une affectation explicite challenger-only. scoring-model v1=LR C1 sans poids (champion), v2=Dummy .5 (failed), v3=LR C.1 sans poids (challenger), vrais run IDs vérifiés. Dummy n’a pas déplacé le champion ; deuxième passage sans version supplémentaire.
- **Vérifié :** 72 tests réussis ; modèle champion distant et pyfunc chargés, cinq probabilités/predictions concordantes, seuil décision.5 identique au run et distinct de la gate.7 ; trois versions READY, alias finaux conformes. Preuves sous reports/m1/registry-*. Choix exploratoires sur test répété, aucune supériorité scientifique revendiquée.
- **Suite :** étape7 vérifiée ; étapes 8/9 non exécutées, aucune reproduction Jia, nouveau training, donnée brute/secret suivi, push ou merge. Conserver B1/B2, split et variables ; pipeline DVC final et Feast restent à faire après autorisation.

- **Diagnostic officiel après commit418d026 :** make check-m1 bloqué par permission d’exécution du script (mode644, laissé intact). Même vérificateur lancé via bash : 14/18, code4 ; Registry entièrement vert. Restent pipeline DVC train/evaluate, reports/metrics.json, filiation run DVC/data_md5 et Feast. Logs check-m1-after-registry*.log ; aucun stage8/9 lancé.


## S9 — 2026-10-20 — Finalisation M1 DVC et Feast

- **Préalable :** reprise après intervention de Syrine sur la charge du poste. Docker CLI info encore lent, moteur /info et docker ps accessibles, services/PVC prêts, pas de nouvelle instabilité observée pendant les opérations. Aucune infrastructure recréée, réinitialisée ou supprimée. Mode checker644→755 autorisé, contenu inchangé.
- **DVC :** quatre stages ; download/prepare conservés et ignorés ; un fit LR C=.1 balanced selon params existants, run b55a5e9846cb44aeac027426280053e8, protocol=A et launched_by=dvc, MD5 brut16e6acc1f69d648c4ec1d3b44efc0179 conforme au lock. AUC 0.8329744164, coût expérimental36, seuil décision 0.838435. Deuxième évaluation identique octet par octet, repro suivante ignorée, six objets poussés et remote synchronisé.
- **Feast :** entité employee/EmployeeNumber, vue request_features, service scoring_v1 ;13float64/14String sans sensibles/cible. Apply et matérialisation réussis ; offline1176×30 avec27features conformes ; online1salarié/27features conformes. Snapshot UTC fixe synthétique, aucune prétention temporelle production.
- **Vérifié :** 77 tests passent, un warning de dépendance Feast/NumPy ; lint réussi ; intermédiaire17/18 puis make check-m1 réel18/18 code0. Nouveau clone temporaire avec cache vide : pull/repro sans fit, métriques/lock identiques, Feast reconstruit, Git propre ; Python existant réutilisé, nouveau cluster et installation vierge non testés. Logs et détails dans reports/m1/final-validation.md.
- **Registre et suite :** trois versions et alias v1 champion/v3 challenger conservés, Dummy v2 failed. Aucun appel de promotion DVC8.4 : conflit annoncé et options documentées. B1/B2/XP-Cube, split, variables et hyperparamètres inchangés ; aucun push/PR/merge/tag. Revue réelle par Syrine puis Aziz et intégration/PR/J0 uniquement après autorisation.

## S10 — 2026-10-20 — Audit M1 avant publication et J0

- **Pilote :** Syrine avec assistance Codex ; revue du guide 8–10 au HEAD d2ea3ca, arbre initial propre, aucun AGENTS.md applicable trouvé. Les 15 commits M1 restent intacts ; aucune contribution/revue d’Aziz supposée.
- **Vérifié :** lecture GitHub : main 7606b83, seule PR M0 fusionnée, aucune branche/PR M1 ; lecture MLflow : 25 runs FINISHED, versions 1/2/3 et alias conservés ; DVC local/cloud à jour. Relecture des preuves 18/18, 77 tests et lint antérieures, sans réexécuter entraînement ni contrôle officiel pendant l’audit.
- **Constats et documents :** divergence 8.4 confirmée ; alignement futur LR C=1 sans poids recommandé, à autoriser. Simulation du parseur sans fit : les neuf RF hériteraient aussi de none, poids balanced explicite recommandé pour préserver la grille. Preuves 8.5/10.3/10.4 encore incomplètes. README/card/ADR/NOTES et état A actualisés, rapports historiques conservés ; audit, résumé des contributions, checklist Aziz, brouillon de PR et procédure publication/J0 préparés dans reports/m1.
- **Accord et suite :** Syrine confirme l’accord dataset par courriel du professeur ; message non retrouvé dans la recherche ciblée, date/objet à consigner sans inventer d’issue. Diagnostic droits Aziz inaccessible au connecteur (403, pas une preuve de droits insuffisants). Paramètres/registre/locks/dépendances inchangés ; aucun commit/push/PR/merge/tag pendant l’audit. Autoriser séparément corrections techniques puis publication et jalon.

## S11 — 2026-10-20 — Alignement DVC, reproductibilité et validation avant publication

- **Pilote :** Syrine avec assistance Codex ; audit documentaire commité db871c8, code 49533e3. LR DVC C=1 sans poids, seed 42 ; neuf RF explicitement balanced. Données, préparation, contrat, split 80/20, gate 0,70 et dépendances inchangés ; aucun travail B1/B2/XP-Cube exécuté.
- **Reproductibilité :** clone isolé conservé, §8.5 none/balanced/none avec retour train/evaluate au cache, même run/lock/métriques ; §10.3 force les quatre stages, données et 294probabilités exactement identiques. Checkpoint 78fe741 propre au clone, non intégré. Le lock principal est préservé pendant ces essais.
- **DVC/Registry :** run de référence ef2d3f85ebe3432f9172275c34bbd6ac, MD5 export 16e6acc1f69d648c4ec1d3b44efc0179, AUC 0,8368507193, seuil 0,5, coût 35. Trois objets poussés, dix objets S3 vérifiés ;29 runs FINISHED. Nouvelle v4 champion, v3 challenger réaffectée, versions 1/2/3 conservées, idempotence et rejet Dummy réels.
- **Vérifié :**85 tests, un warning Feast/NumPy ; lint et check-m1 18/18 code0. Signature, paramètres, 294probabilités et métriques du modèle distant conformes au modèle DVC ; différence des archives skops expliquée par IDs/horodatages, payloads/schéma normalisé identiques. Feast offline/online conforme ; anciens rapports conservés, contrôles officiels inchangés.
- **Limites / suite :** même cluster et venv existant ; mémoire limitée, aucune infrastructure recréée. Résultats pédagogiques sur test répété ; §10.4 à rejouer par Aziz avec ses IDs/versions, sans approbation supposée. Rapport reports/m1/alignment-validation.md ; attente de validation Syrine avant tout push Git/PR/merge/tag, capture/remise et J0 ultérieurs.


## S12 — 2026-10-27 — Intégration collaborative M1

- **Pilote :** Syrine avec assistance Codex ; contributions sources d’Aziz reprises sélectivement avec auteurs et commits tracés. Aucune revue humaine GitHub présumée.
- **Fait :** branche lab/m1-versioning dans un worktree isolé depuis d740ca5 ; sensibilité/ADR cherry-pickés -x, CV extraite et adaptée dans des modules indépendants ; ADR0002/0003 renumérotés, ADR0004 ajouté. Contrat, préparation, modèle, lock, Feast, gate/seuil, B1/B2 et dépendances intacts.
- **Mesuré :** 112tests, warning Feast/NumPy connu, lint vert, checker18/18 code0 sur intégration technique ; CVtrain ROC AUC0,854679982±0,029784770 et AP0,672947514±0,053510568 (écarts-types, pas IC). Deux diagnostics identiques octet pour octet, aucun seuil promu.
- **Préservé :** DVC4stages ignorés, données/modèle conformes cache/lock/dépôt personnel ;29runs FINISHED,22runs grille inchangés, championv4DVC/challengerv3 vérifiés ; Feast offline/online reconstruit pour le worktree. Aucune nouvelle grille, promotion ou modification des branches personnelles.
- **Incidents :** Docker Desktop arrêté, conteneurs existants redémarrés ; cacheDVC/tunnels rétablis sans recréation ni suppression. Échecs initiaux conservés.
- **Suite :** vérifier encore le HEAD documentaire final, publier uniquement la branche d’intégration et PR brouillon sous autorisation reçue ; vraie revue Aziz, replay §10.4 du contrat commun, capture/remise et référence du courriel restent requis avant fusion/J0. Rapport reports/m1/integration/final-integration.md.
