# Projeto 2 — Mini SOAR de Integração de Ferramentas

Automação que recebe um IP ou hash suspeito, consulta sua reputação em uma fonte de
threat intelligence (AbuseIPDB para IPs, VirusTotal para hashes — ou uma base local
mockada quando não há chave configurada) e envia um alerta formatado para Slack/Discord
(ou registra localmente em modo mock), com um worker que reexecuta o playbook em
intervalos fixos.

Projeto de portfólio pessoal explorando automação de resposta a incidentes de segurança.

Documentação completa de engenharia de software em [`docs/`](docs):
- [`01-requisitos.md`](docs/01-requisitos.md)
- [`02-arquitetura-design.md`](docs/02-arquitetura-design.md)
- [`03-plano-de-testes.md`](docs/03-plano-de-testes.md)

## Como rodar

```bash
docker compose up --build -d
curl http://localhost:8002/health
```

Abra `http://localhost:8002/docs` para a documentação interativa (Swagger UI).

Por padrão, sem nenhuma configuração, tudo já funciona em **modo mock** (base local de
reputação + notificações registradas em modo console, visíveis via `GET /notifications`).
Para usar as APIs e webhooks reais:

```bash
cp .env.example .env
# edite .env com suas chaves/webhooks
docker compose up --build -d
```

## Exemplo de uso

```bash
# Consultar um indicador malicioso conhecido da base mock
curl -s -X POST http://localhost:8002/lookup \
  -H "Content-Type: application/json" \
  -d '{"indicator": "203.0.113.9"}' | python3 -m json.tool

# Ver notificações geradas
curl -s http://localhost:8002/notifications | python3 -m json.tool

# Rodar o playbook manualmente contra a fila de exemplo (data/indicators_queue.json)
curl -s -X POST http://localhost:8002/playbook/run-queue | python3 -m json.tool

# Acompanhar o worker rodando o playbook automaticamente
docker compose logs -f worker
```

## Rodando os testes

```bash
docker compose run --rm api pytest -v
```

## Stack

Python 3.12, FastAPI, Uvicorn, SQLite, `httpx`, Pytest, Docker Compose (2 serviços:
`api` + `worker`).
