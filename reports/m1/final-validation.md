# M1 — finalisation technique DVC / Feast

Date : 2026-10-20. Branche work/syrine/m1. Historique conservé, aucun push,
PR, merge ou tag créé. Protocole pédagogique A uniquement ; B1/B2 et les
hypothèses XP-Cube restent inchangés. Tests/comparaisons A sur test répété :
aucune performance scientifique indépendante ni supériorité statistique revendiquée.

## Précontrôles et limites d’infrastructure

Après un arrêt préalable demandé pour pression mémoire/disque, Syrine a réduit la
charge du poste. Docker CLI info reste parfois lent/expiré ; le moteur a été vérifié
par GET /info sur son socket : version 28.4.0, quatre conteneurs Running, overlayfs.
Docker ps, les trois nœuds Ready, pods SeaweedFS/MLflow1/1 et PVC Bound sont vérifiés.
Les restartCount étaient2 pour les deux services, événements historiques expirés.
Les nœuds n’indiquaient ni MemoryPressure ni DiskPressure ; endpoints MLflow et S3
répondaient. Environ1.2–1.4 Gio disponibles sur 3.8 Gio, swap encore fortement utilisé.
D: conserve192Go libres, disque virtuel WSL945Gio. Aucun volume, cluster ou service
recréé, supprimé ou réinitialisé. Les opérations ont été séquentielles et légères.
L’anomalie CLI n’est pas déclarée résolue et sa cause n’est pas démontrée.

Mode du vérificateur officiellement corrigé100644→100755 ; son contenu Git reste
identique (blob592a04ba431d6314b8bf2787b573c64c91d6b6ee). Aucune modification des
critères. Avant DVC, le précédent modèle smoke local a été déplacé, sans perte ni
suppression, dans models/smoke-history ; tous ses hashes ont été revérifiés.
[Preuve de conservation](final-model-backup.json).

## DVC : quatre stages et filiation

- download et prepare conservés : première repro les ignore. Données et split
  stratifié80/20 seed42 inchangés, 1176/294 lignes (190/47 Yes).
- train : une seule exécution de LR C=.1 balanced, autres paramètres existants inchangés.
  Le rôle MLflow distingue désormais pedagogical_pipeline des smoke tests.
- evaluate : modèle local et seuil de ses métadonnées, aucun serveur MLflow requis ;
  JSON conforme à l’étape 8, valeurs arrondies à4 décimales, confusion et n_test inclus.
- Dépendances officielles conservées et complétées pour les fichiers réellement lus :
  CSV brut (hash tracé), lecteur de contrat, uv.lock et sections de contrat pertinentes.
  Cache du modèle DVC, métriques cache:false suivies par Git.

Run réel : **b55a5e9846cb44aeac027426280053e8**, FINISHED, expérience scoring,
protocol=A / protocol_id=mlops_A_v1 / launched_by=dvc. Code entraîné 82f2cc7.
MD5 brut DVC et tag MLflow : **16e6acc1f69d648c4ec1d3b44efc0179**. Il s’agit du
CSV exporté ; version source Kaggle1 et empreinte source restent dans dataset.yaml.
Seuil modèle0.8384353741496599 ; paramètres C=.1 et balanced vérifiés.
ROC AUC exacte0.8329744164010682, AP0.6392128739124473, coût expérimental36.
[Paramètres, tags, métriques et hashes](final-lineage.json).

Commandes réellement exécutées : dvc dag, dvc repro, dvc status, dvc metrics show,
dvc push (**6 fichiers poussés**), seconde évaluation, seconde repro, status --cloud.
Le JSON de la seconde évaluation est identique octet par octet ; les quatre stages
sont ignorés lors de la seconde repro. Les métriques communes au smoke LR C=.1 balanced
sont identiques à1e-12 près, donc deux fits distincts concordent ici ; aucune garantie
bitwise universelle sur tout matériel. [Preuve](final-metric-reproducibility.json).
DVC status : à jour ; status --cloud : cache et remote storage synchronisés.

Le lock généré par DVC a été normalisé pour le lint en préservant les valeurs YAML1.2
(notamment la chaîne Yes, ambiguë en YAML1.1). Les entrées download/prepare restent
sémantiquement identiques à celles d’origine, et leurs sorties n’ont pas été régénérées.
L’exercice8.5 de changement de poids n’a pas été exécuté : conservation des paramètres
exigée ; pas de nouvel essai opportuniste ni de téléchargement forcé.

## Contenu exact de reports/metrics.json

```json
{
  "tn": 244.0,
  "fp": 3.0,
  "fn": 33.0,
  "tp": 14.0,
  "pr_auc_trapezoidal": 0.6363,
  "brier_score": 0.1463,
  "log_loss": 0.4508,
  "roc_auc": 0.833,
  "average_precision": 0.6392,
  "f1": 0.4375,
  "precision": 0.8235,
  "recall": 0.2979,
  "accuracy": 0.8776,
  "business_cost": 36.0,
  "decision_threshold": 0.8384,
  "confusion": {
    "tn": 244,
    "fp": 3,
    "fn": 33,
    "tp": 14
  },
  "n_test": 294
}
```

## Registre préservé, conflit de l’étape 8.4 explicité

| Version | Rôle | Run ID | ROC AUC |
|---|---|---|---:|
| 1 | champion, LR C=1 sans poids | 5ef49fc5f3e740f28c523b0dcc1ae8c1 | 0.8368507193 |
| 2 | Dummy failed | 0c42486a18f340ddb2db995d8797c70d | 0.5 |
| 3 | challenger, LR C=.1 sans poids | 139ae364aa6e4166b2bd19ef533f48e7 | 0.8360754587 |

Toujours trois versions ; alias contrôlés après la repro. Le run DVC n’a pas été
promu/enregistré comme nouvelle version. L’étape 8.4 officielle affecterait les deux
alias à un autre modèle, LR .1 balanced. Options annoncées avant toute opération :
(1) conserver les alias et la filiation DVC séparée (appliqué) ; (2) enregistrer
ultérieurement le run DVC sans toucher les alias via une opération dédiée autorisée ;
(3) convenir d’un nouveau paramétrage/recalcul et d’une promotion explicite. Ces deux
dernières options ne sont pas exécutées. Le 18/18 ne prouve donc pas que le champion
actuel a été produit par la configuration DVC courante. Gate .70 inchangée, distincte
du seuil de décision du modèle DVC. Aucun scénario Jia exécuté.

## Feast appliqué, matérialisé et vérifié

Entité employee / EmployeeNumber (INT64), vue request_features, service scoring_v1,
source Parquet1470×29 : clé +27 prédicteurs +timestamp. Schéma depuis dataset.yaml :
13Float64 et14String. Identifiant, cible, Age/Gender/MaritalStatus hors prédicteurs.

feast apply et materialize-incremental ont réussi. Offline : **1176×30**, les27
features correspondent exactement aux valeurs de train, numériques et catégories.
Online : **1 salarié,27 features**, aucune valeur manquante inattendue et toutes
identiques à la préparation. Trois requêtes une seconde avant le snapshot renvoient
des features manquantes, comme attendu. [Résultats](final-feast-verification.json).

Timestamp fixe2026-01-01T00:00:00+00:00, TTL 3650jours pédagogique. Données fictives,
pas d’historique temporel RH réel ; ce test mécanique ne démontre pas l’absence de
fuite temporelle en production. Bases locales ignorées, jamais suivies par Git.

## Tests, contrôle intermédiaire et contrôle final

- Tests globaux : **77 passed,1 warning in15.73s**. Warning NumPy/Feast sur l’unité
  generic de timedelta, sans échec ; dépendances verrouillées inchangées.
- Cinq nouveaux cas : évaluation au seuil stocké, répétabilité, rejet du seuil non fini,
  schéma/entité Feast et séparation des colonnes. Pas de test supprimé/skip/xfail.
- Deux échecs initiaux de fixtures sont conservés : mock d’un module MLflow lazy et
  propriété Feast join_keys au lieu de join_key. Les fixtures ont été corrigées,
  sans modifier des contrôles officiels ou des données pour rendre le résultat vert.
- make lint : ruff check, ruff format et yamllint réussis.
- Contrôle intermédiaire : **17/18**, seul Feast absent.
- Contrôle final réel : **make check-m1,18/18,code retour0**, au commit techniqueccf031f.
  [Sortie complète](check-m1-final.log). Vérificateur intact, mode755 autorisé.

## Clone propre : portée réelle de la reproduction

Nouveau dossier /tmp/mlops-m1-repro-2d_9ct98, commit ccf031f, cache DVC initialement vide.
Pull depuis le remote puis repro : quatre stages ignorés, métriques et lock identiques
octet par octet. Évaluation locale également réussie avec tracking URI volontairement
injoignable, démontrant l’autonomie de ce stage. Feast reconstruit et vérifié offline/
online dans ce clone. État Git propre ; compteur MLflow25 avant/après, aucun fit ajouté.
[Preuve](final-clean-clone.json), [commandes et retours](final-clean-clone-commands.json).

Environnement Python existant réutilisé par PATH : ni uv sync vierge ni nouveau cluster
n’ont été testés. Le lien de venv créé au premier essai apparaissait comme fichier
non ignoré (le motif .venv/ ignore les dossiers) ; seul notre lien superflu a été retiré,
sans supprimer l’environnement ni aucun dossier. Contrôles répétés et état propre
vérifiés ; log initial conservé. Credentials du clone uniquement dans son fichier
local ignoré, mode600, dossier temporaire privé conservé. Pas de suppression de dossier.

## Reprise, revue et J0

Procédure complète pour même poste, autre étudiant et cluster d’Aziz dans NOTES.md.
Un serveur vierge a ses propres runs/versions : ne pas réutiliser les run IDs de Syrine.
Le recalcul indépendant peut changer le hash du dossier MLflow (run ID/dates) sans
changer les métriques ; garder ces écarts pour revue, pas écraser le lock de référence.

Prochaines actions uniquement : revue par Syrine, publication après autorisation,
comparaison/intégration avec le travail réel d’Aziz via lab/m1-versioning, PR et revue
GitHub effective, nouvelle validation sur le commit d’intégration. Pour J0 Setup finS3,
vérifier organisation optionA, socle M0/M1, dataset validé, card/ADR/journal et preuves ;
tag j0 seulement après autorisation. Aucun push/PR/merge/tag réalisé ici, aucune
contribution ni approbation d’Aziz inventée. Validation technique M1 acquise ; validation
scientifique B1/B2 et originalité des RQ demeurent hors de cet incrément.
