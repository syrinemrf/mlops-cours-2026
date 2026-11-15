#!/usr/bin/env bash
# Relais localhost:30080 -> NodePort Kourier (30080) du cluster kind, SANS recréer le cluster.
# Notre cluster a été créé avant l'ajout du mappage 30080 dans infra/kind/kind-config.yaml :
# `docker port mlops-lab-control-plane` ne liste que 80, 443 et 6443. Un conteneur socat
# sur le réseau docker « kind » expose le port sur le poste (127.0.0.1 seulement).
# Usage : bash serving/kourier-relay.sh start | stop
set -euo pipefail
NAME=m5-kourier-relay
case "${1:-start}" in
  start)
    docker run -d --name "$NAME" --restart=no --network kind -p 127.0.0.1:30080:30080 \
      alpine/socat:1.8.0.3 -d TCP-LISTEN:30080,fork,reuseaddr \
      TCP-CONNECT:mlops-lab-control-plane:30080
    ;;
  stop) docker rm -f "$NAME" ;;
  *) echo "usage: $0 start|stop" >&2; exit 2 ;;
esac
