# Rapport — Lab 4 : packaging du modèle

Binôme : Syrine Maaref (@syrinemrf) et Aziz (@MohamedAzizKouch) · Dataset : `ibm-hr-attrition`
· Modèle : `scoring-model` **v7** · Mesures du 2026-11-08

**Modèle packagé.** `@champion` résolu en version explicite au moment de l'export :
**v7**, run MLflow `ef5f2ec9031741e682eb435c35e419e5` (tag `launched_by=airflow`), régression
logistique C=1 sans poids, seuil de décision 0,5 (param `decision_threshold` du run). Métriques
du run sur le test : ROC AUC 0,8368507193, AP 0,647036, coût expérimental 1:1 = 35. **Origine du
run Airflow non établie** : aucun identifiant de run Airflow dans les tags, et MLflow ne garde
pas l'historique des alias (journal, S13). Même configuration et même ROC AUC que la v4 (modèle
DVC) ; identité binaire non vérifiée. Aucune écriture dans le registre pendant ce lab.

**Parité ONNX.** Sur les 294 lignes de test : écart max |p_sklearn − p_onnx| = 9,97e-08 et
décisions identiques à 100 % au seuil 0,5 (`packaging/app/verify_onnx.py`). La variante BentoML
(pipeline scikit-learn) rend les mêmes probabilités à environ 1e-8 près sur 3 lignes testées.

## 1. Comparatif des tailles

Taille décompressée = somme des couches (`docker history`) ; taille compressée =
`docker image inspect .Size` (magasin d'images containerd de Docker Desktop, valeur que lit
`check-m4`). `docker images` affiche une troisième valeur, l'occupation disque (535 Mo pour
optimized), qui additionne contenu compressé et décompressé.

| Image | Décompressée | Compressée | Utilisateur | CVE HIGH + CRITICAL (Trivy 0.75.0) |
|---|---|---|---|---|
| `scoring-api:naive` | 1 608,8 Mo | 591 Mo | root | 288 (273 HIGH + **15 CRITICAL**) |
| `scoring-api:optimized` | 410,6 Mo | 125 Mo | 10001 (non-root) | 47 (47 HIGH + 0 CRITICAL) |
| `scoring-api:bentoml` | 1 052,2 Mo | 358 Mo | bentoml | 88 (88 HIGH + 0 CRITICAL) |

`optimized` est sous la cible de 500 Mo en décompressé. Avant correction, elle avait 49 HIGH
(voir section 3) ; la taille a pris 0,6 Mo avec la mise à jour de zlib1g.

## 2. Comparatif des latences

`reports/benchmark.md` : 1000 appels par backend après 10 appels de chauffe, en Python dans le
venv du projet (hors conteneur), x86_64, Python 3.12.14. **Machine chargée** pendant la mesure :
4 CPU logiques, load average 2,08 / 3,39 / 3,01 (1/5/15 min), 3 369 Mio de mémoire disponible
sur 7,8 Gio, 5 conteneurs Docker actifs dont les 3 nœuds du cluster kind.

| Backend | P50 (ms) | P95 (ms) | P99 (ms) |
|---|---|---|---|
| sklearn_pipeline | 11,473 | 16,517 | 20,323 |
| onnx_python | 0,227 | 0,567 | 0,931 |
| onnx_batch_100 | 0,662 | 1,200 | 1,518 |

ONNX vs scikit-learn, P50 sur 1 ligne : ×50,4. Un lot de 100 lignes coûte 0,66 ms en ONNX,
soit environ 6,6 µs par ligne.

**Test de charge (Locust)** sur le conteneur `optimized` (un seul worker uvicorn), 100
utilisateurs, 30 s, Locust sur la même machine : 9 469 requêtes, **0 échec**, ≈ 349 req/s,
P50 220 ms, P95 360 ms, P99 430 ms (`reports/m4/locust_stats.csv`). Ces latences mesurent la
file d'attente d'un worker saturé par 100 utilisateurs, pas le coût de l'inférence (0,23 ms).
Ce test a tourné sur le build d'`optimized` antérieur à la mise à jour de zlib1g ; les deux
builds ne diffèrent que par ce paquet système.

## 3. Interprétation

- **Pourquoi optimized est plus petite (÷3,9 en décompressé).** Base `python:3.12-slim` au lieu
  de `python:3.12` (pas de compilateurs, en-têtes ni bibliothèques Debian inutiles) ; build
  multi-stage : seules les dépendances installées dans `/deps` passent dans l'image finale ;
  dépendances de serving uniquement (onnxruntime, FastAPI, pas de scikit-learn, MLflow ni
  skl2onnx) ; contexte de build en liste blanche (quelques fichiers, au lieu du dépôt avec
  `.git`). BentoML est intermédiaire : il embarque scikit-learn, pandas et son propre runtime.
- **Pourquoi ONNX est plus rapide.** Le pipeline scikit-learn paie, à chaque appel, la
  validation pandas, le ColumnTransformer et l'encodage one-hot en Python ; ONNX Runtime exécute
  un graphe compilé en C++, sans DataFrame. Le gain est massif sur une ligne (le coût fixe
  domine), plus faible par ligne sur un lot.
- **Ce que montrent les scans.** Toutes les vulnérabilités HIGH/CRITICAL sont dans des paquets
  Debian de l'image de base, aucune dans les paquets Python, aucun secret détecté.
  - **optimized** : 49 HIGH au premier scan, dont seulement 2 avec un correctif Debian publié
    (zlib1g, CVE-2026-76844 et CVE-2026-85091), **corrigées** par une mise à jour ciblée ;
    restent **47 HIGH sans correctif publié** (statuts `affected`/`fix_deferred`), listées
    une par une dans `reports/m4/security.md` et **acceptées provisoirement** : bibliothèques
    système (util-linux, ncurses, systemd, perl, sqlite…) que l'API n'appelle pas directement.
    L'absence d'exposition est une hypothèse, pas une preuve.
  - **naive** : 15 CRITICAL sans correctif (libmariadb, libopenexr, libxml2, openssh-client),
    toutes dans des paquets inutiles à l'API : raison suffisante pour ne pas la déployer.
  - **ModelScan** : l'ONNX est « sans problème » parce qu'il est **ignoré** (format protobuf
    sans code, sûr par construction, pas analysé) ; le pickle piégé de démonstration est détecté
    en **CRITICAL** (`os.system`) ; le modèle v7 du registre est en skops (pas un pickle), seul
    type non approuvé `numpy.dtype`, autorisé au Lab 1. Le scan du **pickle embarqué par
    BentoML a échoué** (erreur du scanner ModelScan 0.8.8) : ce pickle n'est **pas vérifié**.

## 4. Choix recommandé

**`scoring-api:optimized`**, poussée en `localhost:5001/scoring-api:1.0.0` et vérifiée par
`docker pull` (même identifiant d'image). Raisons : 3,9 fois plus petite que la naïve, aucune
CVE CRITICAL et aucune HIGH corrigeable restante, non-root avec HEALTHCHECK, modèle ONNX sans
code exécutable au chargement, latence d'inférence inférieure à la milliseconde, et labels qui
relient l'image à la version exacte du registre (`mlflow.model_version=7`). BentoML apporte un
outillage (adaptive batching, model store) utile à plus grande échelle, mais son image est plus
lourde, a plus de CVE, et embarque un pickle que nous n'avons pas pu faire valider par ModelScan.

## 5. Pistes d'amélioration

- **Plusieurs workers uvicorn** (ou réplicas Kubernetes au Lab 5) : sous 100 utilisateurs, la
  latence est dominée par la file d'attente d'un worker unique, pas par l'inférence.
- **Image distroless** ou base plus récente : supprimerait la plupart des 47 HIGH système
  restantes ; rescanner à chaque rebuild (Trivy en CI au Lab 6).
- **Quantization INT8** du graphe ONNX : gain marginal pour une régression logistique de 12,6 ko,
  à ne tenter qu'avec une vérification de parité des décisions.
- **Reproductibilité de l'image** : épingler l'image de base par digest et la version de zlib1g.
- **Modèle ONNX hors Git** (choix du binôme : pas de binaire de modèle dans Git) : la CI du Lab 6
  devra soit exporter le modèle depuis MLflow, soit le récupérer comme artefact ; à décider.
- **Pickle BentoML** : tester une version plus récente de ModelScan, ou sauvegarder le modèle
  BentoML dans un format sans pickle.
