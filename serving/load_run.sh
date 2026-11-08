#!/usr/bin/env bash
# Un palier Locust avec garde-fou : échantillonne la mémoire de la VM Docker et l'état du
# cluster (serving/watch_resources.sh) et ARRÊTE Locust si la mémoire disponible passe sous
# MIN_AVAIL_MIB, si un pod est OOMKilled/Evicted ou si un nœud n'est plus Ready.
# Usage : bash serving/load_run.sh <users> <spawn_rate> <durée> [processes]
set -uo pipefail
USERS=$1 SPAWN=$2 DURATION=$3 PROCS=${4:-1}
MIN_AVAIL_MIB=${MIN_AVAIL_MIB:-500}
OUT=reports/m5/run_${USERS}
RES=reports/m5/resources_run_${USERS}.csv
export ISVC_HOST=${ISVC_HOST:-scoring-model-predictor.scoring.example.com}
bash serving/watch_resources.sh "$RES" 5 &
WATCH=$!
uv run --no-sync locust -f serving/locustfile.py --host http://localhost:30080 \
  --users "$USERS" --spawn-rate "$SPAWN" --run-time "$DURATION" --headless --only-summary \
  --processes "$PROCS" --csv="$OUT" --html="$OUT.html" >"$OUT.log" 2>&1 &
LOCUST=$!
reason=""
while kill -0 "$LOCUST" 2>/dev/null; do
  last=$(tail -n 1 "$RES")
  IFS=, read -r _ avail _ _ oom notready <<<"$last"
  if [[ "$avail" =~ ^[0-9]+$ ]] && [ "$avail" -lt "$MIN_AVAIL_MIB" ]; then reason="mémoire VM ${avail} Mio < ${MIN_AVAIL_MIB}"; fi
  if [[ "$oom" =~ ^[0-9]+$ ]] && [ "$oom" -gt 0 ]; then reason="pod OOMKilled/Evicted"; fi
  if [[ "$notready" =~ ^[0-9]+$ ]] && [ "$notready" -gt 0 ]; then reason="nœud non Ready"; fi
  if [ -n "$reason" ]; then
    echo "ARRÊT DU PALIER ${USERS} : ${reason} ($(date -u +%FT%TZ))" | tee -a "$OUT.log"
    pkill -INT -f "locust -f serving/locustfile.py" ; sleep 5; pkill -f "locust -f serving/locustfile.py"
    break
  fi
  sleep 5
done
wait "$LOCUST" 2>/dev/null
touch "${RES}.STOP"; wait "$WATCH" 2>/dev/null
awk -F, 'NR>1 && $2!="" {if (min=="" || $2<min) min=$2; if ($4>maxp) maxp=$4} END {print "mémoire VM disponible min : " min " Mio ; pods predictor prêts max : " maxp}' "$RES" | tee -a "$OUT.log"
[ -z "$reason" ] && echo "palier ${USERS} terminé normalement" | tee -a "$OUT.log"
