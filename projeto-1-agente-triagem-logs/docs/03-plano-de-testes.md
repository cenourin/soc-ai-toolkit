# Plano de Testes — Agente de IA para Triagem de Logs

## 1. Estratégia

Testes automatizados com `pytest`, executados dentro do container (mesmo ambiente de
execução) via `docker compose run --rm api pytest -v`. Não dependem de rede nem de
`ANTHROPIC_API_KEY` — o classificador heurístico é usado como engine padrão nos testes,
garantindo determinismo.

## 2. Casos de teste

| ID | Caso | Tipo | Resultado esperado |
|----|------|------|---------------------|
| T01 | `test_heuristic_bruteforce_ssh` | Unitário | Log de `Failed password` classificado como `SUSPEITO`/`CRITICO`, ação `bloquear_ip` ou `investigar_usuario` |
| T02 | `test_heuristic_normal_login` | Unitário | Log de login bem-sucedido classificado como `NORMAL`, ação `ignorar` |
| T03 | `test_heuristic_port_scan` | Unitário | Log de múltiplas portas/conexões classificado como `SUSPEITO` |
| T04 | `test_health_endpoint` | Integração (API) | `GET /health` retorna 200 e `{"status": "ok"}` |
| T05 | `test_analyze_endpoint_persists_event` | Integração (API) | `POST /events/analyze` retorna 200, evento aparece em `GET /events` |
| T06 | `test_analyze_batch_endpoint` | Integração (API) | `POST /events/analyze-batch` processa N linhas e retorna N resultados |
| T07 | `test_analyze_rejects_empty_log` | Integração (API) | `POST /events/analyze` com `log_line=""` retorna 422 |
| T08 | `test_stats_endpoint` | Integração (API) | `GET /events/stats` retorna contagem coerente após inserir eventos conhecidos |
| T09 | `test_filter_by_classification` | Integração (API) | `GET /events?classification=SUSPEITO` retorna apenas eventos suspeitos |

## 3. Execução

```bash
docker compose build
docker compose run --rm api pytest -v
docker compose up -d
curl -s http://localhost:8001/health
curl -s -X POST http://localhost:8001/events/analyze \
  -H "Content-Type: application/json" \
  -d '{"log_line": "Failed password for root from 203.0.113.9 port 51321 ssh2"}'
```

## 4. Critério de saída (Definition of Done)

- 100% dos casos T01–T09 passando.
- `docker compose up` sobe sem erro e `/health` responde 200.
- Chamada manual via `curl` a `/events/analyze` retorna classificação e ação coerentes
  para um log de ataque conhecido.
