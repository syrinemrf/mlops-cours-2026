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
**Dataset :** IBM HR Analytics Employee Attrition (validé par le professeur selon Syrine ; lien de l’issue à renseigner)
**Extensions :** [À compléter à la S8 : @pseudo-1 → ext/<nom> · @pseudo-2 → ext/<nom>]

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
