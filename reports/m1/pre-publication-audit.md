# Audit M1 avant publication et J0

Rapport historique de l’audit initial : ses constats décrivent le snapshot d2ea3ca.
Syrine a ensuite autorisé les corrections et exercices de reproductibilité ; leurs
résultats seront consignés séparément sans remplacer les preuves ci-dessous.

Audit du 2026-10-20 sur `work/syrine/m1`, HEAD de référence
`d2ea3ca4154ab4c963abc36ee717d776dc48c22e`. Arbre propre à l’arrivée.
Ce document et les corrections documentaires restent non commités pour revue.
Aucun paramètre, code d’entraînement, dépendance, lock, métrique, version ou alias
modifié ; aucun entraînement, push, PR, merge ou tag exécuté pendant cet audit.

**Avis : contrôles techniques M1 conformes au snapshot ; conformité complète au
guide et remise encore en attente.** Le 18/18 ne couvre pas toutes les consignes
narratives, notamment la promotion du modèle produit par DVC.

## Références et état vérifié

- [Guide M1](../../labs/m1-versioning/README.md), étapes 8 à 10 et rendu ;
  [contrôles officiels](../../labs/m1-versioning/check.sh).
- [Organisation et J0](../../labs/m10-capstone/README.md), organisation du binôme,
  tableau des jalons et « Rendre un jalon » ; lecture pour préparer J0 seulement.
- [Preuves techniques finales](final-validation.md), [sortie 18/18](check-m1-final.log),
  [tests 77/77](final-tests.log), [lint](final-lint.log).
- [État synthétique de cet audit](pre-publication-state.json).

Lecture GitHub réelle le 2026-10-20 : dépôt public, branches distantes
`main=7606b83`, `lab/m0-setup=a60f58c`, `work/syrine/m0=23b452e` ; aucune branche M1.
Seule la [PR M0 #1](https://github.com/syrinemrf/mlops-cours-2026/pull/1) existe,
fusionnée le 19 octobre. Aucune revue M1 n’est donc possible à ce stade. Le travail
local éventuel d’Aziz n’a pas été inspecté et aucune contribution ne lui est attribuée.
Le dépôt vient du template, sans relation GitHub `fork` ; le README du cours
autorise explicitement « Use this template ou fork » : pas d’écart à corriger ici.

Relecture MLflow réelle, sans écriture : **25 runs FINISHED**, trois versions,
alias champion v1 / challenger v3 inchangés. `dvc status` : à jour ;
`dvc status --cloud` : cache et remote `storage` synchronisés.
Les 77 tests et le 18/18 ci-dessus sont les preuves de la finalisation précédente,
pas des suites rejouées pendant cet audit documentaire. Les vérifications à refaire
sur le futur commit d’intégration ne sont pas préjugées.
Contrôles documentaires exécutés ici : `git diff --check`, analyse des liens locaux
et parsing JSON réussis ; `make lint` réussi avec environnement gelé (`UV_FROZEN=true`),
Ruff indique 61 fichiers déjà formatés. Les SHA-256 des huit fichiers techniques
protégés (paramètres, contrat, pipeline/lock, métriques, uv.lock, promote et diagnostic
registre) sont identiques avant/après ; HEAD reste d2ea3ca.

## 1. Divergence DVC / registre : diagnostic confirmé

| Rôle actuel | Paramètres LR | Run ID | AUC exacte | Seuil de décision |
|---|---|---|---:|---:|
| DVC local, non enregistré | C=0,1, balanced | b55a5e9846cb44aeac027426280053e8 | 0,8329744164010682 | 0,8384353741496599 |
| v1 champion, grid search | C=1, sans poids | 5ef49fc5f3e740f28c523b0dcc1ae8c1 | 0,8368507192695321 | 0,5 |
| v3 challenger, grid search | C=0,1, sans poids | 139ae364aa6e4166b2bd19ef533f48e7 | 0,8360754586958395 | 0,5 |

Même contrat, split 80/20 seed 42, 27 prédicteurs et empreinte du CSV exporté
`16e6acc1f69d648c4ec1d3b44efc0179`. Pourtant, ce ne sont pas les mêmes
hyperparamètres, la même fonction de décision ni le même artefact. Un `dvc pull`
restitue aujourd’hui le modèle balanced, pas le champion chargé par
`models:/scoring-model@champion`. Le seuil balanced provient du train, sans
calibration ni recherche de seuil sur test : [audit mathématique](threshold-audit.md).

L’étape 8.4 impose d’enregistrer/promouvoir le modèle du pipeline. Le checker
vérifie un run DVC avec le bon MD5 et, séparément, des versions/alias ; il ne teste
pas l’égalité entre le run du champion et celui des métadonnées du modèle DVC.
Le 18/18 est réel ; l’écart 8.4 est réel aussi. La conservation des alias jusqu’ici
respectait la consigne explicite de Syrine, sans correction silencieuse.

### Solution recommandée, à autoriser avant exécution

| Option | Conformité et arbitrage |
|---|---|
| Enregistrer le run DVC actuel sans changer champion | Trace une version supplémentaire, mais ne réalise pas la promotion demandée8.4 |
| Promouvoir le run DVC actuel C=0,1 balanced | Conforme à8.4 sans nouveau fit, mais remplace le champion convenu par une autre configuration et un autre seuil |
| Aligner DVC sur C=1 sans poids puis promouvoir son nouveau run | Respecte8.4 et le choix pédagogique de configuration du champion ; nouveau fit, lock/preuves/diagnostics à vérifier |

Aligner `train.C: 1.0` et `train.class_weight: none` dans `params.yaml`, en
conservant tout le reste : variables, split, seed, coûts 1:1 et gate ROC AUC 0,70.
Reproduire DVC, enregistrer le **nouveau run DVC exact**, puis le promouvoir si
sa métrique réelle passe la gate. Garder les anciens runs/versions et leurs preuves.
Le challenger convenu reste LR C=0,1 sans poids.

| Effet à vérifier après accord | Conséquence attendue, pas un résultat déjà obtenu |
|---|---|
| DVC | download/prepare inchangés ; train/evaluate recalculés |
| `dvc.lock` | paramètres train, hash modèle et dépendance modèle d’evaluate actualisés ; hashes données inchangés |
| MLflow | nouveau run `protocol=A`, `launched_by=dvc`, commit/MD5/paramètres vérifiés |
| Métriques | comparaison avec C=1 sans poids de la grille ; vérifier les valeurs réelles, ne pas recopier les anciennes |
| Décision | seuil modèle attendu 0,5 ; vérifier métadonnées, run, évaluation et prédiction distante |
| Registre | nouvelle version (probablement v4, numéro à lire) ; v1/v2/v3 préservées |
| Alias | champion vers nouveau run DVC, puis réaffectation explicite du challenger v3 |
| Contrôles | tests/lint, DVC local/cloud, gate, chargement distant et check-m1 à relancer |

Référence empirique existante C=1 sans poids : AP 0,647036, précision 0,714286,
rappel 0,425532, F1 0,533333, accuracy 0,880952, coût 35,
TN/FP/FN/TP=239/8/27/20. DVC actuel : AP 0,639213, rappel 0,297872,
coût 36, matrice 244/3/33/14. Le nouveau fit pourrait reproduire les valeurs de
la grille ; cela doit être mesuré. La différence d’AUC C=1 contre le challenger
C=0,1 est d’environ0,000775 : aucune supériorité statistique démontrée.

`src.promote` applique une gate absolue, pas une comparaison au champion ; il
positionne aussi challenger lors de chaque appel. L’ordre futur est donc :

1. Inspecter/sauvegarder l’état de référence et vérifier infrastructure/ressources.
2. Implémenter et committer les seuls paramètres approuvés, avec tests pertinents,
   puis `dvc repro`. Consigner le run créé et ses paramètres réels.
3. Lire `models/model/MLmodel`, contrôler son `mlflow_run_id`, son seuil, les tags
   MLflow, MD5 du lock et métriques ; ne pas sélectionner un ancien run par sa seule AUC.
4. Définir `M1_DVC_RUN_ID` à cet ID vérifié, contrôler qu’il n’est pas vide
   (`: "${M1_DVC_RUN_ID:?Definir le nouveau run DVC verifie}"`), puis
   `python -m src.promote --run-id "$M1_DVC_RUN_ID"`.
   En cas de gate échouée, arrêter et diagnostiquer ; pas d’abaissement du seuil.
5. `python -m src.promote --run-id 139ae364aa6e4166b2bd19ef533f48e7 --challenger-only`.
   Vérifier les deux alias par `get_model_version_by_alias`, pas les alias de la
   seule liste de versions (champ parfois vide observé).
6. Répéter l’appel sur le même run pour vérifier l’absence de version dupliquée,
   puis vérifier Dummy toujours failed et charger le champion pour cinq prédictions.
7. Ajouter une assertion indépendante : champion.run_id = modèle local.metadata.run_id
   = run DVC retenu ; vérifier paramètres, empreintes et arrondi des métriques.
   Ne pas modifier le checker officiel. `dvc push`, nouvelles preuves et commit de résultats.

Préparer aussi l’évolution du diagnostic `src/verify_registry.py` : il contient
les IDs de Syrine en dur et échouerait légitimement après changement de champion.
Le rendre paramétrable plutôt que copier ces IDs sur le serveur d’Aziz. Aucune
modification de ce code effectuée ici.

Le modèle MLflow contient run ID et dates : un nouveau fit change son hash DVC
même si les prédictions sont identiques. Conserver le lock de référence et les
anciens rapports ; ne pas écraser les preuves du run balanced par les futurs résultats.

## 2. Audit des livrables et exigences restantes

| Exigence | Constat / preuve | État |
|---|---|---|
| Contrat et ingestion IBM HR | version 1/hash source, schéma 1470×35, export 1470×32, séparation27 features/ID/sensibles/cible | Conforme |
| §8.1–8.3 pipeline et évaluation | quatre stages, dépendances, paramètres, seuil local, JSON métriques, lock, MD5 run DVC | Conforme |
| §8.4 champion issu de DVC | champion issu de la grille ; run DVC non enregistré | Écart confirmé |
| §8.5 modification d’un paramètre puis retour cache | non exécuté, déclaré dans final-validation | À démontrer |
| §9 Feast offline/online | apply/materialize, 1176 lignes offline/27 features, 1 profil online/27 features conformes ; requêtes avant snapshot négatives | Conforme au test réalisé |
| §10.1 commit et instructions | 15 commits M1, NOTES, code/contrat/lock/preuves suivis | Local conforme ; publication/intégration/PR/revue/fusion en attente |
| §10.2 clone même poste | cache vide puis pull/repro quatre skips ; lock/métriques identiques, Feast reconstruit | Vérifié à ccf031f, Python et cluster réutilisés |
| §10.3 tout recalculer | double évaluation et deux fits LR concordants ; aucun `dvc repro --force` intégral | Preuve demandée encore manquante |
| §10.4 autre poste/cluster | instructions écrites, aucune exécution indépendante d’Aziz observée | À faire réellement |
| Dépendances | pyproject/uv.lock présents, inchangés dans M1 ; installation vierge non testée | Verrouillage conforme, portée du test limitée |
| Données/modèles dans DVC | cache et remote local synchronisés ; modèles dans MLflow/S3, pas dans Git | Conforme sur le cluster de Syrine |
| Résultats MLflow | 2 smoke +22 grille +1 DVC FINISHED, 3 familles +Dummy, 3 versions et gate | Conforme ; filiation champion/DVC à corriger |
| Exclusions Git | aucun raw/model/FeastDB/venv/env/config.local suivi ; signatures clés privées/GitHub/AWS non détectées | Contrôle ciblé conforme, pas une garantie exhaustive |
| Checker M1 | blob592a04ba431d6314b8bf2787b573c64c91d6b6ee intact, mode755 | Conforme |
| Recherche Jia | quatre problèmes distingués, preuves fichiers/lignes, A/B1/B2 séparés, RQ1–RQ3 hypothèses | Conforme au cadrage, aucune reproduction exécutée |
| Capture et rendu publié | log18/18 présent ; aucune image de capture suivie identifiée ; main ne contient pas M1 | À finaliser avant M2 |

Pour8.5, après autorisation, faire le changement **d’un seul paramètre**, documenter
`dvc status`, `dvc params diff`, `dvc metrics diff`, puis restaurer uniquement
ce changement et constater réellement le retour au cache. Cette démonstration
précède l’alignement final si l’on part du snapshot balanced actuel. Ne pas confondre
ce diagnostic contrôlé avec une sélection sur le test. Garder tous les fichiers
étrangers intacts et enregistrer les résultats sans promettre un cache non vérifié.

Pour10.3, créer un nouveau clone isolé au futur commit final, puis exécuter
séquentiellement `dvc repro --force`, `dvc metrics diff --all` et comparer les
hashes données. Conserver le lock régénéré comme preuve locale, pas comme nouveau
lock commun : les métadonnées MLflow changent. Ce sera un nouveau run ; ne pas le
promouvoir automatiquement. Le scénario forcé n’a pas été exécuté pendant cet audit.
Pour10.4, Aziz rejoue réellement sur son cluster ; les IDs/versions sont locaux à
son serveur. Les guides de reprise ne constituent pas une preuve d’exécution.

**Limite de reprise de grille :** `src.grid_search.run_identity` inclut les octets
du lock complet et de params ; ces fichiers ont changé depuis la grille 9c02057.
`src.compare_runs` recalcule cette identité depuis le workspace courant : son export
historique ne se régénère pas en lançant aveuglément ce script à d2ea3ca. Refaire la
vérification depuis un clone du snapshot 9c02057 ou relire les runs/artefacts du manifeste
historique avec leur provenance. Ne pas relancer22 fits pour contourner cette différence.
La portabilité de ces diagnostics est une correction de code à traiter séparément.

**Effet indirect du changement global de poids :** les neuf configurations RF de
`src/grid_search.py` n’indiquent pas `--class_weight` ; `src.train.parse_args` lit
donc sa valeur dans `params.yaml`. Une simulation en mémoire du parseur, sans
modification de fichier ni fit, confirme qu’un passage global à `none` ferait
passer ces neuf RF de balanced à sans poids. Les anciens runs ne changent pas,
mais la grille rejouée par Aziz serait différente. Recommandation à autoriser en
même temps que l’alignement : rendre le poids balanced **explicite dans les neuf
configurations RF de la grille**, conserver les 22 configurations et ajouter une
vérification de leur indépendance aux defaults DVC. Ne pas masquer cet effet par
une réécriture des manifests existants ni relancer la grille ici. Les tests actuels
vérifient le seuil correspondant aux paramètres effectifs, sans figer le poids RF :
ils pourraient donc rester verts malgré ce changement de protocole.

## 3. Accord dataset, documents et portée scientifique

Syrine confirme pendant cet audit un **accord du professeur reçu par courriel**.
Le message d’accord n’a pas été retrouvé par la recherche ciblée dans la messagerie
connectée ; date/objet/référence restent à consigner. Cela ne remet pas en cause sa
déclaration. Aucun contenu privé de messagerie n’est exporté dans le dépôt.
Le guide prévoit une issue de proposition sur le dépôt du cours avec label `validé`.
Recherches IBM dans le dépôt du cours et issues du dépôt commun : aucun résultat.
Ne pas inventer une URL ni ouvrir une issue automatiquement : référencer le courriel
de façon minimale et demander si ce canal suffit ou si le professeur souhaite une
régularisation dans son formulaire. Ne pas redater l’accord pour prétendre prouver
le respect du délai avant S2.

Corrections documentaires réalisées : README actualisé (M0 fusionné, M1 local,
sections utiles au projet sans supprimer les instructions du cours), dataset card
actualisée après entraînement, statut ADR distinguant décision de Syrine et revue
du binôme, NOTES avec lecture chronologique, journal sans fausse issue, état courant
A dans le cadrage scientifique. Les définitions et expériences B1/B2/RQ ne changent pas.
Les anciens logs et rapports restent des snapshots explicitement indexés dans
[README des preuves](README.md) ; leurs échecs et compteurs historiques sont conservés.

Formulation obsolète encore présente dans `params.yaml` : commentaire « no training
runs in this increment ». Il n’a pas été modifié puisque Syrine interdit de toucher
les paramètres avant accord ; corriger ce commentaire lors de l’alignement autorisé.
Ne pas transformer le statut proposé de l’ADR en « approuvé par Aziz » sans vraie revue.

Le protocole A a consulté le test à répétition pour comparer et choisir ses candidats.
Ses AUC ne sont ni une performance finale indépendante ni un gain sur Jia. B1 reste
le code auteur tel que distribué ; B2 les corrections explicites à conditions comparables.
RQ1 calibration/agrégats RH, RQ2 SHAP/OLAP, RQ3 DVC/MLflow/SSAS restent des hypothèses ;
aucune innovation démontrée ni cube SSAS expérimenté ici.

## 4. Décisions avant publication et J0

1. Autoriser ou refuser l’alignement DVC C=1/sans poids, son nouveau fit et sa
   promotion, avec maintien du challenger actuel et des anciennes versions.
2. Autoriser les preuves 8.5/10.3 supplémentaires et l’adaptation des diagnostics
   locaux au nouveau run et aux serveurs distincts, sans changer les checks officiels.
   Inclure le poids RF explicite pour préserver la grille historique après changement
   des defaults DVC ; aucune nouvelle configuration ni campagne supplémentaire.
3. Consigner la référence minimale de l’accord par mail ; confirmer le traitement
   de l’issue attendue par le guide avec le professeur, sans en inventer une.
4. Relire puis committer les corrections documentaires ; renouveler les preuves
   sur le commit technique retenu. Messages de commits en anglais, sans réécriture.
5. Autoriser ensuite la publication personnelle, comparer le travail réel d’Aziz,
   intégrer via `lab/m1-versioning`, obtenir sa vraie revue de PR puis autoriser la fusion.
6. Vérifier la remise M1 sur main, les clusters des deux membres et les contrôles
   J0, puis autoriser distinctement création/publication du tag `j0`.

Le précontrôle J0 est lu, **pas exécuté** : son script est actuellement mode 644,
donc `make check-m10 JALON=j0` échouerait sur permission. Son appel explicite avec
`bash labs/m10-capstone/check.sh --jalon j0` évite de modifier le vérificateur.
Il vérifie aussi l’existence de `j0` : avant création, ce point doit être annoncé
manquant, pas masqué. Après création locale autorisée, vérifier tout avant publication.

Attention au compteur d’auteurs : deux variantes du nom de Syrine, même courriel,
sont comptées distinctement ; un contrôle automatique vert ne prouve pas le travail
d’Aziz. Ne pas modifier les auteurs, ne pas fabriquer de commit ni d’approbation.
Les contrôles `course-ci` du template sont désactivés pour le propriétaire étudiant :
une CI ignorée n’est pas une exécution des tests du projet.

La procédure exacte, les points de comparaison du binôme, les captures et la remise
sont préparés dans [binome-review-publication.md](binome-review-publication.md).
**J0 n’est ni créé ni déclaré prêt à publier pendant cet audit.**
