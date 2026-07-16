#!/usr/bin/env bash
# Sobe os dois projetos de portfólio ao mesmo tempo, cada um como um projeto Docker
# Compose independente (evita colisão de nomes de serviço entre os dois projetos).
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Subindo projeto 1: agente de triagem de logs (porta 8001)"
docker compose -p triagem-logs -f projeto-1-agente-triagem-logs/docker-compose.yml up --build -d

echo "==> Subindo projeto 2: mini SOAR (porta 8002)"
docker compose -p mini-soar -f projeto-2-mini-soar/docker-compose.yml up --build -d

echo
echo "Projeto 1 (triagem de logs): http://localhost:8001/docs"
echo "Projeto 2 (mini SOAR):       http://localhost:8002/docs"
