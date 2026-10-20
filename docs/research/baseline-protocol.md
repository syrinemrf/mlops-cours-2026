# Baseline Jia et protocoles scientifiques — cadrage A / B1 / B2

**Statut : séparation A / B1 / B2 validée par Syrine, 2026-10-20.** Audit documentaire et statique seulement.
Aucun entraînement scientifique B1/B2, recherche d’hyperparamètres, calibration ou SHAP exécuté. Deux smoke tests pédagogiques A autorisés séparément.
Aucune reproduction de résultat revendiquée. Architecture, dépendances verrouillées,
contrat et pipeline DVC M1 restent inchangés. Aucun avis d’Aziz n’est supposé.

## 1. Fiche critique et références vérifiées

**[J1]** Haojie Jia (2026), *Explainable AI for employee turnover prediction:
a SHAP-based intelligent analytics approach*, **Scientific Reports 16, 31038**.
[Article et DOI 10.1038/s41598-026-60901-3](https://www.nature.com/articles/s41598-026-60901-3).
Publication affichée : 6 juillet 2026 ; « Version of record » : 6 octobre 2026.
Texte en accès ouvert, CC BY 4.0. Consulté le 20 octobre 2026.

**Fiche critique de l’article.** Le travail propose quatre niveaux SHAP sur IBM HR
synthétique, complétés par seuils, équité et comparaison externe. XGBoost est retenu
pour les interactions TreeSHAP, sans supériorité statistique sur la régression
logistique. Résultat annoncé : ROC-AUC **0,773**, IC 95 % **[0,716 ; 0,828]**.
Les limites incluent données transversales, absence de causalité et généralisation
incertaine. L’évaluation externe réentraîne sur Saudi : elle ne démontre pas le
transfert d’un modèle IBM figé. Le balayage des seuils sur le test reste exploratoire,
pas une validation indépendante d’un seuil sélectionné. Les défauts de code ci-dessous
imposent de distinguer protocole annoncé, archive distribuée et résultats recalculés.
Les conclusions scientifiques restent conditionnelles à cette vérification.

**[Z1]** Jia, dépôt logiciel versionné,
[DOI 10.5281/zenodo.20825816](https://doi.org/10.5281/zenodo.20825816),
[métadonnées officielles](https://zenodo.org/api/records/20825816).
Publication du dépôt : **2026-06-24** ; version conceptuelle parente 20825815,
à ne pas confondre avec l’instantané 20825816 audité. Métadonnées : CC BY 4.0.
Le README évoque encore une soumission : ne pas assimiler ce texte à une preuve de
synchronisation avec la version éditoriale d’octobre. Aucun contact auteur effectué.

Archive : [`replication_package.zip`](https://zenodo.org/api/records/20825816/files/replication_package.zip/content),
**10 116 988 octets**, MD5 publié et revérifié :
`7f770b6cd80ab5eadcd99cc13d07828c` ; SHA-256 calculé localement :
`ae0f54e7eb37e6aa609b2a20d1955f5184b98b4fd0609501b84927981de62193`.
Ce contrôle établit l’accord avec les octets servis par Zenodo, pas l’exactitude des
résultats. Archive conservée dans /tmp pour audit, pas recopiée dans le dépôt du cours.
Les données et modèles entraînés ne sont pas fournis ; certaines matrices SHAP le sont.

**[L1]** Niculescu-Mizil et Caruana (2005), *Predicting Good Probabilities With
Supervised Learning*, ICML : [source primaire](https://icml.cc/Conferences/2005/proceedings/papers/079_GoodProbabilities_NiculescuMizilCaruana.pdf).
**[L2]** Lundberg et Lee (2017), *A Unified Approach to Interpreting Model Predictions*,
[NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html).
Ces références sont des points d’entrée pour calibration et SHAP, pas une revue
systématique achevée. Leur existence exclut de présenter la simple application de
ces techniques comme une nouveauté. Référence bibliographique exacte XP-Cube
non trouvée dans le dépôt ; les formulations validées par Syrine sont en section 8.

### Périmètre de l’audit du code

Inventaire de l’archive et lecture des README/guide/requirements, des scripts centraux
pipeline, main, SHAP/v2, robustesse, seuils/équité et des parties pertinentes des
scripts Saudi et de figures. **22 fichiers Python analysés syntaxiquement via AST**,
sans erreur ; cela ne prouve ni leur exécution ni leur exactitude. Aucun module de
l’archive importé, aucun pickle chargé, aucun script de reproduction lancé.
Lecture des tables et en-têtes NPY sans entraînement. `verify_package.sh` ne compte
que les fichiers : ce n’est pas un test de reproduction scientifique.

### Quatre problèmes principaux : qualification et preuves

Les chemins sont relatifs à `code/` dans l’archive [Z1] épinglée ci-dessus.
Aucun impact chiffré sur les AUC publiées n’est établi par cet audit statique.

1. **Partage des estimateurs : défaut confirmé de construction.**
   `step1_main.py:137` conserve le meilleur estimateur, puis ligne 148 :
   ```python
   pipe_fold = search.best_estimator_.__class__(steps=search.best_estimator_.steps)
   ```
   `set_params` et `fit` suivent aux lignes 149–150 ; sauvegarde et prédiction aux
   lignes 175–185. Les composants sont les mêmes objets (identité vérifiée avec les
   constructeurs sklearn locaux, sans fit). Conséquence possible : les refits CV
   écrasent l’état du refit train complet par celui du dernier fold. L’effet exact
   dans l’environnement auteur reste à mesurer. B1 conserve le code ; B2 clonera
   les composants des folds et isolera le refit final.
2. **Jointure des cohortes : défaut confirmé d’alignement.**
   `step1_main.py:64–69` sauvegarde les indices séparément, CSV sans index.
   `step1_threshold_fairness.py:20,83–85` relit le CSV puis utilise
   `test_idx = X_test.index.values` et `df_full.loc[test_idx]` : son RangeIndex
   sélectionne les premières 441 lignes source au lieu du test. Diagnostic sans
   modèle : zéro position correctement réidentifiée ; Male/Female réel 272/169,
   mauvaise sélection 262/179, ces derniers effectifs correspondant à l’archive.
   Conséquence : métriques attribuées aux mauvais groupes. Même motif dans
   `step1_shap.py:331–339`, mais `make_fig6_v3.py:42–77` extrait les groupes du
   vrai X_test : ne pas généraliser le défaut à toutes les figures. B2 joindra le
   manifeste d’indices/ID, avec contrôle ligne par ligne ; B1 reste inchangé.
3. **Bootstrap : divergence confirmée avec l’annonce, pas invalidité générale.**
   `step1_main.py:212–239`, `rng.randint` ligne 213, tire toutes les positions
   ensemble et rejette les tirages monoclasse ligne 223. C’est un bootstrap ordinaire,
   pas stratifié comme annoncé dans l’article. Les proportions de classes et IC
   peuvent varier ; l’effet quantitatif reste inconnu. B1 conserve ce calcul ; B2
   déclarera explicitement la stratification. Un évaluateur commun apparié servira
   aux comparaisons, distinct des sorties natives de chaque protocole.
4. **Robustesse : choix méthodologique discutable, pas bug démontré.**
   `step1_robustness.py:49–57,63–75` utilise 8 configurations XGB contre 48 dans
   `step1_main.py:80–92`. Profondeurs 3/5, subsample/colsample fixés à .8.
   Une différence avec l’expérience principale ne mesure donc pas seulement la seed.
   B1 et B2 garderont la même grille réduite pour leur comparaison appariée.
   Étendre à la grille complète serait une expérience distincte, jamais une
   correction silencieuse présentée comme une simple amélioration du modèle.

### Constats complémentaires et détails d’audit



Les chemins/numéros de lignes suivants désignent les fichiers **dans [Z1]**.

| Constat vérifiable | Conséquence et traitement proposé, sans correction appliquée ici |
|---|---|
| `step1_main.py:137,148–150,175–185` reconstruit le pipeline avec les mêmes objets `steps`, puis les réajuste pour les scores CV | Partage de références : les refits peuvent remplacer l’estimateur refitté sur tout le train par celui du dernier fold, avant sauvegarde/test. Démonstration sans fit avec les constructeurs sklearn locaux : mêmes instances scaler/classifieur. Incidence chiffrée sur les résultats non mesurée ; ne pas affirmer que l’archive correspond à un vrai refit final. Variante corrigée : `clone` pour chaque fold et refit final distinct. |
| `step1_main.py:212–239` utilise `rng.randint` sur toutes les positions du test | Bootstrap **ordinaire**, avec rejet des tirages monoclasse, malgré l’annonce de stratification. Garder la méthode réellement distribuée pour le mode fidèle ; stratification explicite pour le mode corrigé. |
| `step1_main.py:246–271` porte un commentaire DeLong mais calcule des différences bootstrap appariées | Ne pas appeler les p-values « test de DeLong ». Documenter leur définition, la résolution des 1 000 tirages et la multiplicité des six paires. |
| `step1_main.py:64–69` sauvegarde les indices séparément, mais `step1_threshold_fairness.py:20,83–85` relit le CSV sans index et utilise son RangeIndex | Attributs d’audit associés aux premières 441 lignes source au lieu des lignes test. Diagnostic sans modèle sur nos données dans l’ordre source : vrai test Male/Female = **272/169** ; premières 441 = **262/179**, identiques aux effectifs archivés ; zéro position réidentifiée correctement. Le rappel par âge publié n’est donc pas une mesure d’équité fiabilisée par cet audit. Corriger via indices sauvegardés ou jointure sur identifiant hors X, puis vérifier valeurs/labels ligne par ligne. |
| `step1_shap.py:331–339` reproduit cette jointure ; seule la longueur est contrôlée | Risque identique pour cohortes du CSV. `make_fig6_v3.py:42–77` reconstitue au contraire les cohortes depuis X_test : figure et CSV ne suivent pas nécessairement le même chemin. Ne pas conclure que tous les artefacts cohortes sont fiables ou tous faux. |
| `step1_robustness.py:49–57,63–75` utilise une grille XGBoost de **8** configurations, contre **48** dans main | Répétition pas strictement identique de la recherche principale : différence de seed **et** de budget. Reproduire cette variante sous son propre identifiant ; grille complète sur chaque seed seulement comme extension clairement nommée. |
| `step1_threshold_fairness.py:20–54` maximise F1 sur les labels test | Analyse descriptive possible, mais seuil retenu ainsi non validé hors sélection. Aucun seuil opérationnel de notre projet ne sera choisi sur ces scores. |
| `step1_pipeline.py:67–72` fait get_dummies avant split, sans drop_first | Le vocabulaire voit les catégories test. Pas d’apprentissage de cible, mais information transductive à déclarer. En mode corrigé, vocabulaire fixé a priori ou ajusté dans les folds ; ne pas corriger silencieusement le mode fidèle. |
| `step_external_saudi.py:54–70` remplit par médianes avant split | Potentielle fuite de distribution dans la validation externe si des valeurs sont manquantes ; effet effectif non mesuré. Ce n’est pas le protocole IBM. Imputation dans les folds pour une extension corrigée. |
| `step1_shap.py:47` et robustesse utilisent TreeExplainer sans fixer explicitement perturbation/output | Les defaults de la version de SHAP font partie de la reproduction ; verrouiller et inspecter l’espace de sortie, pas supposer des contributions en probabilité. |
| requirements.txt épingle matplotlib 3.10.8, README dit 3.10.0 ; requirements contient aussi python-apt, PyGObject, outils multimédia et nvidia-nccl | Freeze d’environnement large, pas lock minimal portable démontré. Ne pas l’installer dans .venv du cours ; arbitrage de version et environnement isolé à valider. |
| Guide attend AUC 0.7726, CSV performance_test contient **0.7728587742672249** | Distinguer point estimé, moyenne bootstrap et arrondi 0.773 ; aucune modification pour viser arbitrairement un chiffre. |

Le défaut de jointure est vérifié par diagnostic d’indices sans fit. Les autres
incidences quantitatives restent **à mesurer**, et aucune accusation sur l’origine
des tables n’est déduite de l’audit. Demander clarification à l’auteur serait utile,
mais aucun message externe ne sera envoyé sans autorisation.

## 2. Protocole de reproduction B et informations manquantes

Il existe un écart entre intention méthodologique et implémentation. Prévoir deux
identifiants **sans les confondre** : **B1** `jia_as_released_v1` (code distribué intact,
si exécution autorisée) et **B2** `jia_method_corrected_v1` (correctifs approuvés et tracés).
La deuxième n’est jamais une reproduction exacte du logiciel original. Aucun des
deux ne doit être assimilé au protocole A du professeur.

### Données et encodage observés dans le logiciel

Utiliser le **CSV source original 35 colonnes**, même version Kaggle 1 et SHA-256
source que notre ingestion, en préservant l’ordre. Ne pas utiliser notre CSV exporté
32 colonnes : il a retiré les constantes et transformé les codes ordinaux.
Le package attend `ibm_hr.csv` mais ne fournit ni hash source ni version Kaggle.
Notre ancre existante sert au manifeste local ; identité bit à bit avec le fichier
auteur **non établie**. `EmployeeNumber` et trois constantes retirés de X ; conserver
la clé dans un manifeste séparé pour retrouver les individus, jamais comme prédicteur.

- Cible `Attrition == Yes`, entier 1, sinon 0 ; ajouter en mode corrigé un contrôle
  strict des deux modalités avant encodage.
- Garder **Age, Gender, MaritalStatus parmi les prédicteurs** de B, contrairement à A.
- Gender Male=1/Female=0 et OverTime Yes=1/No=0.
- One-hot complet, sans catégorie de référence supprimée : BusinessTravel,
  Department, EducationField, JobRole, MaritalStatus.
- Garder comme entiers Education, EnvironmentSatisfaction, JobInvolvement, JobLevel,
  JobSatisfaction, PerformanceRating, RelationshipSatisfaction, StockOptionLevel,
  WorkLifeBalance. Les 49 noms encodés et les 30 parents sont fournis en JSON dans [Z1].
- Arbres : pas de standardisation. LR : StandardScaler avant SMOTE dans le pipeline.
  Le scaler porte sur toute la matrice encodée, pas seulement les continues.
- Split stratifié **70/30, seed 42** : tailles attendues 1029/441, positifs 166/71.
  Sérialiser identifiants et positions avant toute perte d’index. Test final figé.

### Validation, modèles et espaces de recherche exacts du code

StratifiedKFold(5, shuffle=True, random_state=42). Pipeline imblearn : scaler pour
LR seulement → SMOTE(random_state=42, k_neighbors=5, defaults de la version) →
classifieur. SMOTE uniquement dans le fold d’apprentissage ; pas sur validation,
calibration ou test. Le SMOTE classique génère des valeurs fractionnaires sur
les indicatrices/ordinaux ; reproduire ce choix puis le critiquer, pas substituer
SMOTENC dans une reproduction dite exacte.

GridSearchCV(scoring=roc_auc, refit=True). Versions majeures épinglées dans [Z1] :
Python 3.12, sklearn 1.8.0, xgboost 3.2.0, lightgbm 4.6.0,
imblearn 0.14.1, shap 0.51.0, statsmodels 0.14.6, numpy 2.4.6, pandas 3.0.3.
Conserver les paramètres implicites de ces versions dans le manifeste.

| Modèle | Grille du code `step1_main.py` | Paramètres fixes importants |
|---|---|---|
| XGBoost, 48 configurations | max_depth 3/5/7 ; learning_rate .05/.1 ; n_estimators 200/400 ; subsample .8/1 ; colsample_bytree .8/1 | random_state=42, eval_metric=logloss, tree_method=hist, n_jobs=1 |
| RF, 18 | n_estimators 200/500 ; max_depth 10/15/None ; min_samples_split 2/5/10 | random_state=42, n_jobs=1 |
| LightGBM, 24 | num_leaves 15/31/63 ; learning_rate .05/.1 ; n_estimators 200/400 ; subsample .8/1 | random_state=42, n_jobs=1 ; subsample_freq non précisé, donc subsample peut être inactif selon default |
| LR, 8 | C .01/.1/1/10 ; penalty l1/l2 | random_state=42, max_iter=2000, solver=liblinear ; pas class_weight=balanced ajouté |

Les meilleurs paramètres fournis ne sont pas une nouvelle recherche : XGB profondeur 3,
400 arbres, learning_rate .1, subsample/colsample .8 ; RF 500/profondeur10/minsplit2 ;
LGB 400/63 feuilles/.1/subsample .8 ; LR C=.01/l2. Un futur essai à paramètres fixés
sera un smoke test, pas une reproduction de la recherche ni une preuve de supériorité.

### Évaluation, robustesse et SHAP observés

Seuil 0.5 pour Accuracy/Precision/Recall/F1/confusion. ROC_AUC sur probabilités ;
`PR_AUC` est en réalité **average_precision_score**, pas l’intégrale trapézoïdale.
Brier score ; courbe de calibration quantile, 10 bins. Le mot « calibration » du
balayage de seuil ne signifie pas apprentissage d’un recalibrage sigmoïde/isotone.

En référence archive, XGB : ROC_AUC 0.7728587743, AP 0.4794031116,
Brier 0.1185923964 ; TN/FP/FN/TP = 352/18/47/24. La moyenne bootstrap AUC
archivée est 0.7736643291, bornes 0.7162693751–0.8280025837. Ce sont des
**sorties de l’auteur lues dans l’archive**, pas nos scores reproduits.
Bootstrap 1000 tirages seed42, mêmes positions pour les différences appariées,
percentiles 2.5/97.5 ; utiliser le code réel ou sa variante corrigée selon protocole.

Robustesse : seeds 0,1,7,21,2024 ; XGB seul, grille réduite profondeur3/5,
learning_rate .05/.1, arbres200/400, subsample/colsample=.8 ; split, CV, SMOTE
et modèle changent de seed ensemble. Ce n’est ni cinq validations indépendantes
ni un IC de généralisation à une autre organisation.
Ablation `step1_xgb_stress.py` : RandomizedSearchCV, 80 tirages par variante,
SMOTE contre scale_pos_weight ; la seconde explore notamment scale_pos_weight
uniforme 1–11. Domaine des autres paramètres dans le script : profondeur entiers
2–10, arbres100–1000, learning_rate [.01,.30), subsample/colsample [.5,1),
min_child_weight1–10, gamma/reg_alpha [0,1), reg_lambda [0,2). Ne pas exécuter
cette ablation lourde dans l’incrément M1.

SHAP : partir du XGB retenu et **de son état d’apprentissage identifié** ; calculs
sur X_test et aussi X_train dans v1, puis interactions sur le test. La v2 somme
les contributions dummy par parent avant de calculer mean(abs(contribution parent)).
Interactions : somme des blocs dummy puis facteur 2 pour une paire hors diagonale.
Préserver les quatre niveaux : classement global, dépendances, interactions,
explications individuelles et cohortes. Cas A = proba max parmi les vrais Yes ;
cas B = proba min parmi les vrais No ; cas extrêmes illustratifs, pas preuve d’utilité.
Cohortes Department, JobLevel 1–2/4–5 (niveau 3 absent de cette comparaison),
YearsAtCompany <2/2–5/>5. Les artefacts v1 et figure v3 doivent rester identifiés.
Audit équité code : Gender, MaritalStatus et pd.cut Age [0,30,40,50,100],
**right=True par défaut** : les libellés <30/30-39/40-49/50+ ne reflètent pas
exactement l’inclusion de 30/40/50. Groupes n<20 non scorés. Consigner les bornes,
le nombre de positifs et le diagnostic de jointure avant toute comparaison.

Validation externe Saudi : autre source (DOI cité dans [Z1]), schéma et encodage
numérique spécifiques, réentraînement et sélection sur son propre train/test.
Ne pas y importer des conclusions causales ou la performance IBM. Son inclusion
nécessitera audit source/licence, contrôles d’imputation et budget séparés.

### Ce qui empêche encore une reproduction exacte attestée

- Hash et version source auteur absents ; indices test, test_probas.npz et modèles
  non distribués. Les scripts peuvent les générer mais cela ne certifie pas
  l’identité avec les sorties déposées ; matrice SHAP seule insuffisante.
- Historique exécution/commit, commande complète, OS, matériel, BLAS/OpenMP et
  états exacts des modèles non fournis. Déterminisme bit à bit non garanti par une seed.
- Partage d’objets, jointures, bootstrap, grille de robustesse et versions graphiques
  à arbitrer. Aucun contournement pour obtenir 0.773.
- Version éditoriale vs dépôt à clarifier ; les informations manquantes seront
  marquées « non disponible », jamais comblées comme si l’auteur les avait données.
- Manifeste minimal et compatibilité Python/packages à tester **après autorisation**,
  hors environnement du cours. Aucun téléchargement d’environnement lancé ici.

## 3. Différences avec A et audit des cinq commits M1

| Élément | A : protocole MLOps conservé | B : Jia à isoler |
|---|---|---|
| Split | 80/20 stratifié, seed42, 1176/294 | 70/30 stratifié, seed42, 1029/441 |
| Espace source | 27 prédicteurs ; 13 quantitatives, 14 catégories | 30 prédicteurs source, 49 colonnes encodées |
| Sensibles | Age/Gender/MaritalStatus audit seulement | Inclus dans X, audit séparément |
| Ordinaux | Libellés puis one-hot | Codes entiers conservés |
| Imbalance | Defaults cours class_weight=balanced à évaluer | SMOTE dans CV, pas ajout silencieux de poids |
| Modèles | LR/RF/GradientBoosting sklearn/dummy | XGB/RF/LGB/LR |
| Prétraitement | Imputation/standardisation/one-hot du lecteur | Encodage spécifique, LR scaler puis SMOTE |
| Finalité | Checks pédagogiques, expérience scoring, modèle scoring-model | Reproduction scientifique, espace et registres distincts |
| Seuils | Gate ROC AUC .70 provisoire ; coûts expérimentaux1:1 | Seuil décision0.5 + balayage exploratoire ; aucune gate .70 importée |

Les deux tests se recouvrent potentiellement : ce ne sont pas deux cohortes
indépendantes. **Aucun gain A-versus-B ne sera revendiqué sur leurs AUC.** Pour
comparer deux méthodes, fixer le même protocole, X, split/IDs, folds, budget et rôle
des données ; une ablation des sensibles doit se faire à split/budget constants.

| Commit préservé | Portée examinée et conclusion |
|---|---|
| b380e15 | Ingestion Kaggle version1/hash, schéma, ID et filtrage : appartient à A. Point source réutilisable pour B, pas le CSV filtré. |
| c6541a2 | Dataset card, hypothèses, audit : contexte scientifique initial à compléter par ce document, pas une reproduction Jia. |
| 4cd1b01 | Test des sensibles générique, nouveaux groupes Age : propriété de A préservée ; groupes B restent ceux du code audité. |
| 9a83ee4 | DVC download/prepare, split80/20, source Feast : reste intégralement A. |
| 01c2d44 | Preuves tests/S3/lock et documentation : reproductibilité MLOps, pas preuve de résultats scientifiques. |

**Entraînement A autorisé :** étape 4.3 et les deux smoke tests fixes de 4.5,
LR par défaut puis RF 50 arbres/profondeur 5. Tag `protocol_id=mlops_A_v1`, rôle
`pedagogical_smoke_test`. Le test A 80/20 est exposé pour ces contrôles pédagogiques :
résultats exploratoires, pas une preuve scientifique indépendante après sélection.
Aucun choix d’hyperparamètre/seuil sur ces scores ; aucun grid search ni promotion.
Le seuil analytique balanced du cours est calculé sur train uniquement : ce n’est
pas une garantie de calibration. Coûts 1:1 expérimentaux, non économiques établis.
Aucune évaluation des tests scientifiques B1/B2 dans cet incrément.

## 4. Stratégie d’isolation validée, implémentation scientifique différée

- A garde dataset.yaml, params.yaml, src/, dvc.yaml/dvc.lock, sorties data/processed,
  expérience **scoring**, registre **scoring-model**, remote **s3://dvc-store/scoring**.
- B aura un espace de travail et pipeline distincts, source35 partagée par hash,
  contrat et configurations dédiés, environnement Python isolé. Pas de modification
  de uv.lock/pyproject.toml du cours ni de conversion du contrat A pour réutiliser B.
- Identifiants proposés : `protocol_id=mlops_A_v1`, `jia_as_released_v1`,
  `jia_method_corrected_v1`, puis une famille `research_calibration_v1` pour les
  extensions. Expérience B proposée `research-jia-2026`, sous-espaces DVC/modèles
  dédiés ; aucun espace scientifique créé dans cet incrément.
- Toute sortie MLflow future : protocol_id, source_sha256, feature_schema_sha256,
  split_manifest_sha256, fold_manifest_sha256, training_scope, seed, code_commit,
  environment_hash, correction_patch_hash et origin=author_archive|local_reproduction.
  Les mesures de l’auteur ne sont pas loggées comme nos entraînements.
- Ne pas mélanger les anciens fichiers fournis et les fichiers régénérés : chemins
  distincts, provenance par artefact. Aucun modèle recherche n’écrase @champion du cours.
- Conserver le code auteur intact pour audit ; correctifs minimaux sous patch identifié,
  sans modernisation opportuniste. Toutes dépendances/installations futures requièrent
  l’autorisation demandée par Syrine. Pas de nouvelle branche maintenant.

## 5. Métriques, reproductibilité et comparaisons admissibles

Préenregistrer le tableau de résultats avant calcul final : ROC AUC, AP, accuracy,
precision/recall/F1, TN/FP/FN/TP, Brier, log-loss, calibration par quantiles et bins
fixes, pente/intercept de calibration si estimables. Distinguer **AP** du PR-AUC
trapézoïdal ; calculer les deux si nécessaire sous des noms différents. Fixer
l’écrêtage des probabilités pour log-loss et en conserver le paramètre.
Brier bas seul ne démontre pas une calibration suffisante ; ajouter baseline de
prévalence calculée sur train, fiabilité et incertitude, sans optimiser sur test.

Preuves requises : source d’origine et licences, hashes source/export/code/environnement,
ordre des lignes et des colonnes, manifeste ID/split/fold, CV scores complets,
best_params, états refittés, probabilités individuelles avec IDs/rôle, scores et
scripts de métriques, seeds, threads, RAM/temps, warnings, résidus d’additivité SHAP.
Écrire un manifeste d’exécution immuable ; versionner par DVC, relier au run MLflow.
Les prédictions/lignes restent hors Git et à accès adapté, même sur données synthétiques.

Critères gradués : (a) code et données identifiés ; (b) protocole égal ; (c) résultats
recalculés sous environnement identifié ; (d) écarts expliqués. L’arrondi .773 ou le
recouvrement d’un IC ne suffisent pas. Une tolérance numérique sera fixée avant
exécution selon versions/precision, pas élargie après lecture des résultats.
Les CSV fournis servent de cibles d’audit, pas de sorties attendues forcées dans un test.
Sur des méthodes comparables : différences appariées sur **les mêmes individus**,
bootstrap apparié/stratifié précisé, IC95%, effet pratique et coût de calcul.
Pas de preuve d’amélioration basée uniquement sur p<.05, sur un meilleur seed ou sur
un test dont les labels ont déjà servi à choisir la variante. Documenter comparaisons
multiples et ne pas présenter cinq splits qui se recouvrent comme cinq cohortes indépendantes.

### Extension calibration, après gel de la baseline

Comparer non calibré, sigmoïde et isotone, avec méthode et hyperparamètres sélectionnés
**dans le train seulement**. Une option réaliste est une CV externe de développement
sur le train, avec recherche et calibration internes : chaque calibrateur apprend
sur des prédictions hors apprentissage provenant de folds non suréchantillonnés.
Dans chaque fit du modèle de base, scaler/SMOTE ne voient que ses lignes train.
Les calibrateurs voient la prévalence naturelle, jamais les étiquettes synthétiques
SMOTE ; ne pas calibrer sur les probabilités in-sample d’un modèle déjà ajusté.
Après sélection Brier/log-loss sur développement, refitter le dispositif complet sur
le train et ouvrir une fois le test final. La sigmoïde peut préserver le classement,
l’isotone crée des ex aequo ; une amélioration de calibration n’implique pas une
hausse d’AUC. Seulement 166 positifs dans le train B : risque élevé de surajustement
isotone, à mesurer par validation/IC, pas de garantie de gain.

Les analyses SHAP sur test et les cas extrêmes restent descriptifs après gel. Une
explication qui suggère un nouveau feature engineering oblige à revenir au train
et à disposer d’une nouvelle évaluation indépendante pour toute affirmation confirmatoire.

## 6. Registre des risques de fuite et d’interprétation

| Risque | Garde-fou à vérifier dans les futurs tests |
|---|---|
| SMOTE avant CV, scaler/imputation avant fold | Instrumenter les indices de fit ; pipelines avec rééchantillonnage uniquement côté train |
| Seuil, hyperparamètres, calibrateur choisis avec test | Manifeste des rôles, gel avant accès final ; sélection sur train/CV exclusivement |
| Index CSV réinitialisé et jointure d’audit erronée | Joindre par clé technique hors X ; égalité labels/valeurs/IDs, pas seulement longueurs |
| Réemploi d’instances entraînées entre folds | Cloner les composants ; vérifier refit final et absence de partage d’état |
| SMOTE et proportion réelle | Calibration/validation/test à prévalence naturelle ; conserver les indices synthétiques séparés |
| Vocabulaire one-hot observé sur test | Déclarer le mode fidèle transductif ; variante corrigée fit sur train ou vocabulaire métier fixé avant split |
| Attribut sensible exclu mais proxys présents | Audit conditionnel/incertitude, aucune promesse de suppression des biais |
| SHAP observé puis sélection opportuniste de cohortes/cas | Règles ex ante et journal des analyses exploratoires ; pas d’inférence causale |
| Source synthétique sans temps ni horizon de départ | Pas de validation temporelle inventée ni de prévision de départs futurs réels |
| Validation externe avec preprocessing global | Refaire la séparation avant tout paramètre appris dans la variante corrigée |

## 7. Plan de travail compatible avec la RAM disponible

Mesure pendant l’audit : WSL **3.8 Gio**, environ **1.1 Gio disponible**, swap déjà
fortement utilisé. Le guide auteur recommande au moins 8 Go ; son temps annoncé
n’est pas une estimation validée sur notre poste. Aucun réglage WSL/Docker permanent
ni arrêt/destruction des services M0 sans décision de Syrine.

1. **Maintenant :** document, inventaire, lecture des tables, AST22 et deux diagnostics
   sans fit. Rien d’autre installé ou entraîné.
2. **Après validation du cadrage et autorisation d’environnement :** environnement
   isolé minimal à versions documentées, contrôle d’encodage/split49/30 et tests de
   jointure/clonage ; un smoke test LR puis XGB à paramètres déjà fournis, annoncés
   comme tests techniques. Pas d’accès au test final pour régler ces essais.
3. **Reproduction principale autorisée séparément :** un modèle et un fold à la fois,
   GridSearchCV n_jobs=1, pre_dispatch limité, BLAS/OpenMP à un thread. Le changement
   de parallélisme est tracé et son effet numérique vérifié ; les grilles ne sont
   pas réduites en prétendant reproduire la grille complète.
4. **Budget :** main = 98 configurations × 5 = 490 fits, plus refits et scores CV
   additionnels ; robustesse réduite = 200 fits + refits ; stress = 800 fits +
   refits ; validation Saudi encore distincte. Reporter les étapes lourdes ou utiliser
   un poste adéquat autorisé si la mémoire est insuffisante. Aucun délai promis.
5. **SHAP :** commencer après gel avec un diagnostic réduit étiqueté tel quel, puis
   calcul test complet si mémoire possible. En-têtes fournis : valeurs441×49 float32,
   interactions441×49×49 float32 (~4.24 Mo hors copies) et agrégées441×30×30 float64.
   La mémoire des tableaux n’est pas le pic mémoire des modèles/processus. Lire par
   blocs pour les interactions si possible, conserver le résultat et tracer le procédé.
6. **Robustesse, calibration et externe :** étapes séparées, checkpointées par DVC ;
   pas de produit cartésien immédiat seeds×modèles×calibrateurs×grilles. Étendre après
   estimation réelle temps/RAM, sans sélection du meilleur seed sur test.

## 8. XP-Cube, SSAS et RQ1–RQ3 validées

Formulations validées par Syrine. Ces axes restent des hypothèses de recherche :
leur originalité nécessite une revue approfondie. La référence bibliographique exacte
XP-Cube et le corpus SSAS restent à fournir/vérifier.

| Question | Expérience proposée | Preuve et limite |
|---|---|---|
| RQ1 : calibration probabiliste et fiabilité des prédictions agrégées par groupe RH | Non calibré vs sigmoïde vs isotone ; calibration interne au train ; sommes des probabilités par groupe | Brier, log-loss, fiabilité, PR-AUC, erreur des totaux et IC appariés ; données synthétiques sans horizon temporel réel |
| RQ2 : cohérence mathématique des explications SHAP lors des opérations OLAP | Vérifier additivité, regroupement des dummies et invariants roll-up/drill-down à espace de sortie fixé | Résidus numériques, conservation des sommes et bases ; sigmoid des SHAP logit ne donne pas des contributions probabilistes |
| RQ3 : traçabilité et reproductibilité des mesures prédictives entre DVC, MLflow et SSAS | Recharger les mêmes versions, reconstruire les mesures au même grain | Hashes/manifests/run IDs/partitions SSAS, égalité des comptes/sommes ; aucun cube déployé ici |

### Contrat mathématique proposé pour le cube

Pour une population d’évaluation fixée G : N_G individus uniques, observé
O_G = sum(y_i), attendu E_G = sum(p_i), erreur signée E_G−O_G ; publier aussi
|E_G−O_G| et son incertitude. Il s’agit d’une agrégation de labels synthétiques,
pas d’un forecast RH temporel. Un modèle prédisant la même prévalence à tous peut
bien approximer un total et mal classer les individus : conserver les deux niveaux.

E_G et O_G sont additifs pour des cellules disjointes ; la moyenne de risque est
E_G/N_G, pas une moyenne non pondérée des moyennes. Sommes de pertes Brier/log-loss
additives, moyennes pondérées par N ; **AUC et AP ne sont pas additives** et doivent
être recalculées sur les lignes pertinentes. Les groupes RH qui se chevauchent ne
peuvent être additionnés comme une partition. sum(p_i(1−p_i)) exige une hypothèse
d’indépendance conditionnelle ; ne pas en déduire un IC garanti en présence de
corrélations, incertitude de modèle ou groupes minuscules.

Pour SHAP brut en log-odds : base + sum_j(phi_ij) = marge du modèle. Après regroupement
correct des dummies, cette identité doit rester vraie à une tolérance fixée.
Agrégation OLAP : sum_i(marge_i) = N_G×base + sum_j sum_i(phi_ij), si modèle et base
identiques. **sigmoid(sum marges) n’est pas sum probabilités** ; on ne transforme pas
chaque SHAP logit par sigmoid pour obtenir des « contributions aux départs attendus ».
Une calibration non linéaire change la fonction expliquée : soit expliquer le modèle
composite sur l’espace probabilité avec une méthode justifiée, soit garder deux
canaux explicitement distincts, SHAP marge et probabilités calibrées.

Conserver sum(phi), sum(abs(phi)) et N pour calculer correctement une importance
moyenne par cohorte. L’importance globale d’un parent est mean(abs(sum dummies)),
pas sum(mean(abs(dummy))). Les interactions et les classements top-k ne se
roll-up pas comme des compteurs : conventions et invariants nécessaires.

Grain de faits SSAS proposé : (identifiant technique, snapshot synthétique,
protocol_id, split_role, model_run_id, calibration_id, explanation_id). Clés de
version immuables reliant source SHA, DVC lock/output hash, commit, environnement,
run MLflow et batch/partition SSAS. Une seule prédiction par clé ; aucune double
comptabilisation entre modèles, seeds ou partitions. Employer des dimensions
conformes et règles d’agrégation explicites, contrôler concordance SQL/CSV/cube.
Aucun SSAS ni cube déployé dans cet incrément.

### Validation demandée avant changement d’architecture

- Fournir la référence exacte XP-Cube et approfondir l’état de l’art des RQ validées.
- Valider le maintien de A et l’isolation de B, puis le suivi séparé du mode fidèle
  et du mode corrigé ; décider si une demande de clarification auteur est souhaitée.
- Maintenir les rôles train/CV/test explicites ; A limité aux deux smoke tests autorisés.
- Autoriser séparément l’environnement de recherche et choisir un poste/budget RAM
  approprié. La baseline et la contribution ne seront pas développées implicitement
  dans les scripts du cours.
- Approuver un plan de revue documentée (requêtes, critères inclusion/exclusion,
  tableau des travaux et lacunes) avant toute affirmation de nouveauté scientifique.

## Annexe — éléments contrôlés dans cet incrément documentaire

Cinq commits examinés ; arbre initial propre sur work/syrine/m1 ; pas d’AGENTS.md
applicable trouvé. Références Nature/Zenodo consultées ; archive et MD5 vérifiés ;
22 AST parsés ; tables et en-têtes contrôlés. Diagnostics locaux sans fit : partage
de références des objets Pipeline et divergence de jointure sur split70/30.
Aucune exécution de code auteur, aucune modification d’architecture ou de lock,
aucun résultat MLflow produit et aucun accès à SSAS. Ce document n’est ni une
reproduction achevée ni une validation intégrale du Lab M1.

Empreintes SHA-256 de fichiers audités, relatifs à code/ dans [Z1] :

| Fichier | SHA-256 |
|---|---|
| step1_main.py | f7328dc32b0ba3980a67baeb7e213ec333f24b354eeac2035fe89ebcc85445ec |
| step1_pipeline.py | 52d4bb17a954fe1617f69ddbef2b935beb3f0022c645e79f007e0cb67b11c27b |
| step1_threshold_fairness.py | 8f049eb5743fd4e037aca71167b52201ffca84744fe2308ab2c809630b939e00 |
| step1_robustness.py | e314a6b003688abe39bc512f6c678301db768b4c3d75a11dfb4a6525ac4607e1 |
| requirements.txt | 9d666f3ce8bead2058c6fae8f93853a954af2e3c28c28b7be9c78d715709c206 |

## Comparaison contrôlée B1 / B2 à préenregistrer

Même source/ordre/hash, IDs train/test 70/30 seed42, espace de variables, folds,
modèles, grilles, seeds, SMOTE, métriques et environnement pour les deux variantes.
Corrections sous patch versionné, aucun retrait des sensibles ni changement de split.
Autres preprocessings : ablations distinctes. Évaluateur commun sur les mêmes lignes,
seuil 0.5 et mêmes tirages bootstrap appariés ; garder aussi les sorties natives B1
pour vérifier la fidélité, sans les confondre avec les métriques harmonisées.
Aucun choix de correctif, hyperparamètre ou seuil basé sur le test final.
