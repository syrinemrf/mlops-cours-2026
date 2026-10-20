# M1 — revue du binôme, intégration et préparation de J0

Préparé le 2026-10-20 depuis `work/syrine/m1@d2ea3ca`. **Procédure future,
non exécutée.** Aucun push, PR, merge, tag ou changement de registre pendant
l’audit. Commencer par résoudre les décisions de [l’audit](pre-publication-audit.md).
Les commandes ci-dessous supposent chaque autorisation obtenue au moment indiqué.

Actualisation après autorisation : alignement 8.4 et exercices 8.5/10.3 exécutés,
85 tests et 18/18 vérifiés ; voir [les résultats](alignment-validation.md).
Les commandes de publication, comparaison, PR, fusion et tag restent futures.

## 1. Contributions observables de Syrine

Les quinze commits M1 initiaux audités à d2ea3ca depuis `main@7606b83` portent l’auteur `syrinemrf`.
Cela décrit Git, sans attribuer de travail ni d’approbation à Aziz.

| Domaine | Commits et livrables représentatifs | Ce qu’Aziz peut comparer |
|---|---|---|
| Source/contrat IBM HR | b380e15, c6541a2, 4cd1b01 ; download, contrat, tests, card/ADR | Source Kaggle 1, hash, schémas35/32, ID et sensibles hors27 features |
| DVC/préparation | 9a83ee4, 01c2d44 ; prepare, lock, preuves S3 | Split stratifié1176/294 seed 42, identifiants disjoints, types et hashes |
| Cadrage scientifique | f81e2b5 ; baseline-protocol.md | A/B1/B2, quatre constats documentés, RQ1–RQ3 non démontrées |
| Entraînement et grille A | 48c354e, cdead3f, 9c02057, fcc9cdb | 2 smoke +22 runs, paramètres, métriques/seuils, limites du test répété |
| Registre A | 418d026, c51c992 | Gate 0,70, Dummy rejeté, idempotence, alias et modèle distant |
| Pipeline/Feast/preuves | 82f2cc7, ccf031f, d2ea3ca | 4 stages, évaluation locale, offline/online, 18/18, 77 tests, clone propre |

Les correctifs documentaires de l’audit sont commités dans db871c8 ; alignement,
isolation des paramètres et tests dans 49533e3. Les preuves supplémentaires sont
consignées dans alignment-validation.md. L’assistance Codex est
déclarée dans le journal ; aucune contribution du binôme n’est fabriquée.

## 2. Checklist de comparaison à remplir réellement par Aziz

- [ ] Confirmer son nom de branche, SHA, arbre local et base commune ; décrire
  seulement ses propres changements et résultats réellement exécutés.
- [ ] Lire le contrat : Attrition/Yes,27 features, ID EmployeeNumber, constantes
  retirées, Age/Gender/MaritalStatus conservés pour audit hors prédiction.
- [ ] Vérifier source/version/licences et ancre SHA-256 ; distinguer35 colonnes
  source,32export et29dans le Parquet Feast. Retrouver l’accord par courriel.
- [ ] Comparer split 80/20 stratifié seed 42,1176/294 lignes, 190/47 Yes, zéro
  identifiant partagé et prétraitement appris exclusivement sur train.
- [ ] Relire le seuil balanced 0,838435, son application LR/RF, seuil 0,5 sans
  poids/GB/Dummy ; distinguer calibration, seuil de décision et gate 0,70.
- [ ] Vérifier les 22 configurations par famille et les manifests historiques,
  sans relancer la grille à cause d’une identité de code/lock différente. Après
  alignement DVC sans poids, vérifier que les neuf RF gardent explicitement balanced,
  au lieu d’hériter silencieusement des nouveaux defaults de params.yaml.
- [ ] Confirmer le modèle DVC final convenu, les paramètres effectifs, le MD5
  source/export, le run DVC, les métriques et le champion issu de ce run.
- [ ] Contrôler la gate, Dummy failed, au moins3 versions, absence de duplicats,
  alias champion/challenger avec IDs réels de son serveur et cinq prédictions.
- [ ] Vérifier quatre stages et cache/remote DVC, preuve du changement/retour cache
  §8.5 et replay intégral §10.3, sans remplacer le lock commun par son lock local.
- [ ] Rejouer sur son cluster existant selon NOTES ; consigner les vrais écarts,
  hashes, métriques et run IDs. Ne pas importer les bases MLflow/Feast de Syrine.
- [ ] Vérifier Feast offline/online et les limites du snapshot technique synthétique.
- [ ] Exécuter ses tests, lint et contrôle officiel ; citer le commit et l’heure.
- [ ] Vérifier exclusions Git et fichiers secrets locaux, aucune donnée brute/
  modèle/venv dans la PR. Vérifier NOTES/journal/ADR et distinction A/B1/B2.
- [ ] Soumettre une revue GitHub sur le **dernier SHA de la PR** : commentaires
  techniques, demandes de correction si nécessaire, puis approbation réelle.

Une case vide signifie « non vérifié ». Ni le nom d’Aziz dans le README, ni deux
alias d’auteur de Syrine dans Git, ni une revue automatique ne cochent cette liste.

## 3. Fichiers exposés aux conflits et stratégie d’intégration

| Fichiers | Arbitrage attendu |
|---|---|
| dataset.yaml, src/dataset_config.py, src/download.py | Accord commun sur contrat/version/mapping ; jamais fusionner deux listes de features sans contrôle |
| src/prepare.py, src/train.py, src/evaluate.py, params.yaml | Maintenir split/seed/coûts, prétraitement train et modèle A convenus ; relire les interactions |
| dvc.yaml, dvc.lock, reports/metrics.json | Fusionner le pipeline et les paramètres d’abord ; conserver un lock de référence cohérent, régénérer seulement si les entrées effectives changent |
| src/grid_search.py, manifests et exports reports/m1 | Conserver les preuves de chaque snapshot/serveur ; pas de réattribution d’anciens runs à un nouveau code |
| src/promote.py, src/verify_registry.py | IDs locaux et alias propres à chaque MLflow ; diagnostics paramétrables à prévoir |
| features/definitions.py, feature_store.yaml | Schéma/clé/timestamp communs ; bases ignorées reconstruites séparément |
| pyproject.toml, uv.lock | Aucun changement prévu ; si conflit, revoir la nécessité avant de régénérer le verrou |
| README, NOTES, journal, card, ADR, baseline-protocol | Conserver chronologie et auteurs, fusionner les décisions explicites ; science séparée |
| .env, .dvc/config.local, features/data, modèles | Ne sont pas des objets d’intégration Git ; configuration propre à chaque poste |

Préférer une branche d’intégration dans un **nouveau worktree** pour préserver la
branche personnelle et les fichiers ignorés de Syrine. Vérifier au préalable si
`lab/m1-versioning` existe localement ou à distance ; comparer avant réutilisation.
Intégrer les branches convenues par merges préservant les commits/auteurs, sans
rebase, squash, force-push ni stratégie automatique « ours/theirs » pour les locks.
Le travail réel d’Aziz doit être inspecté avant de décider s’il faut le fusionner.

Le cluster de référence pour les artefacts communs peut rester celui de Syrine,
avec accord du binôme. Un simple merge sans changement d’entrées ne justifie pas
un nouvel entraînement. Si le code/contrat/paramètres effectifs changent, reproduire
les stages invalidés et revoir la filiation du champion avant d’approuver.
Le lock régénéré sur le cluster d’Aziz garde ses métadonnées locales et n’est pas
substitué mécaniquement au lock de référence.

## 4. Publication personnelle, après autorisation explicite

Avant le push : corrections approuvées commitées en anglais, arbre propre,
preuves techniques renouvelées si paramètres/code ont changé, DVC poussé sur son
remote, capture préparée. L’audit documentaire seul n’exécute pas ces opérations.

```bash
cd ~/mlops-cours-2026
git status --short --branch
git branch --show-current
git log --oneline origin/main..work/syrine/m1
git diff --check
git ls-files .env .dvc/config.local .venv features/data mlruns mlflow.db
git ls-files data models
git push -u origin work/syrine/m1
git fetch origin
git rev-parse work/syrine/m1 origin/work/syrine/m1
```

Les chemins interdits doivent être absents ; data/models ne doivent contenir que
les .gitignore. Les deux SHA doivent être égaux. Aucun `--force` ni push de toutes
les branches. Vérifier aussi l’affichage de la branche et ses fichiers sur GitHub.
Si SSH demande la passphrase, la saisir uniquement dans le terminal sécurisé.

## 5. Comparer puis construire la branche officielle

Après publication des vrais travaux et accord sur l’intégration, définir
`M1_AZIZ_BRANCH` au nom réellement confirmé, sans supposer `work/aziz/m1`.

```bash
git fetch origin
: "${M1_AZIZ_BRANCH:?Renseigner le nom confirme de la branche Aziz}"
git branch --all
git worktree list
git log --graph --oneline --left-right work/syrine/m1..."origin/$M1_AZIZ_BRANCH"
git diff --stat work/syrine/m1 "origin/$M1_AZIZ_BRANCH"
git diff origin/main...work/syrine/m1 -- dataset.yaml params.yaml dvc.yaml
git diff "origin/main...origin/$M1_AZIZ_BRANCH" -- dataset.yaml params.yaml dvc.yaml
git branch --list lab/m1-versioning
git ls-remote --heads origin refs/heads/lab/m1-versioning
```

Si Aziz n’a pas de branche publiée, arrêter la comparaison distante à ce constat
et convenir du transfert ou de sa revue ; ne pas inventer de branche. S’il n’y a
aucune branche d’intégration préexistante, créer après accord un dossier neuf :

```bash
M1_INTEGRATION_DIR=$(mktemp -d /tmp/mlops-m1-integration-XXXXXX)
git worktree add -b lab/m1-versioning "$M1_INTEGRATION_DIR" origin/main
cd "$M1_INTEGRATION_DIR"
git merge --no-ff work/syrine/m1 -m "merge(m1): integrate Syrine's validated work"
```

Si lab/m1-versioning existe déjà, remplacer cette création par son inspection
(`git log`, `git diff`, état du worktree) puis une réutilisation convenue ; aucune
réinitialisation automatique. Pour les changements d’Aziz retenus après revue :

```bash
git merge --no-ff "origin/$M1_AZIZ_BRANCH" -m "merge(m1): integrate Aziz's reviewed work"
```

En cas de conflit, résoudre ensemble à partir de la table précédente. Ne pas
committer un lock partiellement fusionné. Configurer localement le worktree selon
NOTES (credentials ignorés), récupérer le cache, vérifier les stages invalidés,
puis vérifier tests/lint/contrat/DVC/Feast/registre et le contrôle officiel. Les
preuves portent sur le commit d’intégration, avec les écarts réellement constatés.

Après autorisation de publier **cette** branche d’intégration :

```bash
git status --short --branch
git diff --check
git push -u origin lab/m1-versioning
```

## 6. PR et revue effective d’Aziz

La CLI `gh` n’est pas installée sur ce poste au moment de l’audit ; aucune
installation ajoutée. Utiliser GitHub dans le navigateur :

1. Ouvrir [la comparaison](https://github.com/syrinemrf/mlops-cours-2026/compare/main...lab/m1-versioning)
   **après publication** ; base `main`, compare `lab/m1-versioning`.
2. Titre proposé : `lab/m1-versioning : pipeline DVC, registre et Feast pour IBM HR`.
   Adapter [le brouillon de description](pr-description.md) au résultat final réel,
   compléter les cases restantes et conserver les limites. Ne pas annoncer la
   résolution8.4 tant qu’elle n’a pas été exécutée et vérifiée.
3. Demander une revue à `MohamedAzizKouch` dans Reviewers. Le contrôle des droits
   via le connecteur a renvoyé403 `Resource not accessible by integration` :
   cela concerne l’accès de l’intégration et **ne prouve pas** un défaut de droits
   d’Aziz. Vérifier la demande réelle dans l’interface ; si elle échoue, conserver
   le message exact, sans modifier les droits automatiquement.
4. Aziz lit le diff, exécute sa checklist, soumet ses observations puis sa revue.
   Vérifier que son état est `APPROVED` sur le dernier commit à fusionner, sans
   demande de changements non résolue. Un commentaire Copilot ou de Syrine ne
   constitue pas sa revue. Toute modification après revue appelle une relecture.
5. Sur le SHA relu, afficher tests/lint/check-m1 et preuves DVC/registre/Feast.
   Les workflows `course-ci` sont conditionnés au propriétaire du cours ; des
   jobs ignorés dans notre dépôt ne remplacent pas les vérifications locales.

## 7. Fusion, rendu publié et capture — après accords requis

Après la vraie revue d’Aziz et autorisation de fusion, utiliser **Create a merge
commit** sur GitHub, en vérifiant le SHA relu ; préserver les commits et auteurs.
Ne pas choisir squash/rebase et ne pas effacer les branches comme effet annexe.
Dans un worktree où main est disponible, sans modifications locales :

```bash
git fetch origin
git switch main
git merge --ff-only origin/main
git rev-parse HEAD origin/main
git merge-base --is-ancestor work/syrine/m1 main
git merge-base --is-ancestor lab/m1-versioning main
```

Le résultat doit contenir les commits retenus. Reprendre l’environnement/ports du
cluster existant selon NOTES, `dvc pull`, vérifier la filiation du modèle, puis :

```bash
make test
make lint
dvc status
dvc status --cloud
git rev-parse HEAD
make check-m0
make check-m1
git status --short --branch
```

Ne pas présenter une ancienne sortie comme celle du commit fusionné. M0 peut
échouer sur son dernier contrôle Git tant que le HEAD n’est pas publié et récupéré
dans les références distantes ; ce n’est pas un motif de modifier son checker.

**Capture M1 :** terminal agrandi, affichage du SHA puis `make check-m1`, attendre
la fin et le code 0, capturer les18 lignes vertes et le récapitulatif avec
`Win + Maj + S`. Réduire la police si nécessaire, sans couper une ligne d’échec.
Conserver par exemple `check-m1-<SHA>.png` et la sortie texte datée. Ne pas fabriquer
une capture à partir d’un ancien log. Compléter avec l’interface MLflow montrant
runs/versions/alias et preuves DVC/Feast, sans configuration locale ni secret.

Si l’image est ajoutée à Git après fusion, elle crée un nouveau commit : prévoir
une PR documentaire relue et recontrôler le nouveau main avant J0. Une capture
jointe à la PR conserve le SHA montré sans changer le commit testé.

**Remise M1 du professeur :** dépôt GitHub public (ou partagé avec l’enseignant),
code src/features, contrat, paramètres, dvc.yaml/lock/config, reports/metrics.json,
pyproject/uv.lock et NOTES **fusionnés dans main par la PR du lab**, avec capture
entièrement verte. Échéance : **avant le début de M2** ; aucune date calendaire
ni plateforme de dépôt supplémentaire n’est spécifiée dans l’énoncé. Vérifier les
consignes de remise du groupe. Le `dvc push` vers localhost remplit le stockage de
ce cluster ; il ne publie pas les données sur GitHub ni sur celui du professeur.

## 8. Préparer puis publier j0, après autorisation distincte

Conditions : main publié/relu, corrections M1 décidées, contrôles M0/M1 verts au
commit retenu, dataset et accord traçables, organisation A/membres/README exacts,
reproduction et preuves des deux membres, journal/card/ADR à jour. J0 est Setup
fin S3 ; ne pas développer M2 pour passer ce jalon.

Le mode actuel de `labs/m10-capstone/check.sh` est644. Sans modifier le checker,
utiliser l’appel équivalent explicite :

```bash
bash labs/m10-capstone/check.sh --jalon j0
```

Avant le tag, le contrôle « Tag j0 » est attendu manquant. Tous les autres échecs
doivent être examinés ; ne pas réduire AUTEURS_MIN ni contourner les contrôles.
Pour employer exactement `make check-m10 JALON=j0`, demander séparément la
correction du seul mode exécutable ; aucun contenu de vérification à modifier.
La création locale du tag n’est autorisée qu’après validation de tous les autres
prérequis et accord explicite de Syrine.

```bash
git status --short --branch
git fetch origin
git rev-parse HEAD origin/main
git tag --list j0
git ls-remote --tags origin refs/tags/j0 'refs/tags/j0^{}'
```

Comparer les SHA et vérifier l’absence de j0 local **et** distant. Si déjà présent,
lire son commit et demander la conduite à tenir ; ne jamais déplacer/recréer un tag
de jalon publié. Après ces contrôles et autorisation, choisir le SHA exact validé :

```bash
M1_J0_COMMIT=$(git rev-parse origin/main)
git tag -a j0 "$M1_J0_COMMIT" -m "milestone(j0): record reviewed M0 and M1 foundations"
bash labs/m10-capstone/check.sh --jalon j0
git rev-parse 'j0^{commit}' origin/main
```

Si un contrôle échoue après création locale, ne pas publier le tag : diagnostiquer
et solliciter une décision, sans le déplacer automatiquement. Si tout est vérifié
et la publication du tag autorisée :

```bash
git push origin refs/tags/j0
git ls-remote --tags origin refs/tags/j0 'refs/tags/j0^{}'
```

Vérifier dans GitHub **Code > Tags** que `j0` désigne le SHA validé de main et que
les livrables sont consultables à ce tag. Le guide J0 indique que l’enseignant lit
ce tag : pas de rapport final, poster ou vidéo à inventer à J0. La capture exigée
pour le rendu M1 reste à joindre selon les consignes de remise du groupe.
