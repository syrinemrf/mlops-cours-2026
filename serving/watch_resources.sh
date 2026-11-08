#!/usr/bin/env bash
# Échantillonne, pendant un test de charge, la mémoire de la VM Docker et l'état du cluster.
# Une ligne CSV toutes les N secondes ; s'arrête seul quand le fichier STOP existe.
# Usage : bash serving/watch_resources.sh reports/m5/resources_run_100.csv [intervalle_s]
# Colonnes : horodatage UTC, mémoire disponible de la VM Docker (Mio, /proc/meminfo vu
# depuis un conteneur), mémoire des 3 nœuds kind (Mio), pods prêts du predictor,
# pods OOMKilled/Evicted dans le cluster, nœuds non Ready.
set -uo pipefail
OUT=${1:?fichier CSV de sortie}
EVERY=${2:-5}
NS=scoring
SEL="serving.kserve.io/inferenceservice=scoring-model"
echo "utc,vm_mem_available_mib,kind_nodes_mem_mib,predictor_pods_ready,oom_or_evicted,nodes_not_ready" >"$OUT"
while [ ! -e "${OUT}.STOP" ]; do
  avail=$(docker run --rm busybox:1.37 awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo 2>/dev/null)
  nodes=$(docker stats --no-stream --format '{{.MemUsage}}' mlops-lab-control-plane mlops-lab-worker \
    mlops-lab-worker2 2>/dev/null | awk '{v=$1; if (v ~ /GiB/) {sub(/GiB/,"",v); v*=1024} else {sub(/MiB/,"",v)}; s+=v} END {printf "%d", s}')
  ready=$(kubectl get pods -n "$NS" -l "$SEL" --no-headers 2>/dev/null | awk '$2 ~ /^2\/2|^1\/1/ && $3=="Running"' | wc -l)
  oom=$(kubectl get pods -A --no-headers 2>/dev/null | grep -cE 'OOMKilled|Evicted')
  notready=$(kubectl get nodes --no-headers 2>/dev/null | awk '$2!="Ready"' | wc -l)
  echo "$(date -u +%FT%TZ),${avail},${nodes},${ready},${oom},${notready}" >>"$OUT"
  sleep "$EVERY"
done
rm -f "${OUT}.STOP"
