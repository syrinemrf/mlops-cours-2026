# Sécurité des images et du modèle — Lab 4 (2026-11-08)

Trivy `aquasec/trivy:0.75.0` (épinglé, `infra/versions.env`), `--severity HIGH,CRITICAL`, base de
vulnérabilités du jour du scan. Rapports bruts : `reports/trivy_{optimized,naive,bentoml}.txt`.

| Image | HIGH | CRITICAL | Avec correctif publié | Secrets | Couche |
|---|---|---|---|---|---|
| scoring-api:optimized | 47 | 0 | 0 | 0 | debian |
| scoring-api:naive | 273 | 15 | 4 | 0 | debian |
| scoring-api:bentoml | 88 | 0 | 2 | 0 | debian |

Aucune vulnérabilité HIGH/CRITICAL dans les paquets Python des trois images : toutes viennent des
paquets Debian 13 de l'image de base.

## Ce qui a été corrigé

- **scoring-api:optimized** : le premier scan donnait 49 HIGH, dont 2 avec correctif Debian publié,
  toutes deux dans `zlib1g` (CVE-2026-76844, CVE-2026-85091). Corrigées par une mise à jour ciblée
  de `zlib1g` dans le stage runtime (`packaging/Dockerfile`), puis rebuild et nouveau scan :
  **47 HIGH, 0 CRITICAL, 0 corrigeable**.
- **naive** et **bentoml** : non corrigées. Ce sont des images de comparaison qui ne seront pas
  déployées ; le cas de la naïve montre ce qu'apporte `python:3.12-slim`.

## Ce qui est accepté, et pourquoi (scoring-api:optimized)

Les 47 HIGH restantes n'ont **aucun correctif publié** par Debian à la date du scan (statuts
Trivy `affected` ou `fix_deferred`) : elles ne sont pas corrigeables sans changer d'image de base.
Elles sont acceptées provisoirement pour un usage de cours, en local, avec ces limites :

- il s'agit de bibliothèques système de l'image de base (util-linux, ncurses, systemd, perl,
  sqlite…). L'API n'en appelle aucune directement, mais **l'absence d'exposition n'a pas été
  démontrée** : c'est une hypothèse, pas une preuve ;
- le conteneur tourne en non-root (uid 10001), n'expose que le port 8000 et ne contient ni
  compilateur ni gestionnaire de paquets Python inutile ;
- à revoir : nouveau scan à chaque rebuild ; piste de réduction, une image distroless ou
  `-slim` plus récente quand Debian publiera les correctifs.

Détail des 47 HIGH acceptées :

| Paquet | CVE | Version installée | Statut | Titre |
|---|---|---|---|---|
| bsdutils | CVE-2026-76642 | 1:2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| bsdutils | CVE-2026-78408 | 1:2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| bsdutils | CVE-2026-78409 | 1:2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| bsdutils | CVE-2026-78410 | 1:2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |
| libacl1 | CVE-2026-54369 | 2.3.2-2+b1 | affected | acl: Symlink traversal privilege escalation via libacl functions |
| libblkid1 | CVE-2026-76642 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| libblkid1 | CVE-2026-78408 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| libblkid1 | CVE-2026-78409 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| libblkid1 | CVE-2026-78410 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |
| liblastlog2-2 | CVE-2026-76642 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| liblastlog2-2 | CVE-2026-78408 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| liblastlog2-2 | CVE-2026-78409 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| liblastlog2-2 | CVE-2026-78410 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |
| libmount1 | CVE-2026-76642 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| libmount1 | CVE-2026-78408 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| libmount1 | CVE-2026-78409 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| libmount1 | CVE-2026-78410 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |
| libncursesw6 | CVE-2025-69720 | 6.5+20250216-2 | affected | ncurses: ncurses: Buffer overflow vulnerability may lead to arbitrary  |
| libsmartcols1 | CVE-2026-76642 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| libsmartcols1 | CVE-2026-78408 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| libsmartcols1 | CVE-2026-78409 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| libsmartcols1 | CVE-2026-78410 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |
| libsqlite3-0 | CVE-2026-119373 | 3.46.1-7+deb13u2 | affected | sqlite: sqlite: Denial of service via heap-based buffer overflow in FT |
| libsqlite3-0 | CVE-2026-119374 | 3.46.1-7+deb13u2 | affected | sqlite: sqlite: Arbitrary code execution via corrupted FTS5 index |
| libsqlite3-0 | CVE-2026-119379 | 3.46.1-7+deb13u2 | affected | sqlite: sqlite: Arbitrary code execution via crafted session changeset |
| libsystemd0 | CVE-2026-16742 | 257.13-1~deb13u1 | affected | systemd: systemd-homed: Local privilege escalation via missing home-re |
| libtinfo6 | CVE-2025-69720 | 6.5+20250216-2 | affected | ncurses: ncurses: Buffer overflow vulnerability may lead to arbitrary  |
| libudev1 | CVE-2026-16742 | 257.13-1~deb13u1 | affected | systemd: systemd-homed: Local privilege escalation via missing home-re |
| libuuid1 | CVE-2026-76642 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| libuuid1 | CVE-2026-78408 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| libuuid1 | CVE-2026-78409 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| libuuid1 | CVE-2026-78410 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |
| login | CVE-2026-76642 | 1:4.16.0-2+really2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| login | CVE-2026-78408 | 1:4.16.0-2+really2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| login | CVE-2026-78409 | 1:4.16.0-2+really2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| login | CVE-2026-78410 | 1:4.16.0-2+really2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |
| mount | CVE-2026-76642 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| mount | CVE-2026-78408 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| mount | CVE-2026-78409 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| mount | CVE-2026-78410 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |
| ncurses-base | CVE-2025-69720 | 6.5+20250216-2 | affected | ncurses: ncurses: Buffer overflow vulnerability may lead to arbitrary  |
| ncurses-bin | CVE-2025-69720 | 6.5+20250216-2 | affected | ncurses: ncurses: Buffer overflow vulnerability may lead to arbitrary  |
| perl-base | CVE-2026-9538 | 5.40.1-6+deb13u1 | fix_deferred | perl-Archive-Tar: perl-Archive-Tar: Denial of Service via crafted tar  |
| util-linux | CVE-2026-76642 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: failed external mount helper still runs privil |
| util-linux | CVE-2026-78408 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migrat |
| util-linux | CVE-2026-78409 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: X-mount.subdir detached-tree resolution can es |
| util-linux | CVE-2026-78410 | 2.41.5-0+deb13u1 | affected | util-linux: util-linux: restricted bind mounts do not pin the source,  |

## Image naïve : les 15 CRITICAL

Toutes sans correctif publié (`affected`), dans des paquets que `python:3.12` complet embarque
sans que l'API en ait besoin : libmariadb / mariadb-common (CVE-2026-44172, CVE-2026-49261),
libopenexr (CVE-2026-42216, CVE-2026-42217), libxml2 / libxml2-dev (CVE-2026-6653),
openssh-client (CVE-2026-60002). Raison suffisante pour ne jamais déployer cette image.

## ModelScan

| Artefact | Résultat | Ce que ça prouve |
|---|---|---|
| `packaging/model/model.onnx` | « No issues found », 1 fichier **ignoré** | Rien sur le fichier lui-même : ModelScan ne lit pas l'ONNX ; il est sûr par construction (graphe protobuf, sans code) |
| `packaging/scan-demo/malicious.pkl` (démo, jamais chargé, hors Git) | **CRITICAL : 1**, `os.system` (module `posix`) | Le scanner détecte un pickle piégé |
| `packaging/scan-demo/model.pkl` | aucun problème | Pas d'opérateur dangereux dans le pickle du modèle |
| v7 du registre (`model.skops`) | « No issues found », fichiers ignorés (skops n'est pas un pickle) ; skops : seul type non approuvé `numpy.dtype`, autorisé au Lab 1 | Le modèle de production n'est pas un pickle |
| modèle embarqué par BentoML (`saved_model.pkl`) | **erreur du scanner** (`argument of type 'NoneType' is not iterable`) | **Non vérifié** : ce pickle n'a pas pu être analysé par ModelScan 0.8.8 |

Conséquence : l'image de production est l'image ONNX (`scoring-api:optimized`). La variante
BentoML embarque un pickle dont l'analyse a échoué ; elle reste une comparaison locale.

