# Installation de KServe dans le cluster existant — 2026-11-08

Cluster `kind-mlops-lab` conservé (ni recréation ni suppression). Relevé avant
installation : `reports/m5/before-kserve.txt` (pods, mémoire). Versions épinglées de
`infra/versions.env` : Knative Serving et Kourier knative-v1.23.0,
cert-manager v1.21.2, KServe v0.21.0, metrics-server v0.9.0 ; KEDA non installé.

## Déroulé

1. `make kserve` : refusé (`Permission denied`), `infra/kserve/install.sh` est en mode 644
   comme dans le dépôt du cours. Script lancé via `bash infra/kserve/install.sh`, mode inchangé.
2. Le script s'est **arrêté (code 1)** à l'application de `kserve-cluster-resources.yaml`.
   Une ressource LLM est refusée par le webhook de KServe v0.21.0 (incohérence en amont,
   6 essais) :

   ```
Error from server (Forbidden): admission webhook "llminferenceserviceconfig.kserve-webhook-server.v1alpha2.validator" denied the request: failed to merge config: template: config:1:2596: executing "config" at <.Spec.TrustRemoteCode>: can't evaluate field TrustRemoteCode in type v1alpha2.LLMInference
   ```

   Les 15 ClusterServingRuntimes (dont sklearn, triton et mlserver) et 12
   LLMInferenceServiceConfig ont été appliqués ; seule la configuration LLM refusée manque.
   Elle ne sert pas à ce lab (aucun LLMInferenceService).
3. Les deux dernières étapes du script, non exécutées à cause de cet arrêt, ont été
   **complétées à la main avec les mêmes commandes** : contrôleurs
   `llmisvc-controller-manager` et `kserve-localmodel-controller-manager` remis à 0 réplique
   (comportement par défaut `KSERVE_LIGHT=1`), puis metrics-server v0.9.0 avec
   `--kubelet-insecure-tls`.

## État vérifié après installation

- 3 nœuds `Ready` ; aucun pod Pending, OOMKilled ou Evicted (seul pod non Running : le pod
  du run KFP `scoring-bad-data-test` du Lab 3, en échec attendu).
- knative-serving (activator, autoscaler, controller, net-kourier-controller, webhook),
  3scale-kourier-gateway, cert-manager (3 pods), kserve-controller-manager 2/2 : Running.
- 16 CRD `serving.kserve.io`, 15 ClusterServingRuntimes, service `kourier` en NodePort
  `80:30080/TCP`, `kubectl top nodes` opérationnel.
- Mémoire disponible de la VM Docker (7 944 Mio) : 3 763 Mio pendant l'installation,
  2 864 Mio une fois la pile prête.
