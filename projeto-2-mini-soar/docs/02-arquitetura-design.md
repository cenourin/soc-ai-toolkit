# Arquitetura e Design — Mini SOAR de Integração de Ferramentas

## 1. Visão geral

```
 ┌───────────────┐   POST /playbook/run-queue (a cada N s)   ┌──────────────────────┐
 │  worker         │ ─────────────────────────────────────▶ │      FastAPI app       │
 │ (loop agendado) │                                          │     (app/main.py)     │
 └───────────────┘                                          └──────────┬─────────────┘
                                                                          │
 Analista ─── POST /lookup {indicator} ─────────────────────────────────┘
                                                                          │
                                                                          ▼
                                                          ┌──────────────────────────┐
                                                          │   SoarService             │
                                                          │   (app/services.py)       │
                                                          └───┬──────────────┬────────┘
                                                              │              │
                                            ThreatIntelClient │              │ Notifier
                                                              ▼              ▼
                                      ┌──────────────────────────┐  ┌─────────────────────┐
                                      │ AbuseIPDB / VirusTotal    │  │ Slack / Discord      │
                                      │ (real, com fallback mock) │  │ webhook (ou mock)    │
                                      └──────────────────────────┘  └─────────────────────┘
                                                              │
                                                              ▼
                                                 ┌──────────────────────────┐
                                                 │  Repository (SQLite)      │
                                                 │  lookups + notifications  │
                                                 └──────────────────────────┘
```

## 2. Módulos

| Módulo | Responsabilidade |
|--------|-------------------|
| `app/main.py` | API FastAPI: rotas de lookup, consulta de histórico e execução do playbook. |
| `app/services.py` | `SoarService`: orquestra detecção de tipo, consulta de reputação, notificação e persistência (playbook de um único indicador — UC01). |
| `app/indicator.py` | Detecção e validação do tipo de indicador (`ip` ou `hash`). |
| `app/threat_intel_client.py` | `ThreatIntelClient`: consulta AbuseIPDB (IP) ou VirusTotal (hash); fallback para `MockReputationSource` em caso de ausência de chave ou falha da API. |
| `app/notifier.py` | `Notifier`: envia alerta para Slack ou Discord via webhook; fallback para `ConsoleNotifier` (registra localmente) quando nenhum webhook está configurado ou o envio falha. |
| `app/db.py` | Acesso a dados via SQLite: tabelas `lookups` e `notifications`. |
| `app/models.py` | Schemas Pydantic e dataclasses internas. |
| `app/queue_runner.py` | Leitura de `data/indicators_queue.json` e execução em lote (UC02), reutilizado pela rota `/playbook/run-queue` e pelo `worker`. |
| `app/config.py` | Leitura de variáveis de ambiente. |
| `worker/loop.py` | Processo de longa duração que chama a API em intervalo fixo, simulando um agendamento cron (UC03), rodando em um **container separado**. |

## 3. Decisões de arquitetura

### 3.1 Motor duplo para threat intel (real + mock) — mesma decisão do Projeto 1

**Contexto:** a vaga cita "consultar automaticamente a reputação na API de threat
intel", mas o projeto precisa ficar demonstrável sem exigir chaves pagas de terceiros.

**Decisão:** `ThreatIntelClient` tenta a API real (AbuseIPDB para IP, VirusTotal para
hash) somente se a respectiva chave estiver definida; qualquer ausência de chave ou
exceção na chamada HTTP aciona `MockReputationSource`, que consulta uma base local
(`data/mock_reputation.json`) contendo indicadores de exemplo conhecidos (incluindo o
hash de teste EICAR, um indicador padrão da indústria para simular malware sem risco
real). O campo `source` na resposta indica qual foi usado (`abuseipdb`, `virustotal`,
`mock`).

### 3.2 Motor duplo para notificação (webhook real + console/mock)

**Decisão:** `Notifier` publica no `SLACK_WEBHOOK_URL` ou `DISCORD_WEBHOOK_URL`
configurado (o que estiver presente; Slack tem prioridade se ambos estiverem). Se
nenhum estiver configurado, ou se o POST falhar, o alerta é registrado na tabela
`notifications` com `channel="console"` e `delivered=false`, sem interromper o fluxo
(RNF03). Isso permite validar toda a lógica de formatação e disparo de alerta via
`GET /notifications`, mesmo sem um workspace de Slack/Discord real.

### 3.3 Worker como container separado em vez de `cron` dentro da imagem da API

**Contexto:** o projeto sugerido na vaga menciona "Linux para rodar como script
agendado (cron)".

**Decisão:** em vez de instalar `cron` dentro do container da API (o que mistura
responsabilidades e dificulta observar logs/escalar independentemente), o agendamento é
um segundo serviço Docker (`worker`) com um loop Python simples
(`while True: run(); sleep(N)`), que chama a API via HTTP. Isso é funcionalmente
equivalente a um cron job, mas mais simples de operar em Docker Compose (`docker
compose logs worker` mostra cada execução) e mais fácil de testar isoladamente.

## 4. Modelo de dados (SQLite)

Tabela `lookups`:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER PK | Identificador autoincremental |
| `indicator` | TEXT | IP ou hash consultado |
| `indicator_type` | TEXT | `ip` ou `hash` |
| `malicious` | INTEGER (bool) | Resultado da consulta |
| `score` | INTEGER | Score de confiança/abuso (0–100) |
| `source` | TEXT | `abuseipdb` / `virustotal` / `mock` |
| `categories` | TEXT (JSON) | Categorias de ameaça retornadas |
| `created_at` | TEXT (ISO 8601) | Timestamp da consulta |

Tabela `notifications`:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER PK | Identificador autoincremental |
| `lookup_id` | INTEGER FK | Referência à consulta que originou o alerta |
| `indicator` | TEXT | Indicador associado |
| `channel` | TEXT | `slack` / `discord` / `console` |
| `message` | TEXT | Corpo do alerta enviado |
| `delivered` | INTEGER (bool) | Se o webhook respondeu com sucesso |
| `created_at` | TEXT (ISO 8601) | Timestamp do envio |

## 5. Contrato da API (resumo)

`POST /lookup`
```json
// request
{ "indicator": "203.0.113.9" }

// response 200
{
  "lookup": {
    "id": 1, "indicator": "203.0.113.9", "indicator_type": "ip",
    "malicious": true, "score": 97, "source": "mock",
    "categories": ["ssh-bruteforce", "scanning"], "created_at": "2026-07-15T12:00:00"
  },
  "notification": {
    "id": 1, "channel": "console", "delivered": false,
    "message": "🚨 Indicador malicioso detectado: 203.0.113.9 (score 97, ssh-bruteforce, scanning)"
  }
}
```

`POST /playbook/run-queue` → `{"processed": 4, "malicious": 2, "notifications_sent": 2}`

## 6. Empacotamento e execução

- Imagem base `python:3.12-slim`, compartilhada entre API e worker (mesmo
  `requirements.txt`, `CMD` diferente).
- `docker-compose.yml` define dois serviços: `api` (porta `8002`) e `worker`
  (sem porta exposta, comunica-se com `api` pela rede interna do Compose via
  `http://api:8002`).
- Volume nomeado para persistir o SQLite; `./data` montado somente leitura para os
  arquivos de exemplo (`indicators_queue.json`, `mock_reputation.json`).
