#!/usr/bin/env bash
# Derruba os dois projetos subidos por run-all.sh.
set -euo pipefail
cd "$(dirname "$0")"

docker compose -p triagem-logs -f projeto-1-agente-triagem-logs/docker-compose.yml down
docker compose -p mini-soar -f projeto-2-mini-soar/docker-compose.yml down
