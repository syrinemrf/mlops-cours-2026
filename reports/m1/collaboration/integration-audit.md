# M1 — audit et proposition d’intégration collaborative

> **Snapshot historique avant autorisation d’exécution.** Les constats et limites
> ci-dessous décrivent la préparation. Les suites effectivement réalisées sont
> dans [le rapport final](../integration/final-integration.md).

Audit du 2026-10-27 (Africa/Lagos). Statut : **proposition à valider par le binôme**.
Aucun merge, cherry-pick, entraînement, promotion, push, PR ou tag effectué.
Le worktree contient uniquement les documents de préparation non commités.
Les validations personnelles antérieures ne valident pas cette intégration.

## 1. État Git réellement observé

| Référence après fetch | SHA | Commits propres depuis la base |
|---|---|---:|
| origin/main | 7606b83e5afbddb30b7a2654d757190ec84e9e09 | base commune |
| work/syrine/m1 et origin/work/syrine/m1 | d740ca5a596c38845b19fa2ce534dfda03cd580f | 18 |
| origin/work/aziz/m1 | 336964faa93f39db54895ee5db18122be2a9f38d | 20 |
| lab/m1-versioning, créée localement pour cette préparation | d740ca5a596c38845b19fa2ce534dfda03cd580f | base Syrine inchangée |

Le fetch SSH a échoué (publickey). Les références ont ensuite été actualisées
par HTTPS depuis le même dépôt public ; la configuration origin SSH est préservée.
Aucune branche lab/m1-versioning locale ou distante n’existait avant sa création.
Le dépôt principal reste sur work/syrine/m1, propre. Aucune branche personnelle
locale d’Aziz n’a été créée ou modifiée ; sa référence distante a été lue.

Worktree isolé : /tmp/mlops-m1-integration-review-20261027-ixvoXF.

Les deux historiques sont indépendants depuis main : 175 fichiers modifiés chez
Syrine, 35 chez Aziz ; 28 chemins modifiés par les deux. Parmi ces 28, seuls
.dvc/.gitignore, .dvc/config et features/feature_store.yaml ont les mêmes blobs.
La comparaison directe peut afficher comme « supprimés » les rapports de Syrine
absents chez Aziz : cela ne signifie pas qu’Aziz les aurait supprimés de son historique.
Les 20 commits propres d’Aziz portent MohamedAzizKouch comme auteur.
Voir [inventaire Git](branch-audit.json) et [commits exacts](aziz-commits.txt).

## 2. Choix communs conservés et variantes

| Sujet | Référence d’intégration Syrine | Variante observée chez Aziz |
|---|---|---|
| Métrique / gate | roc_auc / 0.70 | average_precision / 0.32 |
| Modèle DVC | LR C=1, class_weight=None, seed 42 | LR C=0.01, balanced, seed 42 |
| Seuil de décision | 0.5 | environ 0.838435 avant optimisation exploratoire |
| Âge | <30, 30–44, >=45 | <40, >=40, analyse complémentaire possible |
| Prédicteurs | 13 numériques + 14 catégoriels | 22 numériques + 5 catégoriels |
| Ordinales | neuf échelles traitées comme catégories | ces neuf échelles traitées numériquement |
| Identifiant technique | EmployeeNumber conservé hors prédicteurs | EmployeeNumber supprimé, request_id créé |
| Source automatisée | Kaggle version 1 épinglée, téléchargement déjà éprouvé | miroir OpenML 43696 ; indisponibilité déclarée, CSV manuel et dvc commit |
| Préparation | export 32 colonnes, Feast employee/EmployeeNumber | export 31 colonnes, Feast request/request_id |
| Split demandé | 80/20 stratifié, seed 42 | même configuration ; identité des lignes non vérifiée à partir du cache d’Aziz |

Les neuf variables dont le traitement diffère sont Education, EnvironmentSatisfaction,
JobInvolvement, JobLevel, JobSatisfaction, PerformanceRating, RelationshipSatisfaction,
StockOptionLevel et WorkLifeBalance. Les 27 noms de prédicteurs coïncident, mais
leur espace encodé et leur ordre diffèrent : aucune comparaison de scores ne démontre
une amélioration à conditions égales entre ces deux pipelines.
Age/Gender/MaritalStatus et la cible restent hors prédicteurs dans les deux contrats.
Les coûts 1:1 restent une hypothèse expérimentale, sans justification économique RH.

La clé source.sha256 n’empreinte pas le même objet dans les deux implémentations :
Syrine contrôle les octets du CSV Kaggle source (a5c31e38...), Aziz les octets du
CSV exporté après filtrage/réordonnancement (55a08f10..., download.py:120–125).
Ces valeurs différentes ne prouvent pas une altération de la source.
Les données et lock d’Aziz ne remplacent pas la référence commune.

## 3. Contributions originales proposées et limites vérifiées

### CV stratifiée sur train — 7f9d1ede88f277f6bdcb513c5db4f28c3b4bd59d

Fichiers du commit : params.yaml, src/train.py, tests/test_train.py.
[Source figée : train.py](https://github.com/syrinemrf/mlops-cours-2026/blob/336964faa93f39db54895ee5db18122be2a9f38d/src/train.py#L125-L133).

- CV_FOLDS=5 et CV_METRICS sont définis lignes 52–53 ; fonction lignes 125–133.
- StratifiedKFold(shuffle=True, random_state=seed), sur X_train/y_train seulement
  dans main (lignes 145–146 et 172–174). Le Pipeline complet est passé au
  cross_val_score : imputation/standardisation/encodage sont réappris dans chaque pli.
  Aucun fit global du prétraitement avant la CV dans ce code.
- Moyenne et écart-type des ROC AUC/AP sont calculés. Deux appels cross_val_score
  causent **10 fits**, avant le fit final ; une seule passe multimetrique permettrait 5 fits.
- Pas de n_jobs explicite ni error_score='raise' ; proposer un contrôle explicite
  séquentiel et l’échec sur scores non finis. Ce sont des durcissements proposés,
  pas des corrections déjà appliquées.
- Les tests de CV (test_train.py:61–71) vérifient la répétabilité et les clés.
  Ceux du prétraitement (74–79) vérifient le scaler sur train complet ; ils ne
  démontrent pas, seuls, son isolation à l’intérieur de chaque pli.
- Le module de tests porte un skipif global si train.csv est absent (ligne 15).
  Conserver les tests existants et préparer des tests de CV synthétiques sans skip.
- Ne pas importer tout train.py : il utilise aussi X_test pour signature/exemple
  (180–185), arrondit le seuil loggé (169), retire des métriques/tags de Syrine et
  supprime le modèle local via shutil.rmtree (192). Ces différences ne font pas
  partie de l’ajout CV retenu ; la signature sur X_test n’est pas en soi un fit sur y_test.

### Sensibilité OOF — 104cf5cdec0bfdb7f1445b4425a4f7592789597a

Fichiers ajoutés : src/sensitivity.py (91 lignes), tests/test_sensitivity.py (36 lignes).
[Source figée](https://github.com/syrinemrf/mlops-cours-2026/blob/336964faa93f39db54895ee5db18122be2a9f38d/src/sensitivity.py#L68-L87).

- Lit seulement TRAIN_CSV (75) ; cross_val_predict(Pipeline, méthode predict_proba)
  fournit une probabilité hors pli par ligne, avec 5 plis stratifiés (77–78).
- Rapports hypothétiques FN/FP 1,2,3,5,10 ; minimisation empirique de ratio*FN+FP
  (52–65), ex æquo résolu par le seuil le plus bas. Le seuil infini représente
  explicitement « aucune alerte ». Quatre tests couvrent sens des seuils, rappel,
  référence aucune alerte et cohérence du résumé.
- **Dépendance incompatible confirmée** : import CV_FOLDS depuis src.train (20),
  symbole absent à d740ca5. Le commit ne fonctionne donc pas isolément sur notre base.
- Conserver l’analyse comme diagnostic ; ne pas modifier le seuil DVC 0.5.
  Le coût minimal est estimé sur les mêmes OOF qui servent à choisir le seuil :
  optimisme de sélection, explicitement reconnu par l’ADR d’Aziz (ADR-0002:57).
  Ce n’est ni une calibration ni une performance finale indépendante.
- Avant réutilisation robuste : tests entrées/tailles/probabilités finies, présence
  des deux classes, ratio strictement positif, égalités, et absence d’accès au test.
  Pas de nouvelle analyse chiffrée exécutée pour cet audit.

### ADR, fiche et journal

| Source / commit | Proposition d’intégration |
|---|---|
| ea374524e134ff9f63fdeece633a6ad8ac817fa1 — docs/adr/0001-dataset-rh-et-attributs-sensibles.md | Conserver attribution et statut proposé ; distinguer décision sensible commune, variante âge40 et source OpenML non retenue |
| 39596be9db5bef8c5b6b2ae08197307c3f4d0ca5 — docs/adr/0002-metrique-seuil-et-selection-du-modele.md | Conserver proposition AP/0.32, règle une erreur-type, résultats et sensibilité comme variante datée du poste d’Aziz |
| 6d1daef5ab9e666725a8ba993750e8042a9f2bdb — index ADR | Réconcilier numérotation, auteurs et statuts ; ne pas remplacer l’index existant |
| d466fbe1d90a75e54aa34cb2689f4974a768dbfd — docs/dataset-card.md | Reprendre les limites pertinentes par ajouts attribués ; ne pas remplacer source, typage et contrat de référence |
| 4dcfd3bf29177437f32ed3f8fa971bfcb04b6d32, 336964faa93f39db54895ee5db18122be2a9f38d — journal/NOTES | Ajouter les entrées Aziz datées, signaler les exécutions déclarées et les preuves encore à recueillir |

Collision sémantique : chacun a un ADR-0001 avec un fichier différent. Proposition :
garder ADR-0001 Syrine ; reprendre les deux ADR d’Aziz en 0002 et 0003, en conservant
leurs auteurs, date, provenance et statut proposé. Documenter la renumérotation et
ajouter un encadré d’intégration daté qui précise les décisions communes ; ne pas
réécrire silencieusement la décision initiale d’Aziz. Une éventuelle règle commune
CV/diagnostic peut être un ADR-0004 proposé, après accord réel du binôme.

ADR-0001 Aziz:13–14 attend une issue de validation ; la confirmation fournie par
Syrine est un courriel, sans référence partageable encore consignée. Corriger cette
mention dans un ajout daté, sans inventer d’issue. Le seuil âge40 n’a pas de
justification juridique établie dans cet ADR (40–42) : aucun argument légal ajouté.

Les métriques/versions de l’ADR-0002 appartiennent au pipeline et cluster d’Aziz.
Sa gate AP=0.32 (~deux fois la prévalence) reste une alternative provisoire à discuter.
Sa règle one-SE (975ce4e) n’est pas retenue ici : promote.py:31–34 peut retomber sur
les scores test si la CV manque. Ne pas intégrer ce fallback ni mélanger des scores
CV et test dans une sélection commune. L’écart-type des 5 plis n’est pas un IC95%
ni une preuve de supériorité statistique.

Le journal Aziz déclare un check 18/18 exécuté via bash, des runs et son registre.
Ces exécutions ne sont pas rejouées ici et aucun log officiel M1 n’est suivi sur sa
branche : ce sont des déclarations documentées, pas nos nouvelles mesures.
Le checker a le même contenu sur les deux branches, mais mode 755 chez Syrine,
644 chez Aziz. Conserver le mode exécutable actuel et tous les critères officiels.

## 4. Conflits et méthode d’intégration

Simulation **en lecture seule** : git merge-tree à trois arbres, base main,
sans index/worktree modifié, sans commit de fusion. Elle révèle 25 chemins en
conflit et 77 blocs de marqueurs. Liste complète dans branch-audit.json.

Principaux conflits : dataset.yaml, params.yaml, dvc.yaml/lock, src/train.py,
prepare/download/evaluate/grid_search/promote, features/definitions.py, métriques,
NOTES, journal, dataset card, index ADR et tests partagés. Même lorsqu’un ajout est
sans conflit Git, une collision d’identifiant ADR ou d’hypothèse reste possible.
Un merge complet d’Aziz est donc déconseillé pour le périmètre décidé.

Après validation, procéder par petits lots revus :

1. Appliquer les corrections README/NOTES proposées dans planned-doc-updates.patch,
   puis fusionner les seules entrées documentaires utiles en conservant la chronologie.
2. Extraire la CV de 7f9d1ed dans un nouveau module d’analyse, par exemple
   src/cross_validation.py, avec les tests spécifiques ; laisser src/train.py,
   params.yaml, dataset.yaml, préparation et pipeline officiel intacts. Proposer
   une passe commune à cinq fits qui conserve les OOF et calcule ROC AUC/AP par
   pli, plutôt que refaire les fits pour chaque métrique puis pour les OOF.
   Fixer n_jobs=1, graines et threads BLAS à 1 ; commencer par la LR C=1 fixée,
   sans grille, calibration, choix de champion ou réévaluation du test.
3. Reprendre le commit 104cf5c avec sa provenance/auteur, puis adapter séparément
   l’import de CV_FOLDS au module d’analyse et fixer explicitement n_jobs=1.
   Les fonctions de coût restent diagnostiques ; aucun seuil opérationnel choisi.
4. Reprendre les ADR avec provenance et renumérotation explicites, indexer variantes
   et décisions communes, compléter les tests d’isolation décrits plus haut.
5. Après revue, configurer le worktree avec ses fichiers locaux ignorés, récupérer
   les sorties DVC par le cache/remote existant, puis effectuer la validation complète
   sur le commit d’intégration réel. Ne pas copier de base Feast ni de modèle dans Git.

### Attribution Git

Aucun commit d’Aziz n’est cherry-pické à cette étape. Après accord, 104cf5c se prête
à un cherry-pick -x complet (deux nouveaux fichiers), qui conserve son auteur et cite
le SHA source ; compléter l’adaptation avant de déclarer la branche testable.
Les commits CV et documentaires mêlant des changements incompatibles nécessitent
une extraction revue, avec l’auteur source Aziz conservé pour le travail repris,
un lien au commit original et des commits d’adaptation distincts. Faire valider
cette extraction par Aziz ; pas de nouveau code attribué fictivement à sa personne.
Les messages des nouveaux commits seront anglais, type(scope): description.
Aucun amend, rebase, squash ou force-push des branches personnelles.

## 5. Conséquences DVC, MLflow et données

**Option recommandée : analyses auxiliaires, hors du pipeline actuel.** Aucun import
nouveau dans src/train.py, aucun stage supplémentaire, aucune modification de ses
dépendances existantes. Les fichiers d’analyse et leurs tests/docs ne sont pas des
dépendances des quatre stages actuels. Les stages n’ont donc pas de raison d’être
invalidés par ces seuls ajouts ; le vérifier réellement avec dvc status après intégration.
Aucun dvc repro --force ni nouvelle grille/promotion n’est nécessaire pour cet audit.

Empreintes de référence inchangées à ce stade :

| Objet dvc.lock | MD5 |
|---|---|
| CSV brut exporté | 16e6acc1f69d648c4ec1d3b44efc0179 |
| train.csv | 7eec6596ea2b1d84be50811de74cb9b8 |
| test.csv | c9a203d62f2029c7066a259c02da50da |
| features.parquet | a6c0eacf28225e59b818c9e855c47e16 |
| models/model | 46cf394ffbe298bf1e653379449c8f8f.dir |

Référence MLflow **documentée au 2026-10-20**, non interrogée pendant cet audit :
champion v4, run ef2d3f85ebe3432f9172275c34bbd6ac, LR C=1 sans poids, AUC
0.8368507192695321 ; challenger v3, run 139ae364aa6e4166b2bd19ef533f48e7.
Les analyses futures ne doivent pas altérer ces runs, alias ou versions. Si des
runs de diagnostic sont ensuite autorisés, créer des runs distincts avec protocol=A,
evaluation_role=train_cv_diagnostic et leur identité de données/folds/paramètres ;
ne pas ajouter rétrospectivement de métriques CV aux 22 runs historiques.

**Option demandant une nouvelle autorisation : CV intégrée à train.py.** Même ajouter
une constante changerait son empreinte, car les stages train et evaluate dépendent de ce fichier.
DVC invaliderait ces stages ; un repro effectif créerait de nouvelles métadonnées
MLflow et un modèle de hash différent, même si paramètres/prédictions coïncident.
Il faudrait revalider lock, métriques, signature, objets S3 et filiation, enregistrer
le vrai nouveau run et décider sa promotion sous gate .70, en préservant les versions.
Ajouter un stage CV/OOF à dvc.yaml demande également de convenir sorties, dépendances,
coût calcul/mémoire et nouveau lock. Aucune de ces options n’a été exécutée.

Le test pédagogique a déjà été consulté à répétition. Ajouter une CV train-only ne
rend pas ces anciennes évaluations indépendantes. Les coûts optimisés sur OOF sont
exploratoires ; une estimation d’un seuil sélectionné nécessite une validation
supplémentaire/nichée. Les protocoles scientifiques B1/B2 et XP-Cube restent intacts.

## 6. Vérifications de cet audit et critères ultérieurs

Exécutés : fetch/inspection des refs et auteurs ; comparaison des fichiers, contrats,
paramètres, locks et sources ; preview merge-tree ; vérification de l’absence
préalable de branche officielle ; création du worktree depuis d740ca5 ; comparaison
des blobs des fichiers protégés au snapshot de référence ; contrôle du patch
README/NOTES sans l’appliquer. Les quatre sorties de données présentes dans
le dépôt personnel ont leurs MD5 conformes au lock : brut, train, test, Parquet.
Cette lecture ne peuple pas le worktree et ne valide pas ses futurs changements.
Aucun test officiel n’a été modifié. Voir [résultats de l’audit](audit-checks.json).

Non exécutés : pytest, make lint, DVC repro/push, nouvelle CV, sensibilité réelle,
interrogation/modification MLflow/Feast, make check-m1 sur une intégration modifiée.
Le worktree n’a pas reçu de credentials, cache de données, bases locales ou venv.
Aucun résultat 18/18 d’intégration n’est revendiqué. Le patch documentaire est
**proposé, non appliqué**. Les rapports historiques et branches personnelles sont conservés.

Après accord sur les ajouts : tests ciblés CV/OOF puis suite Python complète,
make lint, dvc status et status --cloud, contrôle des hashes et de la signature,
chargement distant du champion et comparaison au modèle DVC, Feast offline/online,
make check-m1 avec 18/18 et code 0 sur le commit d’intégration. Conserver de nouvelles
preuves datées plutôt que remplacer les rapports personnels antérieurs.
Le replay indépendant d’Aziz et la capture/remise §10.4 restent à documenter réellement.

## 7. Accords attendus du binôme

- Confirmer le module d’analyse auxiliaire hors DVC comme première intégration,
  sans changer le champion ni le seuil 0.5 ; cinq plis, seed42, exécution séquentielle.
- Valider l’extraction/attribution des ajouts Aziz et la renumérotation ADR0002/0003,
  avec distinction décision commune / variante de sa branche et statut proposé.
- Convenir si l’âge40 apparaît uniquement en analyse supplémentaire, sans remplacer
  les trois groupes de référence ; AP/0.32 et one-SE restent des alternatives.
- Convenir du cluster de référence pour les validations communes, de la preuve §10.4
  d’Aziz et des sorties agrégées des diagnostics. Ne pas versionner les OOF individuelles,
  données brutes, modèles, secrets ou bases locales dans Git.

Cette préparation s’arrête avant toute application technique et toute publication.
