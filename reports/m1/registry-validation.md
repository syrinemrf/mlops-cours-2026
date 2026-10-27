# M1 — validation de l’étape 7 : Model Registry

Date : 2026-10-20. Branche work/syrine/m1. Protocole A pédagogique uniquement.
Choix autorisés par Syrine : LR C=1 sans poids champion, LR C=.1 sans poids
challenger, Dummy comme contrôle négatif. Coûts expérimentaux 1:1, ROC AUC primaire
et gate .70 inchangés. B1/B2, split, variables et dépendances verrouillées inchangés.

## Diagnostic préalable et stabilité

Deux vérifications successives en lecture seule avant l’implémentation : Docker
28.4.0 répond, conteneurs kind/registry actifs depuis environ2h, trois nœuds Ready,
MemoryPressure/DiskPressure/PIDPressure False ; pods SeaweedFS/MLflow Running 1/1.
RAM3.8 Gio, environ1.1 Gio disponible, swap1.7/2 Gio ; PSI mémoire récente inférieure
à1%, très inférieure à l’incident précédent. Disque WSL environ945 Gio disponible ;
disques des volumes kind environ928 Gio libres. PVC SeaweedFS10Gi et MLflow2Gi Bound.
Pas de nouvelle instabilité observée justifiant un arrêt des opérations légères.

Événements : SeaweedFS a été tué après échec de liveness (événement Killing), puis
redémarré ; exit137, reason Error, fin2026-10-20T12:07:21Z. Ce n’est pas une preuve
OOMKilled. Les événements comportent aussi des timeouts readiness/liveness et un
refus de connexion S3 au démarrage ; MLflow avait des timeouts readiness historiques.
Aucune suppression, recréation, réinitialisation ou relance de service effectuée ici.

Snapshots avant/après opérations : [avant](registry-infra-before.json),
[après](registry-infra-after.json). Docker et /health répondent aux deux ; trois
nœuds Ready, deux pods prêts, compteurs de restart inchangés à2 pour chacun.
Les processus sont consignés par nom uniquement, sans arguments potentiellement secrets.

## Versions réellement enregistrées

| Version | Rôle final | Run ID | ROC AUC réelle | Gate .70 |
|---|---|---|---:|---|
| 1 | champion | `5ef49fc5f3e740f28c523b0dcc1ae8c1` | 0.836850719270 | passed |
| 2 | Contrôle négatif Dummy | `0c42486a18f340ddb2db995d8797c70d` | 0.500000000000 | failed |
| 3 | challenger | `139ae364aa6e4166b2bd19ef533f48e7` | 0.836075458696 | passed |

Registre : **scoring-model**, trois versions distinctes READY, chacune rattachée à
son vrai run et modèle loggé. Tags de version : roc_auc exact, primary_metric,
promotion_threshold, validation_status, source_run_id, data_md5, data_sha256,
data_version, dataset, protocol=A, protocol_id=mlops_A_v1, selection_scope et
seuil de décision. Le hash DVC commun reste16e6acc1f69d648c4ec1d3b44efc0179.

Les alias ont été vérifiés par get_model_version_by_alias : champion→v1/run
5ef49fc5f3e740f28c523b0dcc1ae8c1 ; challenger→v3/run139ae364aa6e4166b2bd19ef533f48e7.
Notre réponse search_model_versions n’expose pas les alias (listes vides) ; les
resolved_aliases du JSON proviennent de cette vérification explicite des alias.

## Ordre, gate et idempotence

Le comportement par défaut du professeur est conservé : enregistrer/réutiliser la
version, poser challenger, puis déplacer champion uniquement si score>=gate.
La nouvelle option explicite --challenger-only permet d’affecter le challenger
convenu sans déplacer le champion ; elle ne baisse ni ne contourne la gate.

Ordre réellement exécuté deux fois via promote_run (la fonction appelée par la CLI) :

1. LR C=1 : v1, gate réussie ; champion et challenger pointent provisoirement surv1.
2. Dummy : v2, AUC=.5<.7, validation_status=failed ; challenger pointe provisoirement
   surv2, champion restev1. Rejet du champion contrôlé immédiatement après l’appel.
3. LR C=.1 avec challenger_only=True : v3, gate réussie ; seul challenger est déplacé.
   État convenu final championv1 / challengerv3.

Seconde exécution réelle : mêmes versions1/2/3, created=False pour les trois appels,
aucune version supplémentaire ; les tags/alias sont réaffectés de façon idempotente.
L’idempotence est séquentielle ; pas de verrou distribué ni garantie de concurrence.
[Opérations et états intermédiaires](registry-operations.json), [log](registry-operations.log).

Commandes CLI équivalentes pour reproduire cet ordre :

```bash
python -m src.promote --run-id 5ef49fc5f3e740f28c523b0dcc1ae8c1
python -m src.promote --run-id 0c42486a18f340ddb2db995d8797c70d
python -m src.promote --run-id 139ae364aa6e4166b2bd19ef533f48e7 --challenger-only
```

Le script rejette avant écriture les runs non terminés, autres protocoles/expériences,
un dataset différent, un score non fini, un seuil invalide, un modèle non READY,
une mauvaise filiation et les doublons de versions déjà présents. Il conserve
--run-id/--filter et la recherche automatique officielle, limitée au protocoleA.

## Chargement distant et prédictions réelles

URI : models:/scoring-model@champion. Chargement sklearn distant réussi, pipeline27
variables vérifié, estimateur LR C=1 et class_weight=None. Seuil de décision du modèle
**0.5**, identique au paramètre du run. Il est distinct du seuil de promotion **0.70**.

Probabilités Yes des cinq premières observations du test :

```text
[0.054739472931851135, 0.004567934055242384, 0.07695643206029057, 0.003461122499474431, 0.4529688832327809]
```

Décisions à0.5 : [0,0,0,0,0] (No). Concordance exacte avec model.predict et le
chargement MLflow pyfunc, cinq prédictions finies ; aucun ajustement sur ces lignes.
Ce petit préfixe sert au test de chargement, pas à estimer les performances du modèle.
Aucune observation brute ni identifiant d’employé ajouté à Git.
[Résultats JSON](registry-verification.json), [log](registry-verification.log).
Vérification réexécutable en lecture du registre : python -m src.verify_registry.

## Tests et limites

- Tests globaux : **72 passed in12.21s**, dont12 nouveaux cas promotion.
- Frontière de gate testée hors réseau : .699999 rejeté, .70 accepté ; .5 rejeté,
  .8 accepté. Fixtures synthétiques, pas de métriques d’expériences inventées.
- Gate réellement exercée dans MLflow : LR au-dessus de.70, Dummy à.5 en dessous,
  champion conservé après Dummy, idempotence des trois versions et état final vérifiés.
- Ruff check, ruff format et yamllint via make lint : résultats dans registry-lint.log.
- Aucune donnée brute, modèle binaire, environnement ou credential suivi ; aucun
  vérificateur officiel modifié, aucun entraînement ni changement de protocole.

Les deux LR ont été retenues après comparaisons répétées sur le test. Leur AUC n’est
pas une estimation finale indépendante, et leur différence est négligeable : aucune
supériorité statistique, causalité ou utilité économique RH démontrée. Les tags passed
attestent uniquement la gate pédagogique, pas une validation scientifique ou métier.

**L’étape7 est validée sur les contrôles demandés.** Le Lab M1 complet reste à vérifier.
Les étapes8/9 ne sont pas exécutées : stages DVC train/evaluate, reports/metrics.json,
reproduction/push et filiation runDVC restent à finaliser à l’étape8 ; configuration,
application et matérialisation du feature store à l’étape9. Aucun push Git ni merge.

## Diagnostic du vérificateur officiel après commit

Sur le commit418d026 : `make check-m1` échoue au lancement (make exit2,
recette Error126 / Permission denied). Le script labs/m1-versioning/check.sh est
suivi en mode100644 et présent en644 ; contenu et droits laissés intacts.
Preuve : [invocation make](check-m1-after-registry.log).

Son exécution intacte avec `bash labs/m1-versioning/check.sh` termine avec le code4 :
**14 contrôles réussis sur18**, quatre échecs réels attendus à ce stade :

1. Pipeline DVC final incomplet : stages train/evaluate et lock associés absents.
2. reports/metrics.json absent : évaluation finale du pipeline à produire à l’étape8.
3. Aucun run lancé par DVC portant le data_md5 attendu : filiation à établir à l’étape8.
4. Feature store Feast non appliqué/matérialisé : étape9 non exécutée.

Les quatre contrôles officiels Registry réussissent : au moins3 versions, champion
au-dessus du seuil, challenger présent, champion chargeable et prédiction réalisable.
[Diagnostic complet via bash](check-m1-after-registry-bash.log).

Pour obtenir un vrai `make check-m1`18/18 : finaliser les étapes8/9 après autorisation,
puis corriger le droit de lancement du script officiel sans modifier ses critères,
et relancer la commande make. Aucune étape8/9 ni correction du vérificateur réalisée
pour ce diagnostic. **Étape7 validée ; Lab M1 global non validé.**
