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

Le test initial spécifique à `personal_status` a été rendu générique le 2026-10-20
avec une fixture synthétique, sur autorisation de Syrine. Son objectif reste vérifié,
avec en plus séparation X/y et lecture d’équité ; aucun test supprimé, ignoré ou xfail.
Les 32 tests de la phase 1 passent, puis 45 avec les tests de préparation.

Suite prévue : initialiser DVC et sa stage download en incluant `dataset.yaml`
(section source comprise) dans les dépendances, puis le remote `s3://dvc-store/scoring`.
Configurer `params.yaml` avec `prepare.id_column: EmployeeNumber` avant d’écrire le
script prepare de l’énoncé : split stratifié 80/20 graine 42, fit sur train seulement.
Conserver les noms `scoring` et `scoring-model`. Ne pas lancer de grid search ou de
promotion tant que cette prochaine étape n’est pas demandée.

## Lab 1 — DVC et préparation (2026-10-20)

Les coûts neutres FN/FP 1:1, ROC AUC et gate provisoire 0.70 sont validés par Syrine.
Précision, rappel, F1, matrice de confusion et AP (`average_precision`, résumé de la
courbe précision-rappel ; distinct de l’intégrale trapézoïdale) seront suivis à l’entraînement.
Age/Gender/MaritalStatus restent hors prédicteurs. Groupes d’âge : <30 (326),
30–44 (830), >=45 (314), respectivement 91, 110, 36 Yes ; pas d’ajustement nécessaire
pour ces effectifs globaux, mais intersections et test seront plus petits.

Le pipeline DVC s’arrête à `download -> prepare`. `dvc repro` ne lance donc pas
train/evaluate. L’extension source/sensitive des dépendances download est volontaire :
version, empreinte ou colonnes d’audit modifiées doivent invalider sa sortie.
La préparation reprend l’énoncé, ajoute des gardes d’identifiant/cible et convertit
explicitement les catégories en chaînes pour le schéma String de Feast.

```bash
source .venv/bin/activate
set -a && source .env && set +a
make pf
dvc repro
dvc status
dvc push
dvc status --cloud
make test
make lint
```

Sur un autre clone, recréer localement les credentials avec `dvc remote modify --local`
à partir des variables `.env` ; ne pas les copier dans `.dvc/config`. Un autre cluster
possède son propre remote, à remplir avec `dvc repro` puis `dvc push`, comme dans le cours.
Les CSV et le Parquet sont dans le cache DVC, jamais dans Git. Le timestamp UTC fixe
est technique, pas un historique RH. Les CSV conservent les sensibles pour l’audit ;
le Parquet Feast contient identifiant + 27 prédicteurs + timestamp, sans sensibles/cible.

Suite exacte : implémenter src/train.py (étape 4.3), commencer par un smoke test
régression logistique instrumenté dans `scoring`, puis évaluation ; ne lancer grid search
et promotion qu’après demande. Cet incrément ne valide pas le Lab 1 complet.

## Reprise actuelle — Lab M1 finalisé (2026-10-20)

Les sections M1 précédentes décrivent les incréments historiques. La procédure
actuelle utilise les quatre stages `download -> prepare -> train -> evaluate`,
Feast et le registre. Le code reste local à `work/syrine/m1` : aucun push, PR,
merge ou tag n’a été effectué pendant cette finalisation. Aziz accédera à cet état
après une publication autorisée ou un transfert local convenu ; ne pas supposer que
la branche distante contient déjà ces commits.

### Même poste et même cluster existant

Vérifier d’abord l’état Git, les conteneurs/nœuds, les pods/PVC et les ressources.
Le stockage Ubuntu/Docker est sur D:, mais `df -h /mnt/d` vérifie l’espace Windows
réel en complément du disque virtuel Linux. Arrêter les écritures si les services
ou volumes deviennent instables ; ne jamais supprimer/recréer le cluster pour un
problème de mémoire ou de port-forward.

```bash
git status --short --branch
docker ps
kubectl get nodes
kubectl -n storage get pods,pvc
kubectl -n mlflow get pods,pvc
free -h
df -h . /mnt/d
make pf
uv sync --locked
source .venv/bin/activate
set -a
source .env
set +a
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export MLFLOW_DISABLE_AGENT_HINT=1 FEAST_USAGE=False DVC_NO_ANALYTICS=1
```

`.env` est configuré localement depuis `.env.example` et reste ignoré. Conserver
`MLFLOW_ENABLE_PROXY_MULTIPART_DOWNLOAD=false` pour les artefacts MLflow depuis WSL.
Ne jamais coller de jeton dans les messages ou les fichiers suivis. Configurer DVC
uniquement dans le fichier local, avec les valeurs de son propre cluster :

```bash
umask 077
dvc remote modify --local storage access_key_id "$AWS_ACCESS_KEY_ID"
dvc remote modify --local storage secret_access_key "$AWS_SECRET_ACCESS_KEY"
chmod 600 .env .dvc/config.local
dvc pull
dvc repro
dvc status
dvc metrics show
dvc status --cloud
```

Remote imposé : `storage`, URL `s3://dvc-store/scoring`, endpoint local `:8333`.
Sur le même remote déjà rempli, les quatre stages doivent être ignorés après pull.
`reports/metrics.json` est suivi par Git ; données et modèle sont dans DVC, pas Git.
Le modèle local DVC est LR C=.1 balanced, avec seuil décision .838435, différent du
champion du registre. Les paramètres de `params.yaml` n’ont pas été changés.

### Feast local : reconstruire les bases ignorées

```bash
cd features
feast apply
feast materialize-incremental "$(date -u +%Y-%m-%dT%H:%M:%S)"
cd ..
python -m src.verify_feast
make test
make lint
make check-m1
```

Entité `employee`, clé technique `EmployeeNumber` ; vue `request_features`, service
`scoring_v1`, 13 Float64 et 14 String issus du contrat. Age/Gender/MaritalStatus,
la cible et l’identifiant restent hors prédicteurs. `features/data/registry.db` et
`online_store.db` sont ignorés et recréés localement, jamais copiés dans Git.
L’horodatage fixe `2026-01-01T00:00:00+00:00` et le TTL 3650 jours sont des conventions
pédagogiques sur une photographie fictive. Le test de jointure avant le snapshot
ne démontre pas une absence de fuite temporelle dans un système RH en production.

### Clone propre sur le même poste

Créer un nouveau dossier temporaire, sans supprimer de dossier existant, puis
cloner le dépôt local validé (tant que la branche n’est pas publiée). Réutiliser
le Python existant par son chemin/PATH ; une nouvelle installation des dépendances
n’a pas été testée dans notre essai de clone. Configurer ses credentials DVC dans
son propre `.dvc/config.local` ignoré, puis `dvc pull`, `dvc repro` et l’évaluation.
Recréer Feast avec les commandes ci-dessus. Le test réel, son chemin temporaire,
les commandes et les limites sont dans `reports/m1/final-clean-clone*.json`.
Ne pas copier un registre Feast : les chemins de la source sont reconstruits pour
chaque clone par `features/definitions.py`.

### Aziz sur son propre cluster

Chaque étudiant possède son MLflow, ses buckets et ses identifiants locaux. Le
localhost d’Aziz n’est pas le stockage de Syrine. Après publication autorisée et
récupération du code validé, Aziz inspecte ses modifications et sa branche personnelle
avant de continuer. Cette procédure ne présume aucune contribution ni revue déjà faite.

1. Vérifier le socle M0 d’Aziz et démarrer ses port-forwards existants ; n’utiliser
   l’installation du Lab0 que pour un véritable nouveau poste, pas pour réinitialiser
   un cluster existant. Installer l’environnement avec `uv sync --locked`, configurer
   `.env` puis `.dvc/config.local` comme ci-dessus.
2. Si son remote est vide et ses sorties absentes : `dvc repro`, puis `dvc push`.
   Les données Kaggle publiques version1 sont téléchargées automatiquement, avec
   empreinte épinglée. L’entraînement produit un run propre au MLflow d’Aziz.
3. Comparer `dvc metrics diff --all` et les métriques. Le dossier MLflow contient un
   run ID et des dates : son hash DVC peut changer même si les métriques sont égales.
   Ne pas remplacer aveuglément le lock de référence de Syrine par ce lock local ;
   conserver l’écart pour revue sur sa branche personnelle.
4. Si un cache partagé restaure un modèle d’un autre serveur mais que son MLflow est
   vide, le cache seul ne peuple pas MLflow. Pour créer son run de pipeline :
   `dvc repro --single-item --force --no-run-cache train`, puis `dvc repro evaluate`.
   Ce recalcul est une action explicite sur sa machine, pas exécutée ici.
5. Pour la checklist complète sur son serveur, lancer sa grille pédagogique une fois
   avec `python -m src.grid_search`, vérifier les22 runs, puis choisir ses propres run
   IDs LR C=1 sans poids, LR C=.1 sans poids et Dummy. Utiliser `src.promote` avec ses
   IDs : champion, Dummy (gate rejetée), challenger avec `--challenger-only`.
   Les IDs inscrits dans `src.verify_registry.py` vérifient le serveur de Syrine ;
   ils ne sont pas portables vers un MLflow vierge. Ne pas copier notre base SQLite
   MLflow ni supposer que les numéros de versions seront identiques.
6. Appliquer/matérialiser Feast, vérifier offline et online, tester, lint et
   `make check-m1` sur son poste. Remonter ses vrais résultats et différences.

### Registre conservé et conflit avec l’étape 8.4

L’état convenu reste v1 champion LR C=1 sans poids, v2 Dummy failed, v3 challenger
LR C=.1 sans poids. `src.promote --filter "tags.launched_by = 'dvc'"` déplacerait
les deux alias vers la LR .1 balanced du pipeline : cette commande n’a pas été exécutée.
Options à discuter : conserver cet état (choix appliqué), enregistrer le run DVC sans
modifier les alias via une opération dédiée à autoriser, ou convenir ultérieurement
d’un nouveau paramétrage/recalcul et d’une promotion. Aucun choix silencieux.
Le 18/18 ne signifie donc pas que le champion actuel a été produit par ce pipeline DVC.

### Revue, intégration et J0 — prochaines actions uniquement

Syrine relit les preuves et autorise séparément une publication. Comparer ensuite
le travail d’Aziz et préparer l’intégration `lab/m1-versioning` selon l’état réel de
ses branches, puis une PR vers main avec sa revue GitHub effective. Ne pas attribuer
une approbation à Aziz avant observation. Refaire la validation sur le commit retenu.
Pour J0 (fin S3, énoncé M10), vérifier organisation optionA, dataset validé, socle
M0/M1, dataset card, ADR et journal ; joindre les preuves et captures réelles. Le tag
`j0`, la publication, la PR et la fusion nécessitent une autorisation ultérieure.
Les résultats A restent exploratoires sur test répété ; B1/B2 et les RQ XP-Cube
restent séparés et inchangés.
