# M1 — étapes 5 et 6 : grille et analyse MLflow

Date : 2026-10-20. Branche personnelle work/syrine/m1. Code d’entraînement :
`9c02057`. Les commits antérieurs sont conservés. Aucun push, merge ou promotion.

## Périmètre réalisé

Grille officielle inchangée : Dummy 1, LR 8, RF 9, GB 4, soit **22 configurations**.
Exécution séquentielle, seed42, threads BLAS/OpenMP limités à 1, même contrat, mêmes
27 prédicteurs et mêmes splits 1176/294 (190/47 Yes). Aucun entraînement Jia,
calibration, installation ou changement des dépendances verrouillées.
Tags : protocol=A, protocol_id=mlops_A_v1, evaluation_role=pedagogical_grid_search,
launched_by=grid_search, dataset, data_version=1, data_md5, data_sha256, grid_identity.

**22 runs FINISHED**, 24 au total avec les deux smoke tests. Chaque run possède ses
paramètres, métriques finies et un modèle loggé READY. Registre interrogé : aucun
modèle enregistré ; aucun alias créé ni modifié. Les modèles de grille restent dans
MLflow ; pas de copie locale supplémentaire par run. Les deux artefacts smoke locaux
sont conservés, models/model n’est donc pas le meilleur modèle de la grille.

## Résultats des 22 runs

Tableau complet : [grid-comparison.md](grid-comparison.md), export exploitable
[CSV](grid-comparison.csv), données/contrôles complets [JSON](grid-comparison.json).
Ils contiennent hyperparamètres, ROC AUC, AP, PR-AUC trapézoïdale, precision, recall,
F1, accuracy, coût expérimental, seuil, temps fit et run, run ID et version des données.
Le MD5 de l’export DVC est commun : `16e6acc1f69d648c4ec1d3b44efc0179`.
La version Kaggle 1 désigne la source ; son export filtré est identifié séparément par
MD5/SHA-256, sans assimiler une première empreinte locale à une preuve d’authenticité.

## Candidats descriptifs, sans champion

| Famille / configuration | ROC AUC | AP | Precision | Recall | F1 | Accuracy | Coût |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dummy prior | 0.500000 | 0.159864 | 0.000000 | 0.000000 | 0.000000 | 0.840136 | 47 |
| LR C=1, sans poids | 0.836851 | 0.647036 | 0.714286 | 0.425532 | 0.533333 | 0.880952 | 35 |
| LR C=0.1, sans poids | 0.836075 | 0.667472 | 0.809524 | 0.361702 | 0.500000 | 0.884354 | 34 |
| RF 400 arbres, profondeur8, balanced | 0.799897 | 0.473152 | 1.000000 | 0.042553 | 0.081633 | 0.846939 | 45 |
| GB 100 arbres, profondeur2, lr=0.1 | 0.814282 | 0.505288 | 0.642857 | 0.191489 | 0.295082 | 0.853741 | 43 |

- **LR C=1 sans poids**, run `5ef49fc5f3e740f28c523b0dcc1ae8c1`, a la meilleure
  AUC observée et le meilleur F1 de la grille ; 20 TP, 27 FN, 8 FP, 239 TN.
- **LR C=0.1 sans poids**, run `139ae364aa6e4166b2bd19ef533f48e7`, a la meilleure
  AP, le coût minimal (34) et le meilleur Brier/log-loss observés ; 17 TP, 30 FN,
  4 FP, 243 TN. Son AUC est très proche de celle de C=1 : pas de supériorité
  statistique démontrée, aucun IC ni test d’hypothèse calculé dans cet incrément.
- RF : meilleur AUC avec 400/profondeur8, mais rappel seulement 2/47. Les neuf RF
  ne détectent que 2 ou 3 positifs ; coût 45–46, contre 47 pour Dummy. La profondeur
  améliore généralement le classement, sans garantir de décisions utiles au seuil
  conservé. Plus d’arbres n’améliore pas monotonement toutes les métriques.
- GB : meilleure AUC avec 100/profondeur2 ; meilleur coût GB avec 200/profondeur2
  (38, AP 0.530093). Augmenter profondeur/arbres ne garantit pas une hausse
  d’AUC ; 200/profondeur3 a davantage de rappel mais une AUC inférieure.

## Déséquilibre, poids et seuils

Le test contient 47 Yes / 247 No (prévalence 15.9864%). Dummy prédit No partout,
AUC=0.5, AP=prévalence, accuracy=84.0136%, coût=47 : l’accuracy seule masque ici
l’absence totale de détection des départs.

Voir [audit mathématique préalable](threshold-audit.md). Sans poids : seuil .5.
Balanced LR/RF : seuil .8384353741496599, obtenu uniquement sur train. GB et Dummy
ne reçoivent pas class_weight ; leur seuil reste .5. Aucun changement basé sur test.
La gate ROC AUC .70 demeure distincte du seuil de décision, inchangée et provisoire.

Comparer LR à C constant isole le choix balanced dans cette grille : sauf C=.01,
les AUC/AP observées baissent avec les poids ; le coût augmente de 2 erreurs pour
C=.1, 1 et 10. Les différences exactes sont dans grid-comparison.md. Le cours décrit
une compensation théorique : nos modèles finis/régularisés ne sont pas obligés de
satisfaire cette équivalence. Les comparaisons RF/GB confondent aussi architecture
et pondération : aucune RF sans poids ni GB pondéré dans la grille officielle.
On ne peut donc pas leur attribuer causalement les écarts inter-familles.

Les LR balanced ont ici des Brier/log-loss moins bons que leurs variantes sans poids,
malgré une AUC correcte. Ces pertes mesurent la qualité probabiliste globale ; elles
ne suffisent pas à identifier seules un défaut de calibration. Aucun calibrateur
appris et aucun inverse-reweighting ajouté aux probabilités : ce serait une expérience
ultérieure distincte, avec validation interne et protocole explicite.

**Attention à PR-AUC :** la métrique officielle average_precision est rapportée comme
AP ; l’aire trapézoïdale est loggée séparément. Pour Dummy, la courbe à deux extrémités
interpolée donne environ .579932 malgré AP=.159864. Cette aire n’en fait pas un bon
modèle ; ne pas confondre les deux définitions ni classer des méthodes sur des noms
ambigus. Les deux valeurs sont conservées, sans masquer l’anomalie d’interprétation.

## Limites méthodologiques et sélection future

Ce sont les étapes pédagogiques 5/6 : les métriques test ont été consultées pour
comparer 22 configurations. Sélectionner ensuite un modèle à partir d’elles crée un
biais de sélection ; elles ne sont pas des estimations finales indépendantes. Aucun
meilleur résultat A-versus-Jia revendiqué : espaces et splits différents. B1/B2
restent séparés, inchangés, non exécutés ; aucune innovation scientifique démontrée.

Proposition pour les sélections scientifiques ultérieures, non implémentée :
CV stratifiée 5 folds uniquement dans train, seeds et folds versionnés, preprocessing
ajusté dans chaque fold, hyperparamètres choisis sur ROC AUC out-of-fold. Pondération
et seuil éventuel calculés uniquement à partir de chaque train interne. Calibration
et optimisation empirique d’un seuil nécessitent un niveau interne supplémentaire
ou une validation dédiée, sans consultation du test. Refit après gel. Le test A déjà
exposé ne devient pas indépendant par ce changement ; prévoir une évaluation nouvelle
indépendante pour confirmer des conclusions. Conserver les checks pédagogiques et
identifier explicitement ces nouveaux résultats, sans corriger B1 silencieusement.

## Reproductibilité et reprise réellement contrôlées

- Script : `python -m src.grid_search`, puis `python -m src.compare_runs` avec .env
  chargé localement. Dépendances et données existantes inchangées.
- Une identité SHA-256 par configuration couvre les paramètres effectifs, code train,
  grille, lecteur du contrat, contrat, paramètres, locks, données brutes/exportées et
  splits, versions Python/paquets et threads. Aucune décision de reprise sur le score.
- Première exécution : 22 runs entraînés une fois. Relance réelle : **22 reused**,
  mêmes run IDs, aucun nouveau fit. Un run incomplet/FAILED, sans métriques finies,
  mauvais paramètres ou sans modèle READY ne serait pas réutilisé. Les erreurs de
  sous-processus sont marquées FAILED avec grid_error et manifestées, sans skip.
- Manifeste initial conservé séparément ; manifeste courant, logs de grille/reprise,
  export CSV/JSON, tags et grid-identity.json des runs constituent les preuves.
- Quatre rechargements distants skops, un par famille, réussis ; toutes les métriques
  recalculées concordent à 1e-12 près, entrées exactement les 27 features du contrat.
- LR C=.1 balanced reproduit toutes les métriques de son smoke à 1e-12 près, sans
  prétendre que cela prouve le déterminisme sur tout matériel ou environnement.
- DVC status : données/stages à jour ; hashes de dataset.yaml, params.yaml, uv.lock,
  dvc.lock, train/test identiques aux preuves smoke. Aucun stage réexécuté pour ce test.
- Tests globaux : **60 passed in 14.51s** (9 nouveaux cas de grille/reprise).
  Lint ruff check/format et yamllint relancés ; résultat conservé dans grid-lint.log.

## Incidents et ressources

Préflight : Docker 28.4.0 répondait, trois nœuds Ready, MLflow /health OK ; 3.8 Gio
RAM total, environ 1.5 Gio disponible, swap2 Gio presque plein. En cours de grille,
pression mémoire et disque très forte (PSI enregistrée), swap plein et ralentissements.
Le port-forward MLflow a perdu sa connexion ; make pf l’a rétabli sur les services
existants. Le script a repris ses appels sans réentraîner les runs terminés.
SeaweedFS a redémarré ; état précédent Error, cause mémoire non démontrée. Aucun
redéploiement, cluster recréé, volume supprimé ou service tiers arrêté par ce travail.

Après rétablissement : nœuds Ready et MLflow /health OK, mais docker info a encore
expiré après 12s. Le JSON services décrit cette limite réelle ; le log services
partiel antérieur conserve la perte de connexion. Vérifier Docker Desktop avant la
suite. La grille a néanmoins terminé avec artefacts accessibles et quatre modèles
rechargés. Aucun secret ou fichier brut n’est ajouté à Git.

Warning MLflow récurrent : pip absent de la venv uv, donc non épinglé dans conda.yaml
généré ; pas corrigé par installation opportuniste. Les dépendances minimales du
modèle sont épinglées et les rechargements testés ; reconstruction conda non testée.
DVC status a d’abord été bloqué par le sandbox sur sa base de cache, puis a réussi
avec accès local autorisé. Aucun échec de configuration ni warning de convergence
observé dans les logs de grille ; ces constats ne garantissent pas une absence de
problèmes dans d’autres environnements.

Fenêtre des 22 runs : **1413.961s**, soit 23.57 minutes,
incidents et journalisation inclus. `fit_seconds` mesure uniquement fit du pipeline ;
`run_seconds` inclut la journalisation. Aucun benchmark matériel scientifique revendiqué.

## Décisions nécessaires avant étape 7

1. Syrine doit arbitrer les candidats : LR C=1 sans poids selon la métrique principale
   ROC AUC, ou LR C=.1 sans poids pour le coût/AP. Écart d’AUC très faible, pas de
   preuve statistique de supériorité ; aucun champion officiellement choisi ici.
2. Confirmer que l’éventuelle promotion serait uniquement pédagogique/exploratoire,
   avec coûts 1:1 et gate .70 provisoires, sans portée décisionnelle RH démontrée.
3. Autoriser explicitement l’étape 7 et préciser le run à enregistrer/les alias permis.
   Rien n’a été promu, même si les scores dépassent .70.
4. Vérifier la disponibilité Docker Desktop après les timeouts avant de poursuivre.

Le Lab M1 n’est pas entièrement validé : make check-m1 intégral non exécuté ici,
registre, étapes DVC train/evaluate et feature store restent notamment à terminer.
