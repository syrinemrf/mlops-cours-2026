# ADR-0001 — Choisir le dataset IBM HR et laisser les attributs sensibles hors du modèle

- **Statut :** proposé
- **Date :** 2026-10-21
- **Auteur(s) :** @MohamedAzizKouch
- **Relu par :** en attente de la relecture de @syrinemrf (pull request)
- **Périmètre :** socle (Lab 1)
- **Liens :** `dataset.yaml`, `src/download.py`, `docs/dataset-card.md`, branche `work/aziz/m1`

## Contexte

Le binôme travaille sur le jeu « IBM HR Analytics Employee Attrition & Performance »
(Kaggle). D'après le journal du binôme, il a été validé par l'enseignant ; le lien de
l'issue de validation n'est pas encore renseigné. Le jeu compte 1 470 employés fictifs et
35 colonnes, avec 237 départs (16,1 %).

Trois contraintes pèsent sur la décision :

- le pipeline doit se reconstruire chez le jury, qui n'a pas forcément de compte Kaggle ;
- depuis mon réseau, le serveur OpenML (miroir public) est injoignable (testé depuis
  Windows et depuis WSL le 2026-10-21) ;
- le jeu contient trois attributs sensibles : l'âge, le genre et la situation familiale.
  Prédire des départs d'employés est un usage qui touche à l'emploi, un domaine encadré.

## Options envisagées

| Option | Avantages | Inconvénients |
|---|---|---|
| A. Garder les trois attributs comme variables du modèle | Peut-être un peu plus de performance | Le modèle utiliserait directement l'âge, le genre et la situation familiale |
| B. Les retirer des variables mais les garder dans le CSV | Le modèle ne les voit pas, et on peut quand même mesurer l'équité (Lab 8) | Des variables proches (poste, salaire, ancienneté) peuvent les remplacer |
| C. Les supprimer complètement des données | Plus simple | On ne pourrait plus mesurer l'équité par groupe |

Pour la source des données : téléchargement automatique par OpenML (sans compte), CSV
officiel de Kaggle en étalon, ou un fichier remis à la main (refusé par le cours).

## Décision

Nous retenons l'**option B** : `Age`, `Gender` et `MaritalStatus` sont déclarés dans
`sensitive` de `dataset.yaml`, mais ne sont dans aucune liste de `features`. L'âge est
découpé en deux groupes, moins de 40 ans et 40 ans et plus (948 et 522 employés, ce qui
donne des groupes assez grands). Le choix de 40 ans est un repère courant, mais je n'ai pas
encore de source juridique à citer.

Pour les données, `src/download.py` télécharge depuis OpenML, vérifie les repères du jeu
(1 470 lignes, 35 colonnes, 237 départs, aucune valeur manquante, aucun doublon, trois
colonnes constantes, un identifiant unique) et compare le SHA-256 du CSV produit à celui de
`dataset.yaml`. Cette empreinte a été relevée sur le CSV officiel de Kaggle (version 1, page
consultée le 2026-10-21). L'option `--from-file` permet de repartir de ce CSV.

## Conséquences

- **Positives :** le modèle n'utilise pas directement les attributs sensibles ; les mêmes
  octets sont garantis quelle que soit la source ; la licence relevée sur Kaggle
  (« Database: Open Database, Contents: Database Contents ») est notée dans `dataset.yaml`.
- **Négatives / dette acceptée :** retirer ces colonnes ne supprime pas les proxys, que le
  Lab 8 devra mesurer. La source automatique (OpenML) n'a **pas été testée sur le jeu réel**
  faute d'accès : en attendant, la stage `download` a été enregistrée avec `dvc commit`, à
  partir du CSV de Kaggle, et un `dvc repro` sur un poste sans accès à OpenML échouera tant
  qu'on n'utilise pas `--from-file`. Le jeu est fictif et sa page Kaggle ne documente ni auteur,
  ni source, ni méthode de collecte : les conclusions ne valent pas pour une vraie entreprise.
- **Vérification :** `tests/test_dataset_config.py`, `tests/test_download.py`,
  `tests/test_raw_data.py` (schéma, types, cible, manquantes, doublons, classes, empreinte),
  `tests/test_prepare.py` (le modèle ne voit ni la cible ni les attributs sensibles),
  `tests/test_features.py` (rien de tout cela dans le feature store) et `check-m1`.
