# Mes notes du cours MLOps — Syrine

## Lab 0 : environnement et organisation

Binôme (option A) : Syrine (@syrinemrf) et Aziz (@MohamedAzizKouch) ;
dépôt commun `syrinemrf/mlops-cours-2026`.
Travail individuel de Syrine sur `work/syrine/m0` avant comparaison avec Aziz.
Dataset retenu : IBM HR Analytics Employee Attrition, validé par le professeur
(information fournie par Syrine). Son adaptation appartient au Lab 1, après validation M0.

### Comprendre les composants

- Docker exécute les conteneurs : ici les trois machines du cluster kind et le registry.
- kind fournit Kubernetes localement : un control-plane et deux workers.
- Kubernetes gère les pods, services et volumes persistants des applications.
- Le registry `localhost:5001` conservera les images du pipeline et de l’API.
- SeaweedFS fournit le stockage objet compatible S3 ; un bucket regroupe des objets.
  `mlflow-artifacts` contient les artefacts MLflow, `dvc-store` les futures données
  du projet et `mlops-test` les objets des tests M0.
- MLflow conserve les paramètres, métriques et artefacts des expériences.
  Ses métadonnées sont dans SQLite sur PVC ; les fichiers passent par son proxy vers S3.
  Pour HR Attrition, il permettra de comparer les expériences de prédiction des départs.
- uv utilise Python 3.12 et `uv.lock` pour reproduire les dépendances dans `.venv`.
- DVC associe des fichiers de données à leurs empreintes et envoie leur contenu dans S3.
  Git suit les petits fichiers `.dvc`, pas les données RH elles-mêmes.

### Reprendre une séance

Dans le dépôt, vérifier `docker ps -a`, `kind get clusters` et `kubectl get nodes`.
Si les trois conteneurs kind existants sont arrêtés, les redémarrer après vérification :

```bash
docker start mlops-lab-control-plane mlops-lab-worker mlops-lab-worker2
kubectl get nodes
make pf
set -a && source .env && set +a
uv run --no-sync python labs/m0-setup/smoke_mlflow.py
make check-m0
```

Les port-forwards exposent MLflow sur http://localhost:5000, S3 sur
http://localhost:8333 et le filer sur http://localhost:8888.
Les logs des tunnels sont dans `/tmp/mlops-port-forward/`.
Ne jamais recréer le cluster pour résoudre un simple arrêt : cela détruirait ses données.

### Secrets

`.env`, `.venv/` et `.dvc/config.local` sont ignorés par Git.
Les identifiants DVC doivent rester dans la configuration locale (`--local`).
Le smoke test DVC est isolé dans `/tmp/dvc-smoke`, pas dans le projet du Lab 1.

### Validation et remise

Le contrôle officiel comporte 19 vérifications. Le dernier demande que le smoke test
soit suivi par Git et que HEAD soit contenu dans une référence distante locale.
Une validation technique locale ne remplace pas le push ni la PR relue.
Aucun push ne doit être exécuté sans accord de Syrine.

Après autorisation de publication et validation complète, afficher dans le terminal :

```bash
make check-m0
```

Agrandir le terminal pour afficher les 19 lignes et le récapitulatif, puis utiliser
`Win + Maj + S` pour conserver une capture destinée à l’espace de rendu.
Capturer aussi le run `hello-mlops` et son artefact `hello.txt` dans MLflow.

### Comparaison avec Aziz et PR

Après publication autorisée des branches personnelles : comparer dans GitHub
`work/syrine/m0` avec la branche personnelle d’Aziz (nom à confirmer).
En local, `git diff work/syrine/m0...origin/<branche-Aziz>` permet une comparaison
sans changer de branche ni modifier les fichiers. Relire ensemble les différences.

Préparer ensuite, d’un commun accord, `lab/m0-setup` avec les commits retenus ;
cette branche existe déjà localement : vérifier son contenu avant de la modifier.
Ouvrir une PR vers `main`, titre `lab/m0-setup : setup OK`, joindre la sortie réelle
et la capture de `make check-m0`, puis faire relire et approuver par Aziz.
La fusion et tout changement de branche restent à faire après accord de Syrine.

### Correctif SeaweedFS vérifié au démarrage

Kubernetes injecte par défaut des variables pour les Services existants. Le Service
nommé `s3` injectait `S3_PORT=tcp://…:8333`. SeaweedFS 4.48 lit cette variable
comme l’option numérique `s3.port` et quittait avec une erreur de conversion.
`enableServiceLinks: false` dans le pod SeaweedFS supprime cette collision ; les
services restent joignables par DNS. Le correctif conserve l’image et les PVC du cours.

### Correctif des port-forwards

Avec `.ONESHELL`, le texte complet de la recette `make pf` figure dans les arguments
du shell. Un `pkill -f "port-forward …"` trop large pouvait donc tuer cette recette.
Les motifs sont maintenant ancrés sur `^kubectl ` pour arrêter uniquement les tunnels
existants. Les commandes, ports et journaux restent ceux du Makefile du cours.

### Lecture des artefacts depuis WSL

MLflow 3.16.1 peut détecter les téléchargements présignés et tenter de joindre
directement `s3.storage:8333`, nom interne au cluster. Pour conserver le mode proxy
du cours, `.env` contient localement `MLFLOW_ENABLE_PROXY_MULTIPART_DOWNLOAD=false`.
Charger `.env` avant les téléchargements avec le client Python. Aucun identifiant
ni URL présignée n’est ajouté à Git.

### Résultat final du 2026-10-19

Branche personnelle publiée ; `make check-m0` : **19/19 vérifications OK — Lab 0 validé**.
La sortie complète est conservée dans `reports/m0/check-m0-final.log`.
Restent la capture à déposer, la comparaison avec Aziz et la PR de validation relue.

### Préparation locale de la clôture

`lab/m0-setup` existait au commit initial `d5a2aa1`, sans commit propre.
Elle a été avancée en fast-forward jusqu’à `23b452e` : les trois commits M0
et leurs auteurs sont conservés. `main` et `work/syrine/m0` restent inchangées.
Le titre et le corps de la future PR sont dans `reports/m0/pr-title.txt` et
`reports/m0/pr-description.md`. Aziz (@MohamedAzizKouch) sera sollicité pour
une relecture réelle ; aucune approbation ni contribution ne lui est attribuée.

Le commit documentaire de clôture restera local à cette étape. Après ce commit,
le dernier contrôle Git de `make check-m0` échouera tant que HEAD n’est pas publié.
La preuve 19/19 obtenue sur la base publiée est conservée séparément : elle ne
prouve pas la publication de la future branche d’intégration. Après autorisation
ultérieure de push, relancer la checklist sur le HEAD publié et capturer son résultat.

## Lab 1 — incrément IBM HR sur work/syrine/m1

M0 est réellement fusionné dans main (PR #1, `7606b83`). Cela n’atteste pas d’une
approbation GitHub d’Aziz. Nouveaux commits : anglais, `type(scope): description`,
sans réécriture des commits historiques. Intégration future via `lab/m1-versioning`.

```bash
uv run --no-sync python -m src.download
uv run --no-sync python -c 'from src.dataset_config import load_config; print(load_config())'
uv run --no-sync pytest -q tests/test_hr_download.py
```

Le téléchargement public Kaggle version 1 est vérifié par SHA-256 du CSV source.
L’export contient 32 colonnes, dont EmployeeNumber hors prédicteurs et trois
sensibles d’audit. Consulter `docs/dataset-card.md`, ADR-0001 et `reports/m1/`.
Coûts 1:1 et gate 0.70 sont des propositions de référence, pas des résultats RH.

La suite officielle existante conserve un test spécifique à `personal_status` ;
il échoue sur le contrat RH. Il n’a pas été modifié ni ignoré pour afficher du vert.
Les nouveaux tests couvrent l’audit hors features sur les attributs réels du projet.

Suite prévue : initialiser DVC et sa stage download en incluant `dataset.yaml`
(section source comprise) dans les dépendances, puis le remote `s3://dvc-store/scoring`.
Configurer `params.yaml` avec `prepare.id_column: EmployeeNumber` avant d’écrire le
script prepare de l’énoncé : split stratifié 80/20 graine 42, fit sur train seulement.
Conserver les noms `scoring` et `scoring-model`. Ne pas lancer de grid search ou de
promotion tant que cette prochaine étape n’est pas demandée.
