## Quoi et pourquoi

Prépare le socle M0 du dépôt commun (option A), avec le smoke test MLflow,
les preuves MLflow/DVC et la documentation de reprise. Le cluster existant a été
restauré sans recréation ; SeaweedFS et MLflow utilisent les versions et PVC du cours.

Branche source prévue : `lab/m0-setup` ; cible : `main`.
Les trois commits M0 de Syrine sont conservés sans réécriture (`e25af6e`,
`ef7a224`, `23b452e`). La préparation documentaire est ajoutée séparément.

## Type

- [x] Lab du socle (`lab/m0-setup`)
- [ ] Extension
- [x] Correctif / documentation

## Correctifs à relire

- Modes exécutables des scripts `infra/kind/create-cluster.sh` et `labs/m0-setup/check.sh`.
- `enableServiceLinks: false` dans SeaweedFS : évite que le Service `s3` injecte
  `S3_PORT=tcp://…`, rejeté par le paramètre numérique `s3.port` de SeaweedFS 4.48.
- Motifs `pkill` de `make pf` limités aux processus commençant par `kubectl`,
  pour ne pas arrêter le shell `.ONESHELL` de la recette elle-même.
- Exclusion explicite de `.dvc/config.local` dans Git.
- Option locale `.env` `MLFLOW_ENABLE_PROXY_MULTIPART_DOWNLOAD=false` documentée :
  maintient la lecture via le proxy MLflow depuis WSL ; `.env` n’est pas versionné.

Aucune version modifiée et aucun volume ou cluster supprimé. Ancien MinIO conservé,
mais le stockage du socle M0 est SeaweedFS. Aucun travail du Lab 1 inclus.

## Comment vérifier

Sur le poste disposant du cluster et de son `.env` local :

```bash
kubectl config current-context
kubectl get nodes
make pf
make check-m0
```

Le smoke test enregistre `hello-mlops` (`accuracy=0.42`, `loss=1.337`) et `hello.txt`.
Les preuves de relecture de l’artefact et de l’objet DVC sont dans `reports/m0/`.

### Preuves réelles et portée

- `reports/m0/check-m0-final.log` : validation publiée 19/19 sur la branche de Syrine.
- `reports/m0/check-m0-integration-base.log` : nouvelle exécution sur `lab/m0-setup`
  au commit `23b452e`, avant le commit documentaire local de clôture.
- `reports/m0/mlflow-readback.txt`, `mlflow-s3-readback.txt`, `dvc-readback.txt` :
  contenus relus via MLflow/S3 ; objet DVC de 12 octets identique au fichier local.
- Vérifications ciblées antérieures : ruff du smoke test, yamllint du manifest,
  bash -n des scripts et git diff --check.

Le dernier contrôle du script vérifie que HEAD figure dans une référence distante
locale. Un nouveau commit local non publié fera échouer ce contrôle Git ; cela
ne remplace ni ne remet en cause les preuves datées sur `23b452e`.
Après autorisation ultérieure de publication, relancer `make check-m0` sur le HEAD
publié, joindre la sortie et la capture finales. Cette préparation locale n’ouvre
pas de PR et n’effectue aucun push ni aucune fusion.

## Checklist

- [ ] `make lint` et `make test` complets exécutés (non relancés pour cette clôture documentaire).
- [x] Preuve M0 19/19 conservée pour le socle publié ; périmètre précisé ci-dessus.
- [ ] Validation et capture du HEAD final après publication de l’intégration.
- [x] Aucun changement de colonnes, cible, seuil ou contrat de données.
- [x] `.env`, `.venv/`, `.dvc/config.local` exclus ; aucun secret personnel détecté
  par la vérification ciblée des chemins et signatures. Les identifiants publics
  de TP fournis dans le template du cours restent inchangés.
- [x] Journal et organisation option A mis à jour.

## Relecture

Relecteur à solliciter : Aziz (@MohamedAzizKouch).
Aucune contribution ni approbation d’Aziz n’est déclarée dans cette préparation.
La relecture devra comporter un commentaire réel sur les correctifs et preuves,
puis une approbation avant la fusion. Aucun résultat de son cluster n’est attesté ici.

## Capture et remise

Après publication autorisée du HEAD retenu, exécuter `make check-m0` dans un terminal
agrandi ; attendre le résultat puis capturer les 19 lignes et le récapitulatif avec
`Win + Maj + S`. Joindre l’image à la PR et la déposer sur l’espace du cours.
Capturer aussi, dans http://localhost:5000, le run `hello-mlops`, ses métriques et
l’artefact `hello.txt`. Si le dernier contrôle Git échoue sur un commit local,
attendre sa publication plutôt que présenter une ancienne sortie comme actuelle.
