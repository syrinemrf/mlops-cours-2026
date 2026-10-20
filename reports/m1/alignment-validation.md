# M1 — alignement DVC / Registry et validation avant publication

Date : 2026-10-20. Branche `work/syrine/m1`. Code de référence entraîné :
`49533e397af86350dbd7ec116c0d8fa4beb7ffa7`. Les commits antérieurs, les 22 runs de
grille et les rapports historiques sont conservés. Aucun push Git, PR, merge ou tag.
Protocole pédagogique A uniquement ; aucune expérience B1/B2 ou XP-Cube exécutée.

## Configuration définitive

LR, `C=1.0`, `class_weight=None` (valeur YAML `none`), `random_state=42`.
Contrat, données, préparation et 27 prédicteurs inchangés ; split 80/20 stratifié,
1176/294 lignes, 190/47 positifs. Gate ROC AUC 0,70, coûts expérimentaux FN/FP 1:1.
Seuil de décision 0,5, distinct de la gate. Les neuf RF de la grille fixent désormais
explicitement balanced ; les 22 configurations gardent leurs conditions effectives
historiques. La grille n’a pas été rejouée.

Nouveau run DVC de référence : **ef2d3f85ebe3432f9172275c34bbd6ac**, FINISHED,
scoring, protocol=A, protocol_id=mlops_A_v1, launched_by=dvc,
evaluation_role=pedagogical_pipeline, publication_candidate=true.
ROC AUC exacte : **0.8368507192695321**. Les valeurs reproduisent le candidat
pédagogique C=1 sans poids de la grille ; aucune amélioration statistique revendiquée.

## §8.5 — changement temporaire et retour au cache

Clone isolé `/tmp/mlops-m1-alignment-9b53bahu/repo`, branche work/syrine/m1.
Python verrouillé existant et même cluster réutilisés, credentials copiés uniquement
dans les fichiers locaux ignorés en mode 600, dossier temporaire privé conservé.
Le modèle de référence du dépôt principal et son lock n’ont pas été altérés par ces essais.

Un checkpoint **uniquement dans le clone**, commit
`78fe7419ae64e8f80876a8ff3dfbb413d859ad1d`, enregistre le lock et les métriques du
premier modèle aligné. Message anglais :
`test(m1): checkpoint isolated reproducibility baseline`.
Son parent est le code 49533e3 ; il ne modifie ni code ni paramètres et ne sera pas
intégré au dépôt principal. Les diffs officiels comparent ainsi au bon modèle de départ.

L’exercice inverse le sens de l’exemple du cours : `none -> balanced -> none`,
puisque la configuration finale convenue est sans poids. **Seul class_weight
change**, à C=1 et seed 42 fixes. Pas de choix de paramètres à partir des scores.

| Étape | Run ID | ROC AUC | Seuil | Coût |
|---|---|---:|---:|---:|
| Base isolée sans poids | 6fa3c25ec6a343d385944deacf20e7bb | 0,8368507193 | 0,5 | 35 |
| Variante balanced | 3dfc2408a966424fa9493d41f6992068 | 0,8280644328 | 0,8384353741 | 37 |
| Restauration sans poids | 6fa3c25ec6a343d385944deacf20e7bb | 0,8368507193 | 0,5 | 35 |

`dvc status` détecte train.class_weight ; repro ignore download/prepare et exécute
train/evaluate. Les sorties de `dvc params diff` et `dvc metrics diff --all` sont
conservées. À la restauration, **train et evaluate sont repris du run-cache** ;
aucun fit ni run ajouté (27 runs avant/après). Paramètres, lock et métriques
retrouvés **octet pour octet**, probabilités identiques, hashes données inchangés.
[Résumé mesuré](alignment-section-8-5.json), [repro retour cache](alignment-section-8-5-restored-repro.log),
[diff des paramètres](alignment-section-8-5-params-diff.log),
[diff des métriques](alignment-section-8-5-metrics-diff.log).

## §10.3 — recalcul intégral forcé

`dvc repro --force` exécute effectivement **download, prepare, train, evaluate**.
Le téléchargement officiel retrouve source1470×35 et export1470×32, sans modifier
les empreintes épinglées. Nouveau run isolé :
**e6f07ea0ee5d47e48a283f6845f2346d**, non enregistré dans le registre.

Par rapport à la base isolée : toutes les métriques prédictives ont un delta 0,
le JSON est identique octet pour octet et les 294 probabilités sont exactement
identiques (écart maximal 0). Les quatre empreintes SHA-256 des données sont
inchangées. Seul dvc.lock diffère dans Git : hash du dossier modèle et dépendance
de ce dossier dans evaluate,4 lignes. Les métadonnées de nouveau run/UUID/date et
la sérialisation du modèle changent ; fit_seconds varie légitimement et ne fait
pas partie du JSON de métriques prédictives.
[Preuve](alignment-section-10-3.json), [exécution intégrale](alignment-section-10-3-force.log),
[diff métriques](alignment-section-10-3-metrics-diff.log).

Portée : même cluster et venv existant. Ce n’est ni une installation vierge des
dépendances ni le replay indépendant d’Aziz sur son poste (§10.4).

## Filiation du modèle de référence et stockage

Dans le dépôt principal, repro ignore download/prepare et recalcule train/evaluate.
Les données et les entrées download/prepare du lock restent identiques. La
normalisation du lock préserve les valeurs YAML 1.2, notamment la chaîne Yes.

- Run : `ef2d3f85ebe3432f9172275c34bbd6ac` ; commit de code 49533e3.
- MD5 du CSV exporté dans le lock et le tag MLflow : `16e6acc1f69d648c4ec1d3b44efc0179`.
- SHA-256 du CSV exporté : `27e7bebda91c7e6d0b77e80128c2d9383d70a19a185b51ecfe3bb90f761d2a78`.
- Hash du dossier modèle DVC : `46cf394ffbe298bf1e653379449c8f8f.dir`.
- Source Kaggle 1 et SHA source dans dataset.yaml inchangés ; l’empreinte source
  observée au premier téléchargement n’est pas une authentification indépendante.
- `dvc push` : **3 objets nouveaux** ; les fichiers déjà présents sont réutilisés.
  Dix objets requis ont été relus par HEAD S3 : ETags single-part conformes aux MD5.
- Nouvelle repro : quatre stages ignorés. Status local à jour et cloud synchronisé.

La référence et le recalcul forcé ont également des probabilités identiques.
[Filiation](alignment-lineage.json), [push](alignment-reference-push.log),
[objets S3](alignment-s3-objects.json), [commandes et codes retour](alignment-repro-commands.json).
Le DAG ASCII conserve son contenu ; seuls ses espaces de fin de ligne sont retirés
pour Git. La sortie originale reste conservée ; [empreintes et détail](alignment-log-normalization.json).

Au total : **29 runs FINISHED** =25 antérieurs + base isolée + variante + forcé +
référence principale. Les rôles de reproduction sont taggés ; seuls les artefacts
du run principal sont promus. Les 22IDs/paramètres/métriques historiques sont revérifiés.

## Registre et chargement distant

| Version réelle | État final | Run ID | ROC AUC |
|---|---|---|---:|
| 1 | conservée, ancien champion | 5ef49fc5f3e740f28c523b0dcc1ae8c1 | 0,8368507193 |
| 2 | conservée, Dummy failed | 0c42486a18f340ddb2db995d8797c70d | 0,5 |
| 3 | @challenger, LR C=0,1 sans poids | 139ae364aa6e4166b2bd19ef533f48e7 | 0,8360754587 |
| 4 | @champion, nouveau run DVC C=1 sans poids | ef2d3f85ebe3432f9172275c34bbd6ac | 0,8368507193 |

Le numéro4 est lu dans le résultat réel du registre. Gate inchangée, répétition
idempotente sans cinquième version, nouvelle tentative réelle sur Dummy rejetée
sans toucher le champion, puis réaffectation explicite de challenger à v3.
Versions1/2/3 et sources préservées ; diagnostic portable sans ancien ID champion codé en dur.

Le champion distant correspond au run des métadonnées du modèle DVC, avec mêmes
paramètres, seed,27 features et signature (13 double,14 string). Les294 probabilités
distant/local sont exactement égales ; toutes les métriques recalculées correspondent
au run à 1e-12 près et au JSON arrondi. Le seuil 0,5 correspond aux prédictions sklearn
et pyfunc. Sur les cinq premières observations : décisions `[0,0,0,0,0]`, probabilités
`[0.05473947,0.00456793,0.07695643,0.00346112,0.45296888]`.
[Opérations](alignment-registry-operations.json), [état final](alignment-registry-state.json),
[vérification distante](alignment-registry-verification.json).

**Intégrité des archives :** les SHA-256 des fichiers skops local/distant sont
différents, sans prétendre qu’il s’agit des mêmes octets. Les contenus des tableaux
sont identiques ; les schémas sont identiques après normalisation des IDs d’objets
et noms de fichiers référencés. Les horodatages ZIP diffèrent aussi. Le code skops
installé utilise `id(obj)` pour sa mémorisation (`skops/io/_utils.py:137,238–242`).
Cet écart de sérialisation est distingué des paramètres/prédictions, tous identiques.
[Constat brut](alignment-model-serialization.json),
[comparaison normalisée](alignment-model-serialization-normalized.json).

## reports/metrics.json

Valeurs réellement produites, arrondies à 4 décimales comme le cours :

```json
{
  "tn": 239.0,
  "fp": 8.0,
  "fn": 27.0,
  "tp": 20.0,
  "pr_auc_trapezoidal": 0.6444,
  "brier_score": 0.091,
  "log_loss": 0.3278,
  "roc_auc": 0.8369,
  "average_precision": 0.647,
  "f1": 0.5333,
  "precision": 0.7143,
  "recall": 0.4255,
  "accuracy": 0.881,
  "business_cost": 35.0,
  "decision_threshold": 0.5,
  "confusion": {"tn": 239, "fp": 8, "fn": 27, "tp": 20},
  "n_test": 294
}
```

## Contrôles finaux et limites

- **85 tests réussis**, un warning Feast/NumPy de dépréciation ; aucun skip ajouté.
- **make lint réussi** : Ruff check/format et yamllint ;62 fichiers déjà formatés.
- **make check-m1 : 18/18, code retour 0** sur l’état technique aligné.
- Feast existant vérifié offline 1176×30,27 features conformes ; online 1 salarié,
  27 features conformes. Les trois requêtes avant snapshot n’ont aucune feature.
- L’option `--output` de verify_feast conserve les anciens rapports ; les bases
  locales ne sont pas versionnées. Aucun besoin de recréer ou réinitialiser le store.

[Tests](alignment-tests.log), [lint](alignment-lint.log),
[contrôle officiel](alignment-check-m1.log), [Feast](alignment-feast-verification.json).
Le checker officiel et ses critères sont inchangés.

Infrastructure : les trois nœuds restent Ready, les PVC Bound ; compteurs de
redémarrage historiques 2 pour SeaweedFS et MLflow. RAM limitée (environ 1,1–1,4 Gio
disponibles), swap très utilisé : exécutions séquentielles, aucune suppression ni
recréation de cluster/volume. La lenteur antérieure de docker info n’est pas
déclarée résolue. MLflow avertit que pip ne peut être versionné dans l’export
conda ; aucun paquet installé pour contourner ce warning, uv.lock inchangé.

Limites scientifiques : candidats choisis sur test pédagogique consulté à répétition,
pas d’estimation finale indépendante, coût 1:1 hypothétique, gate 0,70 provisoire,
données synthétiques sans historique RH réel. Pas de calibration, expérience Jia,
explication SHAP scientifique ou mesure SSAS nouvelle. B1/B2/XP-Cube et dépendances
verrouillées sont conservés. Snapshot Feast artificiel, sans preuve temporelle de production.

## Avec Aziz et avant publication

§10.4 reste à exécuter **réellement sur son propre cluster** : environnement
verrouillé, téléchargement/repro sur remote local vide, comparaison des métriques
et hashes, ses propres runs/versions/alias, Feast et check 18/18. Ne pas substituer
son lock local de modèle au lock commun uniquement pour ses run IDs/dates.
Aucune contribution ou approbation d’Aziz n’est supposée.

Accord dataset par courriel confirmé par Syrine ; référence/date du message encore
à consigner, sans inventer d’issue. Capture réelle du futur commit publié à prendre.
Publication personnelle, comparaison avec Aziz, intégration lab/m1-versioning,
PR/revue effective/fusion puis J0 restent soumis à autorisation. Cet état est une
validation technique locale, pas une remise déjà fusionnée dans main.
