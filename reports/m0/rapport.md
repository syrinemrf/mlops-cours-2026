# Lab 0 — compte rendu de Syrine

## Validation finale — 2026-10-19

`make check-m0` exécuté après publication : **19/19 vérifications OK — Lab 0 validé.**
La [sortie complète](check-m0-final.log) conserve les 19 contrôles réussis.
Le [contrôle initial avant push](check-m0-before-push.log) reste disponible pour la trace.
La capture à déposer et la PR de validation relue restent à faire.

## État initial et diagnostic

Branche `work/syrine/m0`, arbre propre ; origin SSH et upstream corrects.
Docker 28.4.0 et Compose 2.39.4 installés ; cluster kind présent mais trois
conteneurs arrêtés ; kubeconfig `kind-mlops-lab` correct, API refusant les connexions.
Le control-plane était sorti avec 137, mais OOMKilled=false : la cause exacte de
l’arrêt n’est pas prouvée. Le redémarrage Docker signalé par Syrine est compatible
avec cet état. Un ancien MinIO était présent ; ni SeaweedFS ni MLflow déployés.
`.env`, `.venv` et Python 3.12.14 existaient ; uv 0.12.21, MLflow 3.16.1 et
DVC 3.67.1 déjà installés. `uv sync --locked --offline` a vérifié l’environnement
sans téléchargement. kind 0.33.0, kubectl 1.37.0, Helm 3.22.0, k9s 0.51.0.
Docker : 4 CPU, 3.827 Gio RAM ; disque du dépôt : environ 945 Go disponibles.

## Corrections réellement appliquées

- Redémarrage des trois conteneurs existants, sans recréation ni modification du kubeconfig.
- Droit d’exécution rétabli sur `infra/kind/create-cluster.sh` et le contrôle M0.
- `make cluster` : registry `registry:3`, réseau kind et ConfigMap officiels.
- `make storage` : SeaweedFS 4.48 et PVC 10 Gi ; collision de la variable
  Kubernetes S3_PORT avec le paramètre numérique SeaweedFS corrigée par
  `enableServiceLinks: false` dans son pod.
- `make mlflow` : MLflow 3.16.1, SQLite sur PVC 2 Gi et artefacts dans SeaweedFS.
- `make pf` : motifs pkill limités aux commandes commençant par kubectl pour
  éviter de terminer la recette `.ONESHELL` elle-même.
- `.dvc/config.local` ajouté à `.gitignore` ; aucun secret suivi par Git.
- Téléchargement présigné désactivé dans `.env` local pour lire les artefacts
  par le proxy MLflow, sans tenter d’atteindre le DNS S3 interne depuis WSL.

Aucun changement de version ; aucune suppression de cluster, de volume ou
d’historique ; aucun changement permanent WSL/Docker ; ancien MinIO conservé.

## Services et preuves

Trois nœuds Ready en v1.37.0 ; registry sur localhost:5001 ; SeaweedFS et
MLflow Running/Ready. Buckets : `mlflow-artifacts`, `dvc-store`, `mlops-test`.
Le Job AWS officiel a créé les deux buckets communs ; le bucket de test a été
créé par le même client AWS en conteneur, avec un Job temporaire dérivé du
manifest officiel, réutilisant son image et ses secrets dans le cluster.
Aucun client AWS supplémentaire n’a été téléchargé sur le poste.

MLflow `/health` répond OK. Run `hello-mlops` FINISHED, framework scikit-learn,
accuracy 0.42 et loss 1.337 ; run ID `45e061c13292415c9dd1ef883d7b146b`.
Artefact `hello.txt` présent ; contenu `hello mlops\n` relu directement dans S3
et téléchargé avec succès via le proxy MLflow (contenu identique).

Smoke DVC isolé dans `/tmp/dvc-smoke` : `1 file pushed`. Objet
`mlops-test/dvcstore/files/md5/90/db47eedd801dabbdf799868fb4ae77` relu :
12 octets identiques au fichier local. Ses deux commits sont dans le dépôt
jetable uniquement. Le projet principal n’a pas été initialisé avec DVC (Lab 1).

Vérifications ciblées réussies : ruff check et format du smoke test, yamllint
du manifest modifié, bash -n des scripts, git diff --check et exclusions Git.
Les suites générales des futurs labs ne sont pas présentées comme exécutées.

## Livrables et suite

Fichiers : smoke test officiel `labs/m0-setup/smoke_mlflow.py`, `NOTES.md`,
`docs/journal.md`, présent rapport et log ; correctifs dans `.gitignore`,
`Makefile`, manifest SeaweedFS et modes des deux scripts. `.env` reste local.

Tous les commits du projet sont sur `work/syrine/m0` ; `main`, `lab/m0-setup`
et les branches d’Aziz n’ont pas été modifiées. La branche personnelle a été
publiée avec autorisation ; aucune fusion effectuée.
Le premier commit est `e25af6e` (correctifs M0) ; les livrables sont dans
le commit suivant, consultable avec `git log -2 --oneline`.

Le push initial a été débloqué par Syrine dans son terminal WSL : démarrage
d’un agent SSH et chargement de sa clé. La validation après push a réussi.
Afficher `make check-m0` dans un terminal agrandi, puis faire une capture
`Win + Maj + S` montrant les 19 contrôles et le récapitulatif.
Ouvrir également MLflow et capturer le run et son artefact. Comparer avec
Aziz puis préparer ensemble la PR `lab/m0-setup` vers main, à faire relire
et approuver avant toute fusion. Voir `NOTES.md` pour les commandes.
Ne pas commencer le Lab 1 avant la validation et la remise du Lab 0.

Pour l’oral : Docker héberge les nœuds kind ; Kubernetes gère les services ;
SeaweedFS fournit S3 ; MLflow trace les expériences et leurs artefacts ; uv
reproduit l’environnement Python ; DVC versionne les données avec Git et S3.
Pour IBM HR Attrition, ce socle reliera plus tard chaque dataset à ses
expériences de prédiction des départs, sans adapter le dataset durant M0.
