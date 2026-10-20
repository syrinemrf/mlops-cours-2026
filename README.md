# Cours MLOps — repo du cours (2026)

Repo de travail du cours **Machine Learning Operations** (36 h, cycle ingénieur informatique).
Vous le copiez au Lab 0 et vous y travaillez **jusqu'à la soutenance** : chaque lab y ajoute
une brique, et le résultat final est votre mini-projet.

> [!NOTE]
> **En binôme**, deux organisations au choix : un repo commun (un membre le crée à partir de
> celui-ci, bouton **Use this template** ou fork, l'autre le clone) ou deux repos coordonnés
> (chacun crée le sien). Ajoutez votre partenaire et l'enseignant comme collaborateurs.
> Détails : Lab 0, étape 3.

## Organisation du binôme

**Option A — un dépôt commun** : [syrinemrf/mlops-cours-2026](https://github.com/syrinemrf/mlops-cours-2026).
Membres : Syrine ([@syrinemrf](https://github.com/syrinemrf)) et Aziz
([@MohamedAzizKouch](https://github.com/MohamedAzizKouch)). Chaque membre doit rejouer
le socle sur son propre cluster ; les preuves d’exécution d’Aziz restent à recueillir.
M0 est fusionné dans `main` par la [PR #1](https://github.com/syrinemrf/mlops-cours-2026/pull/1),
commit `7606b83`. Cette fusion ne constitue pas une approbation d’Aziz.
M1 est validé techniquement sur la branche personnelle locale `work/syrine/m1`
(`d2ea3ca`, 18/18 contrôles, 77 tests) ; son intégration et sa revue restent à faire.
Dataset retenu : IBM HR Analytics Employee Attrition, validé par le professeur
par courriel selon Syrine ; référence du courriel encore à consigner, aucune issue
de validation identifiée. Voir [l’audit avant publication](reports/m1/pre-publication-audit.md)
et la [procédure de revue et J0](reports/m1/binome-review-publication.md).

## Cas d’usage

Prédiction pédagogique de `Attrition=Yes` sur les profils synthétiques IBM HR.
Aucune décision RH réelle, représentativité ou relation causale démontrée.

## Architecture actuelle

WSL et Docker sur D:, cluster kind existant à trois nœuds, SeaweedFS pour S3/DVC
et artefacts MLflow, registre `scoring-model`, Feast offline Parquet et online SQLite.
Le pipeline DVC enchaîne `download -> prepare -> train -> evaluate` ; reprise avec
`dvc pull` puis `dvc repro` sur le stockage déjà rempli, selon [NOTES.md](NOTES.md).
Sur un cluster existant, vérifier les services et relancer les port-forwards avec
`make pf`. Les commandes d’installation ci-dessous concernent un nouveau poste.

## Données

[Dataset card](docs/dataset-card.md) et [contrat](dataset.yaml) : Kaggle version 1,
source 1 470 × 35, export 32 colonnes dont 27 prédicteurs ; split stratifié 80/20,
seed 42. `EmployeeNumber` est une clé technique ; Age/Gender/MaritalStatus servent
à l’audit et sont exclus des prédicteurs. Données et modèles binaires hors Git.

## Modèle et résultats

Au snapshot local `d2ea3ca`, champion du registre : LR C=1 sans poids, ROC AUC
0,836851 ; modèle DVC : LR C=0,1 balanced, ROC AUC 0,832974. Leur divergence avec
l’étape 8.4 reste à résoudre après autorisation. Ces scores du protocole A sont
exploratoires sur test consulté à répétition, sans supériorité statistique démontrée.
[Preuves techniques](reports/m1/final-validation.md) ;
[protocoles scientifiques A/B1/B2 et RQ XP-Cube](docs/research/baseline-protocol.md).

## Extensions

Aucune extension individuelle déclarée ici. Les hypothèses XP-Cube RQ1–RQ3 ne
constituent ni une extension validée par le professeur ni une innovation démontrée.
La déclaration de chaque membre reste à faire avant la fin S8.

## Démo

La démonstration J0 porte sur les contrôles M0/M1, DVC, MLflow et Feast locaux.
Le [journal complet M1](reports/m1/check-m1-final.log) est disponible ; la capture
d’écran réelle du commit finalement publié reste à prendre. Aucune vidéo finale
ni application publique n’est annoncée à ce stade.

## Démarrage

```bash
git clone git@github.com:VOTRE_USER/mlops-cours-2026.git && cd mlops-cours-2026
make prefetch    # avant la séance : images du socle (~3 Go)
make up          # cluster kind + registry + stockage S3 (SeaweedFS) + MLflow
make pf          # accès depuis le poste : S3 :8333, filer :8888, MLflow :5000
uv sync          # environnement Python du cours (Python 3.12)
```

Puis suivez le [Lab 0](labs/m0-setup/README.md) jusqu'au bout : `make check-m0` n'est vert
qu'une fois toutes ses étapes faites (bucket de test, smoke tests, premier commit).

Prérequis : Docker, kind, kubectl, helm, k9s, uv, git (installés au Lab 0).
**16 Go de RAM requis** à partir du Lab 2 (8 Go suffisent pour les Labs 0 et 1) : sinon,
prévenez l'enseignant dès la première séance (poste de l'école, VM, ou binôme équipé).

## Contenu

| Dossier | Rôle |
|---|---|
| `labs/` | Énoncés des 10 labs (0 à 9) et du mini-projet, scripts `check.sh` ([sommaire](labs/README.md)) |
| `infra/` | Installation des briques (`versions.env` = versions de référence) |
| `dataset.yaml`, `src/` | Contrat de données et code socle adapté à IBM HR Attrition |
| `docs/` | Gabarits du mini-projet : journal, ADR, dataset card, rapport, soutenance, syllabus |
| `rag/` | Projet Python isolé du Lab 9 (LLMOps) |
| `tools/` | Générateur PDF des énoncés, vérificateur énoncé ↔ fichiers |

Le reste (pipelines, API, manifests, monitoring…) est créé par vous, lab après lab.

## Le mini-projet en bref

Socle vérifié par `make check-m0` … `make check-m8` + une **extension personnelle** par étudiant
+ soutenance de 25 minutes avec **défi en direct**. Jalons : J0 (fin S3), J1 (fin S8),
J2 (fin S11), tag `final` 48 h avant la soutenance. Tout est dans
[`labs/m10-capstone/README.md`](labs/m10-capstone/README.md).

> [!TIP]
> Au jalon J1, remplacez ce README par celui de votre projet (le sommaire du cours reste dans
> `labs/README.md`).

## Signaler une erreur

Ouvrez une *issue* sur le repo du cours (`mlops-itbs-2026/mlops-cours-2026`) ; les corrections par
pull request sont bienvenues, en particulier pour le troubleshooting et les versions d'outils.
