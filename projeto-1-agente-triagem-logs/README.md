# Projeto 1 — Agente de IA para Triagem de Logs de Segurança

Agente que lê eventos de log (SSH, firewall, EDR) e usa um LLM — ou um classificador
heurístico local quando não há chave de API configurada — para:
- classificar o evento (`SUSPEITO`, `NORMAL`, `CRITICO`);
- resumir em linguagem natural o que aconteceu;
- sugerir uma ação (`bloquear_ip`, `investigar_usuario`, `ignorar`, `escalar`).

Projeto de portfólio pessoal explorando IA aplicada a triagem de alertas de segurança.

Documentação completa de engenharia de software em [`docs/`](docs):
- [`01-requisitos.md`](docs/01-requisitos.md) — requisitos funcionais/não funcionais, casos de uso, critérios de aceite.
- [`02-arquitetura-design.md`](docs/02-arquitetura-design.md) — arquitetura, módulos, modelo de dados, contrato de API.
- [`03-plano-de-testes.md`](docs/03-plano-de-testes.md) — plano e casos de teste.

## Como rodar

```bash
docker compose up --build -d
curl http://localhost:8001/health
```

Abra `http://localhost:8001/docs` para a documentação interativa (Swagger UI).

Por padrão, sem nenhuma configuração, o agente já funciona usando o **classificador
heurístico local** (sem custo, sem chave de API). Para usar o Claude de verdade:

```bash
cp .env.example .env
# edite .env e preencha ANTHROPIC_API_KEY
docker compose up --build -d
```

## Exemplo de uso

```bash
curl -s -X POST http://localhost:8001/events/analyze \
  -H "Content-Type: application/json" \
  -d '{"log_line": "Failed password for root from 203.0.113.9 port 51321 ssh2"}' | python3 -m json.tool
```

Processar o arquivo de exemplo inteiro via CLI, dentro do container:

```bash
docker compose run --rm api python -m app.cli --file data/sample_logs.log
```

Consultar o histórico:

```bash
curl -s "http://localhost:8001/events?classification=SUSPEITO" | python3 -m json.tool
curl -s http://localhost:8001/events/stats | python3 -m json.tool
```

## Rodando os testes

```bash
docker compose run --rm api pytest -v
```

## Stack

Python 3.12, FastAPI, Uvicorn, SQLite, SDK oficial `anthropic` (Claude), Pytest, Docker.
