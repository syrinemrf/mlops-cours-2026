# Dataset card — IBM HR Analytics Employee Attrition & Performance

| Champ | Valeur |
|---|---|
| Nom (`dataset.yaml`) | `ibm-hr-attrition` |
| Source | [Kaggle, pavansubhasht](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset) |
| Licence Kaggle | `DbCL-1.0` : base ODbL 1.0, contenus DbCL 1.0 |
| Obtention | `uv run --no-sync python -m src.download` ; source officielle uniquement |
| Version suivie | Kaggle **1**, publiée le 2017-03-31 ; quatre stages DVC verrouillés dans dvc.lock |
| Taille source vérifiée | 1 470 lignes × 35 colonnes ; CSV source 227 977 octets |
| Export | `data/raw/dataset.csv` : 1 470 × 32 ; 27 prédicteurs, 3 sensibles d’audit, cible, identifiant |
| Tâche / cible | Classification binaire `Attrition`, `Yes` = 1, `No` = 0 |
| Responsables | Syrine (@syrinemrf), Aziz (@MohamedAzizKouch) ; rédaction de cet incrément par Syrine avec Codex |
| Mise à jour | 2026-10-20 ; choix validés par Syrine, revue GitHub du binôme non effectuée |

## 1. Motivation

Jeu pédagogique synthétique de faible volume, validé par courriel du professeur selon Syrine,
pour apprendre le versionnement, la traçabilité, l’évaluation et l’équité d’une
classification des départs. Les données sont décrites comme fictives, créées par
les data scientists IBM dans la [description Kaggle](https://www.kaggle.com/api/v1/datasets/view/pavansubhasht/ibm-hr-analytics-attrition-dataset).
Elles ne décrivent pas des observations vérifiées d’employés réels. Le projet ne
permet ni décision RH opérationnelle ni conclusion causale sur les départs.
La référence/date du courriel reste à consigner ; aucune issue de validation n’a
été identifiée. L’accord n’est pas présenté comme une référence GitHub observée.

## 2. Composition

Une ligne représente un profil d’employé synthétique. La source contient 26 colonnes
entières et 9 textuelles, sans date d’observation ou historique temporel réel.
Le fichier téléchargé est vérifié avant filtrage : nom et ordre des 35 colonnes,
types entiers non négatifs, domaines catégoriels/ordinaux, absence de valeurs
manquantes et de doublons exacts, identifiant positif unique et distribution cible.

Résultats effectivement mesurés : **1 233 No / 237 Yes**, soit **16,12 % Yes** ;
**0 valeur manquante, 0 doublon exact**. `EmployeeNumber` est unique et conservé
comme clé technique ; il est absent des features retournées par `cfg.split_xy`.
Les constantes `EmployeeCount=1`, `Over18=Y`, `StandardHours=80` sont exclues.
Ces contrôles bloquent toute dérive par rapport à la version épinglée, sans
supprimer arbitrairement des lignes. L’empreinte source protège aussi les valeurs.

Schéma exporté : 13 quantitatives + 14 catégorielles (dont 9 ordinales nominalisées)
+ `Age`, `Gender`, `MaritalStatus` pour l’audit + `Attrition` + `EmployeeNumber`.
`cfg.columns` contient 31 colonnes ; l’identifiant supplémentaire porte l’export à 32.
Il n’est pas déclaré comme attribut sensible pour contourner le lecteur.
Voir [le rapport de conformité](../reports/m1/ingestion-validation.json) pour les
listes de colonnes, les effectifs et les types source ; aucune donnée brute dans Git.

## 3. Attributs sensibles

Choix validé par Syrine : conserver `Age`, `Gender`, `MaritalStatus` pour l’audit, les exclure
des prédicteurs. Le lecteur officiel les gère via `extra_sensitive` ; le retrait
n’élimine pas les proxys potentiels (rôle, ancienneté, salaire…).

- `Gender` : Female 588, Male 882 ; ce codage binaire source n’est pas une description exhaustive du genre.
- `Age` : 18–60 ans ; groupes `<30`, `30-44`, `>=45`, bornes gauches incluses (effectifs 326, 830, 314).
- `MaritalStatus` : Divorced, Married, Single ; attribut social d’audit, sans en déduire de statut juridique.

Effectifs par groupe dans le rapport ; aucun groupe « nan » produit par le lecteur.
L’usage des groupes, les petits effectifs et l’incertitude des métriques seront
à examiner avant tout résultat d’équité. Les modèles pédagogiques ont été entraînés ;
aucun résultat d’équité par groupe n’est établi dans cet incrément.

## 4. Collecte et biais connus

La date Kaggle 2017-03-31 est une date de publication, pas une période de collecte.
La procédure de génération, les relations temporelles et la représentativité d’une
population RH réelle ne sont pas établies par cette source. Pas de validation
chronologique réelle possible. Les taux source ne sont pas une prévalence métier.
Le moment auquel salaire, satisfaction, promotion et ancienneté ont été mesurés
relativement au départ n’est pas établi : risque de fuite temporelle à investiguer.
Ne pas interpréter une association comme l’effet causal d’une politique RH.

## 5. Prétraitement

L’ingestion décode UTF-8 avec BOM, valide la source, applique un mapping fixe des
niveaux ordinaux, filtre/réordonne les colonnes et écrit un CSV UTF-8 à fins de ligne LF.
Aucun paramètre n’est appris sur les données lors de cette transformation.

- **13 quantitatives** : `DailyRate`, `DistanceFromHome`, `HourlyRate`, `MonthlyIncome`,
  `MonthlyRate`, `NumCompaniesWorked`, `PercentSalaryHike`, `TotalWorkingYears`,
  `TrainingTimesLastYear`, `YearsAtCompany`, `YearsInCurrentRole`,
  `YearsSinceLastPromotion`, `YearsWithCurrManager`. Unités monétaires non garanties
  par les métadonnées : ne pas les présenter comme un salaire réel en dollars.
- **5 catégorielles nominales** : `BusinessTravel`, `Department`, `EducationField`,
  `JobRole`, `OverTime`. Le voyage a un ordre de fréquence intuitif mais est traité
  nominalement pour ce premier incrément.
- **9 ordinales** : Education (1–5), EnvironmentSatisfaction (1–4), JobInvolvement
  (1–4), JobLevel (1–5), JobSatisfaction (1–4), PerformanceRating (1–4 ; valeurs
  observées 3 et 4), RelationshipSatisfaction (1–4), StockOptionLevel (0–3),
  WorkLifeBalance (1–4). Codes convertis en libellés préfixés par le rang dans
  `src/download.py`, puis **one-hot** selon le lecteur existant. Le rang reste
  documenté mais n’est pas exploité comme distance numérique ou contrainte monotone.
  Les libellés JobLevel/StockOptionLevel restent neutres, sans inventer leur sens RH.

Le préprocesseur implémenté utilise médiane + standardisation des quantitatives,
mode + one-hot (`handle_unknown=ignore`) des catégories. Il est **ajusté sur
le train seulement**, puis appliqué au test dans la pipeline sklearn. Pas de
calibration ni d’encodage appris sur le test. Le test ciblé vérifie que transform
ne change pas les moyennes apprises sur le train. La sélection pédagogique des
candidats s’est en revanche appuyée sur les scores du test répété : voir la limite ci-dessous.

Split opérationnel conservé : **80/20, graine 42, stratification sur la cible**,
conformément au script de préparation fourni dans l’énoncé, désormais implémenté.
Sorties effectivement produites : **1 176 train / 294 test**, **190 / 47 Yes**, aucun identifiant
commun. `prepare.id_column: EmployeeNumber` est fixé dans
`params.yaml` pour que la préparation conserve la clé existante, sans la dupliquer.
L’horodatage Feast est un artifice technique fixe, pas une date réelle.
Le protocole A du cours a comparé 22 configurations sur ce test et retenu ses
candidats à partir de ces scores : ce test n’est plus une estimation finale indépendante
après sélection. Les seuils de décision n’ont pas été optimisés sur le test.
Les sélections scientifiques futures nécessitent une CV sur le train et un test
final distinct préservé, selon le cadrage séparé B1/B2 ; pas de comparaison de gains
entre splits ou espaces de variables différents.

## 6. Usages

Usage : démonstration pédagogique MLOps uniquement, sans décision individuelle,
sans inférence causale et sans déploiement RH réel. Les noms techniques du cours
restent `scoring`, `scoring-model` et `s3://dvc-store/scoring`.

**Choix validés par Syrine le 2026-10-20 (coûts neutres et gate provisoire) :**

- Primaire `roc_auc`, gate **0.70**, conservée du cours et fixée avant toute mesure
  de modèle ; elle mesure le classement, pas l’utilité RH. Ne pas l’abaisser pour
  faire passer un modèle. Le baseline constant aurait ROC AUC 0.5.
- Rapporter également average precision (référence naïve proche de 0.1612), rappel,
  précision, F1, matrice de confusion, calibration et résultats par groupe avec
  incertitudes. Une accuracy majoritaire de 83.88 % n’est pas une preuve d’utilité.
- FN : profil avec `Yes` manqué ; FP : profil `No` signalé à tort, susceptible de
  mobiliser une intervention inutile et de stigmatiser. Aucune valeur financière
  de ces erreurs n’est fournie. Coûts **1:1**, hypothèse expérimentale neutre
  recommandée par l’énoncé quand la matrice métier est inconnue, pas une vérité RH.
  Le ratio crédit 5:1 n’est pas repris. Avec probabilités calibrées et sans poids,
  cela correspondrait à un seuil de décision 0.5 ; ce seuil n’est pas la gate ROC AUC.
  La correction par poids du cours devra être vérifiée empiriquement/calibrée ;
  les poids ne garantissent pas une correction exacte des probabilités. Le seuil
  analytique balanced observé est 0,838435, calculé sur le train, sans calibration
  apprise ni optimisation empirique sur le test ; voir [l’audit du seuil](../reports/m1/threshold-audit.md).
- À valider : action RH envisagée, capacité d’intervention, coût relatif FN/FP,
  budget de faux positifs et seuil de rappel. L’exclusion des sensibles et les
  groupes d’âge sont validés pour A ; leur pertinence RH réelle reste à étudier.
  Quatre versions sont enregistrées ; champion et challenger sont pédagogiques.

## 7. Distribution et maintenance

Source originale Kaggle, version 1 ; aucun miroir. API publique testée sans jeton.
`--from-file` accepte un ZIP ou CSV obtenu depuis la même version officielle et
vérifie la même empreinte ; ce n’est pas une alternative de provenance.
Si Kaggle exige ultérieurement une connexion, utiliser le client officiel et une
configuration locale à accès restreint (jamais un jeton dans le chat ou Git), puis
ce mode hors ligne. Aucun nouvel outil d’authentification installé ici.

SHA-256 des **octets CSV source**, BOM et CRLF inclus :
`a5c31e38bd7fafc9bc333884eb181b06b41b8e5e488e8f7ccb27199fb3be7659`.
Cette valeur a été **calculée lors de notre premier téléchargement**, puis épinglée
et revérifiée au téléchargement suivant. Elle détecte une modification future ;
elle n’est ni une signature IBM/Kaggle ni une vérification indépendante d’authenticité.
Le ZIP peut changer de métadonnées de compression : le verrou porte sur le membre CSV.
L’empreinte export est distincte et enregistrée dans le rapport de conformité.
Aucun changement silencieux de version/hash : revue du code/contrat requise.
Le stage DVC download dépend aussi des clés `source` et `sensitive` du contrat ;
`dvc.lock` conserve les empreintes des quatre sorties download/prepare et du modèle
train ; evaluate suit les métriques JSON dans Git. Le manifeste local est ignoré avec le CSV.

La [documentation officielle Kaggle](https://github.com/Kaggle/kaggle-cli/blob/main/docs/datasets_metadata.md)
associe le libellé observé au slug `DbCL-1.0` :
[ODbL 1.0 pour la base](https://opendatacommons.org/licenses/odbl/1-0/) et
[DbCL 1.0 pour les contenus](https://opendatacommons.org/licenses/dbcl/1-0/).
Conserver source, notices et liens de licence ; attribuer la base dans les résultats
publics. Une base dérivée utilisée publiquement relève du partage à l’identique
ODbL et doit être accessible, ou accompagnée de la méthode des modifications selon
les conditions de la licence. Le code de transformation est fourni ici ; cela ne
signifie pas que tout code ou tout modèle reçoit automatiquement cette licence.
Aucune redistribution brute dans Git. Conserver ces notices avec une éventuelle
copie DVC partagée et examiner ses conditions de diffusion avant publication externe.

## Citation

IBM data scientists, données fictives ; distribution Kaggle par **pavansubhasht**.
*IBM HR Analytics Employee Attrition & Performance*, version 1, 2017-03-31.
https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset

Licence et version observées le 2026-10-19 via l’API officielle ; extrait de
métadonnées dans `reports/m1/source-metadata.json`. Décision technique mise en œuvre,
proposée à la revue du binôme :
[ADR-0001](adr/0001-pin-ibm-hr-ingestion.md).

## État technique et limites — alignement du 2026-10-20

DVC `storage` pointe sur `s3://dvc-store/scoring` ; credentials dans config.local
uniquement. Le pipeline possède download, prepare, train et evaluate.
CSV train/test : 1176 × 32 / 294 × 32 ; Parquet Feast : 1470 × 29 (27 features,
identifiant, horodatage UTC fixe). Sensibles et cible absents du Parquet ; aucune
imputation ou standardisation apprise à cette étape. La source Feast contient les
features de toutes les lignes comme dans le cours, sans cible ; les modèles
s’entraînent exclusivement à partir de train.csv.
29 runs MLflow terminés : 2 smoke, 22 grille, ancien DVC et 4 nouveaux fits de
reproductibilité/référence. Modèle DVC et champion v4 LR C=1 sans poids,
AUC 0,836851, seuil 0,5 ; challenger v3 conservé. Écart 8.4 résolu, exercices 8.5
et 10.3 réussis : données inchangées et probabilités reproduites exactement.
18/18 contrôles, 85 tests et lint validés. Feast offline/online vérifié ;
replay indépendant d’Aziz 10.4 encore requis.
[Preuves de l’alignement](../reports/m1/alignment-validation.md),
[audit avant publication](../reports/m1/pre-publication-audit.md).
Les anciens rapports décrivent leur incrément, sans remplacer l’état actuel.


## Complément d’intégration du 2026-10-27

Les diagnostics CV/OOF d’Aziz sont adaptés dans des modules indépendants, sur le
train et les 27 prédicteurs de ce contrat. Les propositions AP/gate0,32, deux groupes
d’âge et encodage numérique des neuf échelles ordinales restent des variantes
historiques proposées (ADR0002/0003), sans remplacer cette fiche de référence.
La CV réajuste le prétraitement dans chaque pli ; les analyses de seuil sont
exploratoires, avec coût optimiste quand elles choisissent/évaluent sur les mêmes OOF.
Aucun coût économique, effet causal, statut juridique du seuil d’âge40 ou nouveauté
scientifique n’est établi par ces ajouts. Accord dataset par courriel selon Syrine,
référence/date du message restant à consigner. Voir le rapport d’intégration M1.
