# Dataset card — IBM HR Analytics Employee Attrition & Performance

| Champ | Valeur |
|---|---|
| Nom (`dataset.yaml` → `name`) | `ibm-hr-attrition` |
| Source | [Kaggle](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset) ; miroir [OpenML 43696](https://www.openml.org/d/43696) |
| Licence | « Database: Open Database, Contents: Database Contents » (libellé de Kaggle, page consultée le 2026-10-21) ; je n'ai pas relu le texte juridique complet |
| Obtention | `python -m src.download` (OpenML, non testé sur le jeu réel : serveur injoignable depuis mon réseau) ou `--from-file` avec le CSV de Kaggle |
| Version suivie | Kaggle : version 1 (227,98 kB). DVC : remote `storage` (`s3://dvc-store/scoring`), `md5` du CSV produit `ff1c0fbd0344fb02ae5736714c66b5f5` (voir `dvc.lock`), SHA-256 `55a08f109f1ec9ff6f45eaf1aee177eaddb5f13e5f8037ed0d1fc556d340aaec` |
| Taille | 1 470 lignes × 35 colonnes d'origine ; 31 colonnes retenues, 209 612 octets |
| Tâche | Classification binaire supervisée |
| Cible | `Attrition` ∈ {`Yes`, `No`} ; classe positive (à détecter) : `Yes` |
| Responsables de la fiche | @MohamedAzizKouch (branche `work/aziz/m1`), relecture du binôme à venir |
| Dernière mise à jour | 2026-10-21 |

## 1. Motivation

- **Pourquoi ce jeu de données ?** Il est tabulaire, public, de taille raisonnable (1 470
  lignes) et contient des attributs sensibles, ce qui permet de travailler l'équité (Lab 8).
  D'après le journal du binôme, il a été validé par l'enseignant.
- **Qui l'a créé ?** La page Kaggle le décrit comme un jeu fictif créé par des data
  scientists d'IBM. Les champs auteur, sources, méthode de collecte, DOI et période sont
  vides sur la page : je ne peux pas le vérifier.
- **Pour quel usage ?** Apprendre à prédire les départs d'employés. Il n'a pas été conçu
  pour prendre de vraies décisions sur des personnes.

## 2. Composition

- **Une ligne = un employé fictif.**
- **Variables retenues** (déclarées dans `dataset.yaml`) :
  - 22 numériques, dont plusieurs échelles ordinales de 1 à 4 ou 5 (satisfaction,
    implication, niveau de poste, équilibre vie professionnelle / personnelle) gardées comme
    numériques, plus des montants (`MonthlyIncome`, `DailyRate`, `HourlyRate`, `MonthlyRate`)
    et des durées (`YearsAtCompany`, `TotalWorkingYears`…) ;
  - 5 catégorielles : `BusinessTravel`, `Department`, `EducationField`, `JobRole`, `OverTime` ;
  - 3 attributs sensibles gardés dans le CSV mais **hors du modèle** : `Age`, `Gender`,
    `MaritalStatus`.
- **Colonnes exclues :** `EmployeeCount`, `Over18` et `StandardHours` (une seule valeur
  chacune) et `EmployeeNumber` (identifiant, de 1 à 2 068). `src/download.py` vérifie ces
  hypothèses à chaque téléchargement.
- **Répartition de la cible :** 1 233 `No` (83,9 %) et 237 `Yes` (16,1 %). Le jeu est
  déséquilibré.
- **Âge :** de 18 à 60 ans, moyenne 36,9, médiane 36.
- **Qualité :** aucune valeur manquante et aucune ligne dupliquée, vérifié par
  `src/download.py` (repères de `dataset.yaml`) et par `tests/test_raw_data.py`.
- **Données personnelles :** le jeu est fictif et ne contient ni nom, ni adresse, ni contact.
  `EmployeeNumber` est un identifiant fictif, exclu du modèle.

## 3. Attributs sensibles

Déclarés dans `dataset.yaml` → `sensitive`, mesurés au Lab 8, jamais appris par le modèle.
Chiffres sur les 1 470 lignes du fichier brut.

| Attribut | Groupe | Effectif | Taux de départ |
|---|---|---|---|
| `Age` (découpé) | moins de 40 ans | 948 | 19,0 % |
| `Age` (découpé) | 40 ans et plus | 522 | 10,9 % |
| `Gender` | Female | 588 | 14,8 % |
| `Gender` | Male | 882 | 17,0 % |
| `MaritalStatus` | Divorced | 327 | 10,1 % |
| `MaritalStatus` | Married | 673 | 12,5 % |
| `MaritalStatus` | Single | 470 | 25,5 % |

> [!WARNING]
> Ce sont des taux **descriptifs** : ils ne disent rien sur les causes (le poste, l'ancienneté
> ou le salaire diffèrent probablement selon ces groupes). Et le jeu de test ne contient que
> 294 lignes : par groupe, il y aurait très peu de départs (le groupe `Divorced` en aurait
> environ 7). Au Lab 8, il faudra utiliser les prédictions hors-pli de la validation croisée,
> avec des intervalles de confiance. Le seuil d'âge de 40 ans donne deux groupes de taille
> raisonnable ; sa justification juridique n'est pas encore sourcée.

## 4. Collecte et biais connus

- **Jeu fictif :** il ne représente aucune vraie entreprise, donc les conclusions ne se
  généralisent pas. La page Kaggle ne documente pas la façon dont il a été généré ni sa
  période, et indique une dernière mise à jour il y a une dizaine d'années.
- **Déséquilibre :** 16,1 % de départs, imposé par la source.
- **Échelles ordinales :** les notes de 1 à 4 sont traitées comme des nombres, ce qui suppose
  des écarts réguliers entre les niveaux.
- **Une seule version :** Kaggle n'en publie qu'une (version 1).

## 5. Prétraitement

- `src/download.py` : retire le BOM des noms de colonnes, vérifie les repères, garde
  uniquement les colonnes déclarées dans `dataset.yaml` (dans cet ordre), écrit les entiers
  sans décimale et compare le SHA-256 à celui du contrat.
- `src/prepare.py` : ajoute `request_id` (numérotation des lignes, reproductible grâce à
  DVC), découpe 80 / 20 de façon stratifiée avec `random_state` 42 (1 176 lignes de train et
  294 de test, 16,2 % et 16,0 % de départs) et écrit `features.parquet` pour Feast, sans la
  cible ni les attributs sensibles.
- Le prétraitement du modèle (imputation, standardisation, encodage one-hot) est défini une
  seule fois dans `src/dataset_config.py` et appris sur le train seul, à l'intérieur du
  `Pipeline`.
- Aucune autre transformation.

## 6. Usages

- **Prévus :** apprentissage du MLOps (pipeline, validation, déploiement, monitoring,
  équité).
- **Déconseillés :** toute décision réelle sur des employés ; toute conclusion causale.
- **Coûts :** le jeu ne fournit aucune matrice de coûts, `dataset.yaml` garde donc 1 / 1.
  L'ADR-0002 montre comment le seuil de décision change selon des rapports de coûts
  hypothétiques.
- **Cadre réglementaire :** les décisions qui touchent aux employés relèvent d'un domaine
  encadré (par exemple l'annexe III de l'AI Act et l'article 22 du RGPD). Je n'ai pas vérifié
  ces textes : à relire avant tout usage réel.

## 7. Distribution et maintenance

- Licence : celle affichée par Kaggle (voir l'en-tête). Les données brutes ne sont pas dans
  Git : DVC les versionne sur le remote `s3://dvc-store/scoring` de chaque cluster.
- Le jeu n'évolue plus. Toute modification passe par `src/download.py`, jamais par une
  édition à la main.

## Citation

IBM HR Analytics Employee Attrition & Performance [jeu de données]. Kaggle, version 1.
Auteur non précisé sur la page (propriétaire affiché : pavansubhash).
https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset
(consulté le 2026-10-21).
