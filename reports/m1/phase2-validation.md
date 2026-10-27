# M1 — tests, DVC et préparation — 2026-10-20

## Résultat et périmètre

Branche `work/syrine/m1` ; les commits `b380e15` et `c6541a2` sont conservés.
Phase 1 : **32/32 tests réussis**, contrôles de qualité réussis. Après ajout de la
préparation : **45/45 tests réussis**, `make lint` réussi à l’échelle du dépôt.
Logs : `phase2-tests.log`, `phase2-lint.log`. Aucun test supprimé, skip ou xfail.
Les rapports du 19 octobre décrivent l’incrément initial et son ancien échec ;
le présent rapport et les preuves datées du 20 le complètent sans effacer l’historique.

## Source et décisions

API Kaggle officielle reconsultée : version 1, libellé « Database: Open Database,
Contents: Database Contents », soit base ODbL 1.0 + contenus DbCL 1.0 selon la
documentation Kaggle déjà citée dans la dataset card. Obligations de notices,
attribution et partage à l’identique des bases dérivées publiques inchangées.
Téléchargement en cwd/HOME vierges avec variables Kaggle/AWS/MLflow absentes :
réussi sans intervention manuelle ni secret, SHA-256 export identique
`27e7bebda91c7e6d0b77e80128c2d9383d70a19a185b51ecfe3bb90f761d2a78`.
Simulation sur le même poste avec le venv du cours ; pas une vraie seconde machine.
L’ancre source est issue du premier téléchargement, pas une preuve indépendante
signée par IBM ou Kaggle. Voir `phase1-validation.json`.

Décisions validées par Syrine : cible Attrition/Yes ; ROC AUC, gate provisoire
0.70 ; coûts FN/FP 1:1 expérimentaux non économiques ; Age/Gender/MaritalStatus
pour audit hors prédicteurs ; EmployeeNumber identifiant uniquement.
Précision, rappel, F1, matrice de confusion et AP (average_precision, résumé de la
courbe précision-rappel, distinct d’une intégrale trapézoïdale) seront suivis lors
de l’entraînement. Aucun score de modèle mesuré dans cet incrément.

Groupes d’âge, bornes gauches incluses : <30 = 326 (91 Yes), 30–44 = 830
(110 Yes), >=45 = 314 (36 Yes). Tous dépassent 300 profils ; aucun ajustement des
bornes nécessaire à ce stade. Les intersections et le test auront de plus petits
effectifs, donc les futures métriques d’équité devront inclure leur incertitude.

## Adaptation du test officiel

`test_sensible_hors_features` supposait `personal_status` dans les catégories,
donc échouait avant de tester sa propriété sur IBM HR. Il utilise maintenant un
petit contrat synthétique indépendant du dataset du projet, retire audit_group
des features et vérifie toujours extra_sensitive/columns. Deux assertions de
comportement vérifient en plus la séparation X/y et le maintien de la mesure
d’équité. Le nom du test et son objectif sont conservés ; check.sh et le lecteur
de contrat sont inchangés. Les 32 tests existants passent après cette correction.

## Pipeline DVC exécuté

- `dvc init`, `.dvcignore` du cours, remote par défaut storage vers
  `s3://dvc-store/scoring`, endpoint local `http://localhost:8333`.
- Credentials exclusivement dans `.dvc/config.local` pour DVC, fichier ignoré
  et permissions 600 ; aucune valeur ajoutée au fichier partagé `.dvc/config`.
- Stage download conforme au cours, avec source et sensitive ajoutés aux params :
  version, hash et colonnes d’audit modifiées doivent invalider sa sortie.
- Stage prepare avec les dépendances code, fichier brut, features/sensitive/target/split
  et section prepare de params.yaml. Le pipeline s’arrête là : ni train ni evaluate.
- `dvc repro` exécuté : download puis prepare réussis ; lock généré et MD5 des
  quatre sorties comparés aux fichiers réels, voir `preparation-validation.json`.
- Espaces de fin de ligne générés dans dvc.lock normalisés sans changer sa
  structure YAML ; pipeline et remote revérifiés ensuite.
- Reprise `dvc repro` : les deux stages sont ignorés, pipeline à jour. `dvc status`
  confirme le même état ; preuve `dvc-repro.log`.
- `dvc push` : **4 files pushed** ; log `dvc-push.log` ; `dvc status --cloud` :
  **Cache and remote 'storage' are in sync.**
- Les quatre objets ont été relus dans dvc-store/scoring/files/md5 et leurs
  contenus comparés octet par octet au local et au lock : `s3-readback.json`.

## Préparation effectivement exécutée

`params.yaml` reprend les defaults du cours sans lancer train et définit
prepare.id_column=EmployeeNumber, timestamp UTC fixe 2026-01-01 (technique).
`src/prepare.py` reprend la préparation de l’énoncé avec gardes : identifiant
positif entier unique, cible binaire sans manquant, sensibles hors prédicteurs,
horodatage explicite avec timezone. Fallback séquentiel d’identifiant conservé
pour un contrat dépourvu de clé, mais non utilisé sur les données IBM existantes.

Sorties réelles : train 1176 × 32, test 294 × 32, positifs 190/47 ; aucun ID
commun, toutes les valeurs de la source retrouvées dans train/test. CSV lisibles
par cfg.read_xy ; 27 features, aucune cible, sensible ou clé dans X.
Parquet Feast 1470 × 29 : clé entière, 27 features, timestamp UTC fixe ; numériques
float64, catégories chaînes ; aucune cible ni sensible. Source hors ligne de toutes
les lignes comme dans le cours ; aucun apprentissage de transformation ou modèle
sur le test. Aucun registre Feast instancié ni store matérialisé dans cet incrément.
Les tests vérifient aussi reproductibilité des octets CSV/Parquet et non-mutation
entrée ; le test de préprocesseur confirme le fit sur train, transform sur test.

## Incidents résolus et limites

Docker Desktop initialement inaccessible sous WSL, API cluster refusée. Syrine a
lancé Docker Desktop ; seuls les trois conteneurs kind existants ont été redémarrés.
Nœuds Ready, deux PVC historiques conservés ; aucun make down/delete/prune.
Premier dvc push : endpoint 8333 inaccessible ; après restauration et make pf,
envoi et relecture réussis. Un contrôle repro lancé pendant le push a rencontré
le verrou DVC ; reprise séquentielle réussie, aucun verrou ou cache supprimé.
MLflow a redémarré et le tunnel initial a perdu sa connexion ; make pf relancé
après démarrage complet des workers, sans modifier le déploiement ni les artefacts.
`curl localhost:5000/health` répond OK ; le client liste smoke-test et Default avec
les variables AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY retirées de son environnement.

Les colonnes, les octets de données et les secrets restent hors Git ; les seules
entrées data/ suivies sont les .gitignore. Aucun git push, PR, fusion, grid search,
promotion ou installation d’infrastructure. Le check-m1 complet n’est pas lancé,
puisque train/evaluate/registry/Feast restent à réaliser ; M1 n’est pas annoncé validé.

## Prochaine étape exacte

Étape 4.3 : implémenter src/train.py en conservant l’expérience scoring, les
métriques complémentaires et le modèle scoring-model pour la future promotion ;
commencer par un smoke test de régression logistique avec pipeline complet ajusté
sur train seulement. Créer ensuite evaluate et étendre DVC. Ne lancer les 20+
entraînements et la promotion que sur demande ultérieure. Aucune nouvelle décision
bloquante pour la préparation ; la gate reste provisoire et l’usage reste pédagogique.
