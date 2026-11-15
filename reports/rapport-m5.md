# Rapport — Lab 5 : serving avec KServe

Binôme : Syrine Maaref (@syrinemrf) et Aziz (@MohamedAzizKouch) · Dataset : `ibm-hr-attrition` ·
Modèle : `scoring-model` v7 (run `ef5f2ec9`, `launched_by=airflow`, origine du run Airflow non
établie) · Seuil de décision servi : 0,5 (= `decision_threshold` du champion v7 lu dans MLflow)

Mesures du 2026-11-08 sur un poste Windows/WSL2 : VM Docker 4 CPU et 7 944 Mio, cluster kind
du Lab 0 (3 nœuds) conservé. Pour libérer de la RAM, 12 déploiements KFP ont été mis à 0
pendant le lab (`reports/m5/kfp-paused.md`), sans toucher MySQL, SeaweedFS, les PVC ni MLflow.

## 1. Résumé

InferenceService `scoring-model` en mode **Knative** (KServe v0.21.0, Knative/Kourier
knative-v1.23.0). Il sert l'image FastAPI + ONNX du Lab 4 (`localhost:5001/scoring-api:1.0.0`,
inchangée), appelée par la passerelle Kourier sur `http://localhost:30080` avec l'en-tête `Host`.
Notre cluster a été créé avant le mappage du port 30080 : un relais socat
(`serving/kourier-relay.sh`) l'expose sans recréer le cluster. Autoscaling KPA sur le débit
(`rps`, cible 200, 0 à 5 pods, scale-to-zero). En fin de lab, la **v2.0.0** (même modèle v7,
route `/version`) sert 100 % du trafic après un canary à 10 %.

Installation : le script s'est arrêté sur une configuration LLM refusée par le webhook de
KServe 0.21.0, sans lien avec ce lab ; ses deux dernières étapes ont été complétées avec les mêmes
commandes (`reports/m5/kserve-install.md`).

## 2. Benchmark de latence

Locust (`serving/locustfile.py`, vraies lignes de `test.csv`, une demande par requête, attente
de 0,1 à 0,3 s), un seul processus Locust sur le même poste, via le relais et Kourier. Sortie de
`serving/locust_report.py`, requêtes `/predict` seulement :

| Run | Requêtes | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Erreurs (%) |
|---|---|---|---|---|---|---|
| run_100 | 18907 | 161.7 | 240 | 1200 | 3100 | 0.15 |
| run_500 | 24866 | 139.8 | 2500 | 7600 | 20000 | 0.03 |
| run_1000 | 10356 | 58.3 | 3400 | 57000 | 108000 | 0.61 |

Les durées sont 2 min pour run_100 et 3 min pour run_500 et run_1000. Toutes les erreurs sont des
`502 Bad Gateway` : 28, 8 et 63 ; celles de run_100 tombent toutes dans la même seconde, pendant la
montée en charge (cause non établie).

**Point de saturation.** Dès 100 utilisateurs, le P99 dépasse 3 s ; le **débit maximal mesuré
est de 161,7 req/s** (run_100), puis il **baisse** quand la charge augmente (139,8 puis 58,3).
Ce n'est pas le modèle qui sature. Au run_1000, le CPU des conteneurs du modèle est en moyenne de
**120 m** par pod (24 mesures, maximum 355 m) pour une limite de 1 CPU ; le relais socat reste
sous 10 % de CPU et Kourier sous 0,17 CPU (`reports/m5/bottleneck_run_1000.txt`). Le goulot est
donc en amont des pods, côté client : publication de port de Docker Desktop sous WSL2, nombre de
connexions, ou Locust à un seul processus (aucune alerte CPU de Locust). **Hypothèse non
confirmée.** Ces chiffres décrivent ce banc d'essai local, pas la capacité du service.

**Mémoire (garde-fou).** `serving/load_run.sh` arrêtait Locust si la mémoire disponible de la VM
passait sous 500 Mio, si un pod était OOMKilled/Evicted ou si un nœud n'était plus Ready. Aucun
arrêt n'a été nécessaire. Mémoire disponible minimale : 2 267 Mio (run_100), 2 033 Mio (run_500),
1 990 Mio (run_1000), sans OOM ni nœud instable. Le palier 1 000 a donc été tenté selon la
règle convenue.

## 3. Scale-up observé

| Run | Pods (max observé) | CPU moyen par pod | Temps pour atteindre ce nombre de pods |
|---|---|---|---|
| run_100 | 3 | non mesuré | 89 s (départ à 1 pod après le démarrage à froid) |
| run_500 | 2 | non mesuré | non établi (voir limite) |
| run_1000 | 3 | 120 m (24 mesures, max 355 m) | présent dès la 1re mesure (pods restés du run précédent) |

**Limite de mesure.** Les pods ont été comptés par `serving/watch_resources.sh`, une mesure toutes
les 15 à 20 s. Pendant run_500 et run_1000, il compte parfois 0 pod prêt alors que les requêtes
réussissaient : ses appels `kubectl`, dont les erreurs sont masquées, ont probablement échoué
sous charge. Les maxima ci-dessus sont des **minorants**, et le délai de montée n'est fiable que
pour run_100. Le faible nombre de pods est cohérent avec le débit plafonné : 160 req/s
correspondent à un peu plus d'un pod pour une cible effective de 140 req/s par pod.

Scale-to-zero : **0 pod 57 s après le début d'une observation sans trafic** (le pod était déjà
inactif avant le début : ce n'est pas un délai depuis la dernière requête) · démarrage à froid
(`curl -w`) : **19,8 s** pour la première requête, puis 0,077 s à chaud
(`reports/m5/scale-to-zero.txt`).

## 4. Analyse canary

- Répartition observée sur **1 000** requêtes `/metadata` (plutôt que 200, pour réduire la
  variance) : **891 × 1.0.0 / 109 × 2.0.0**, 0 erreur.
- Cohérence avec 90/10 : 10,9 % contre 10 % attendus. Pour 1 000 tirages à p = 0,1, l'écart-type
  est d'environ 9,5 requêtes : l'écart de 9 est d'environ 1 écart-type, compatible avec 90/10.
  Les adresses dédiées répondent correctement : `latest-…` donne 2.0.0, `prev-…` donne 1.0.0.
- **Décision : promotion.** Critère vérifié avant de promouvoir : sur 50 lignes de test, les
  deux révisions renvoient des probabilités identiques (écart maximal 0), 50/50 décisions
  identiques, même seuil 0,5 et même modèle v7 ; aucune erreur pendant le canary. Après
  `canaryTrafficPercent: 100`, 200 requêtes sur 200 ont répondu 2.0.0. La v2 ne change que la
  route `/version` ; un canary sur un nouveau **modèle** exigerait aussi une comparaison des taux
  d'erreur, des latences et de la distribution des scores, idéalement automatisée (Labs 6-7).

## 5. Points d'amélioration

- **Mesurer sans le goulot du poste** : lancer Locust depuis un pod du cluster ou avec
  `--processes`, sans passer par le relais, pour séparer la capacité du service de celle du poste.
- **Concurrence plutôt que RPS** : l'API n'a qu'un worker uvicorn ; une cible en `concurrency`
  (ex. 10) ou plusieurs workers par pod refléterait mieux sa capacité réelle.
- **Démarrage à froid de 19,8 s** : garder `minReplicas: 1` en heures ouvrées, ou précharger
  l'image sur les nœuds.
- **Batching** : l'inférence ONNX d'un lot de 100 lignes coûte 0,66 ms (Lab 4) ; regrouper les
  demandes réduirait fortement le coût réseau par prédiction.
- **Mesure du scale-up** : compter les pods à partir des événements Knative (KPA) plutôt que par
  `kubectl` sous charge.
- **Canary automatisé** : critère d'erreurs et de latence, rollback automatique (Labs 6-7).

## 6. (Optionnel) Comparatif des serveurs et bonus batch

**Non réalisée, optionnelle.** Triton et BentoML sur KServe n'ont pas été déployés. Ce choix évite
toute écriture dans S3 (`s3://models/triton/`) et tout secret dans le cluster. Le comparatif
local sklearn / ONNX / BentoML figure dans le rapport du Lab 4. Bonus batch non mesuré.
