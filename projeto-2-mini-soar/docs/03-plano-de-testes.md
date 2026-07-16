# Plano de Testes — Mini SOAR de Integração de Ferramentas

## 1. Estratégia

Testes automatizados com `pytest`, executados dentro do container
(`docker compose run --rm api pytest -v`). Nenhum teste depende de rede externa: o
`ThreatIntelClient` e o `Notifier` são exercitados em modo mock (sem
`ABUSEIPDB_API_KEY`/`VIRUSTOTAL_API_KEY`/webhooks configurados), garantindo
determinismo.

## 2. Casos de teste

| ID | Caso | Tipo | Resultado esperado |
|----|------|------|---------------------|
| T01 | `test_detect_ipv4` | Unitário | `"203.0.113.9"` detectado como tipo `ip` |
| T02 | `test_detect_hash_md5` | Unitário | hash de 32 hex chars detectado como tipo `hash` |
| T03 | `test_detect_invalid_indicator` | Unitário | string inválida levanta erro de validação |
| T04 | `test_mock_reputation_known_malicious_ip` | Unitário | IP presente em `mock_reputation.json` como malicioso retorna `malicious=True`, `source="mock"` |
| T05 | `test_mock_reputation_unknown_indicator` | Unitário | Indicador ausente da base mock retorna `malicious=False`, `score=0` |
| T06 | `test_console_notifier_records_message` | Unitário | Sem webhook configurado, `Notifier` registra `channel="console"`, `delivered=False` |
| T07 | `test_health_endpoint` | Integração (API) | `GET /health` retorna 200 |
| T08 | `test_lookup_malicious_indicator_triggers_notification` | Integração (API) | `POST /lookup` com IP malicioso mock retorna `malicious=true` e cria registro em `GET /notifications` |
| T09 | `test_lookup_benign_indicator_no_notification` | Integração (API) | `POST /lookup` com IP benigno não gera notificação |
| T10 | `test_lookup_rejects_invalid_indicator` | Integração (API) | `POST /lookup` com indicador inválido retorna 422 |
| T11 | `test_playbook_run_queue` | Integração (API) | `POST /playbook/run-queue` processa todos os indicadores de `data/indicators_queue.json` e retorna contadores coerentes |
| T12 | `test_lookups_history_endpoint` | Integração (API) | `GET /lookups` reflete as consultas realizadas |

## 3. Execução

```bash
docker compose build
docker compose run --rm api pytest -v
docker compose up -d
curl -s http://localhost:8002/health
curl -s -X POST http://localhost:8002/lookup \
  -H "Content-Type: application/json" -d '{"indicator": "203.0.113.9"}'
curl -s -X POST http://localhost:8002/playbook/run-queue
docker compose logs worker --tail 20
```

## 4. Critério de saída (Definition of Done)

- 100% dos casos T01–T12 passando.
- `docker compose up` sobe `api` e `worker` sem erro; `/health` responde 200.
- `worker` produz ao menos uma execução do playbook nos logs dentro do intervalo
  configurado (`PLAYBOOK_INTERVAL_SECONDS`).
- Indicador malicioso conhecido (base mock) gera notificação visível em
  `GET /notifications`.
