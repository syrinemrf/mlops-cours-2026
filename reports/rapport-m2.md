# Rapport comparatif — Kubeflow Pipelines vs Airflow (Lab 2)

**Binôme :** Aziz Kouch et Syrine · **Date :** 2026-11-01 · **Machine :** 12 cœurs, 15,4 Go de RAM (WSL2 limité à 10 Go), Windows + Ubuntu 24.04 ·
**Dataset :** ibm-hr-attrition (IBM HR Attrition)

## 1. Contexte

Nous avons construit le même pipeline de scoring en deux versions : Kubeflow Pipelines (KFP 2.17) et Airflow 3.3. Il contient 6 steps : ingest, validate, prepare, train, evaluate et register. Chaque step lance la commande du Lab 1 (`python -m src.<étape>`) dans l'image du projet `localhost:5001/scoring-pipeline:1.0.1`. Les deux orchestrateurs partagent donc le même code métier, la même image, le MLflow du cours et le S3 SeaweedFS. Seule la couche d'orchestration change : composants et pipeline compilé pour KFP, DAG avec KubernetesPodOperator pour Airflow. Les steps tournent dans des pods du cluster kind. Le dernier step appelle `src.promote`, qui ne change l'alias @champion que si le contrat du binôme est respecté (ROC AUC ≥ 0,70).

## 2. Résultats quantitatifs

| Mesure | KFP | Airflow |
|---|---|---|
| Installation de zéro (min) | 45 | 2 |
| Temps jusqu'au premier run réussi (min) | 6,3 (1er run, images tirées) | 1,1 (run seul) |
| Durée d'un run complet (min) | 2,2 (avec cache) | 1,1 |
| Relance avec les mêmes paramètres (min) | 2,1 (ingest, validate, prepare en cache) | 1,1 (pas de cache) |
| Hot-reload : modifier un step et voir le résultat (min) | ~4 (build, push, compile, upload, run) | ~1 si seul le DAG change, ~4 si l'image change |
| Lignes de code propres à l'orchestrateur | 296 | 71 |
| Mémoire consommée par l'outil (Go, `docker stats`) | 4,1 (cluster entier, non isolé) | 2,05 |

## 3. Analyse qualitative

### Developer experience

KFP demande plus de code (296 lignes contre 71) : il faut décrire des composants avec des artefacts typés, puis un pipeline compilé en YAML. En échange, l'interface montre les datasets, les métriques et la matrice de confusion de chaque run. Le DAG Airflow est court et ressemble à un script Python ordinaire, mais il ne transmet que de petites valeurs par XCom : les fichiers passent par un espace de travail S3 que nous avons dû gérer nous-mêmes.

### Scaling

Chaque step KFP tourne dans son pod avec ses limites de CPU et de mémoire, et le cache évite de recalculer ce qui n'a pas changé : le gain est visible entre le 1er run (6 min 15) et les suivants (environ 2 min). Airflow lance aussi un pod par step avec le KubernetesPodOperator, mais sans cache d'artefacts. En revanche il est plus léger à installer, et l'ordonnancement (planification, reprise) est son point fort.

### Debugging

Dans KFP, on lit les logs d'un step dans l'interface, avec ses entrées et sorties. Mais une erreur de pull d'image ou de timeout oblige à passer par `kubectl describe`. Dans Airflow, les logs de chaque task sont rangés par run, et la relance d'un seul step est simple. Dans les deux cas, le lineage vers MLflow (tags `launched_by`, `kfp_run_id`) permet de retrouver l'origine d'un modèle.

## 4. Recommandation

Nous choisirions KFP quand le pipeline est centré sur l'apprentissage : beaucoup d'expériences, besoin de suivre les artefacts et de profiter du cache. Nous choisirions Airflow quand l'équipe a déjà des DAG, quand le travail est planifié (réentraînement quotidien) ou quand il mélange ML et autres tâches de données. Pour un petit projet comme le nôtre, Airflow est plus rapide à écrire et à lancer. KFP devient intéressant à partir du moment où l'on compare beaucoup de runs.

## 5. Limites de la comparaison

Nous n'avons testé qu'un seul pipeline sur un cluster kind local, avec un petit jeu de données (1470 lignes) : les temps mesurés reflètent surtout le démarrage des pods et le tirage des images. Nous n'avons pas testé KFP ou Airflow sur un vrai cluster géré (GKE par exemple), ni le KubernetesExecutor d'Airflow, ni plusieurs runs en parallèle. La mémoire de KFP n'a pas pu être isolée de celle du reste du cluster. Les temps d'installation dépendent beaucoup du débit réseau (environ 0,5 Mo/s ici), et chaque durée vient d'une seule mesure.
