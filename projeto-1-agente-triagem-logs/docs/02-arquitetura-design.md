# Arquitetura e Design — Agente de IA para Triagem de Logs

## 1. Visão geral

```
                         ┌──────────────────────────┐
  POST /events/analyze   │                          │
  POST /events/analyze-  │        FastAPI app       │
        batch            │      (app/main.py)       │
  GET  /events           │                          │
  GET  /events/{id}      └────────────┬─────────────┘
  GET  /events/stats                  │
  GET  /health                        ▼
                          ┌──────────────────────────┐
                          │   TriageService           │
                          │  (app/services.py)        │
                          └───────┬──────────┬────────┘
                                  │          │
                     engine=llm  │          │ engine=heuristic
                                  ▼          ▼
                     ┌────────────────┐  ┌─────────────────────┐
                     │ LLMClient       │  │ HeuristicClassifier │
                     │ (Anthropic API) │  │ (regras locais)     │
                     └────────────────┘  └─────────────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │  Repository (SQLite)      │
                     │  app/db.py                │
                     └──────────────────────────┘
```

O CLI (`app/cli.py`) reutiliza o mesmo `TriageService`, garantindo que a lógica de
classificação seja única independentemente do canal de entrada (API ou linha de comando).

## 2. Módulos

| Módulo | Responsabilidade |
|--------|-------------------|
| `app/main.py` | Definição da API FastAPI, rotas e serialização HTTP. |
| `app/services.py` | `TriageService`: orquestra escolha de engine, chama classificador e persiste resultado. |
| `app/llm_client.py` | Cliente do LLM (Anthropic Claude). Constrói o prompt, chama a API, faz parsing da resposta estruturada (JSON). |
| `app/heuristics.py` | Classificador baseado em regras/regex para os padrões mais comuns de logs de segurança (fallback sem custo e sem dependência externa). |
| `app/db.py` | Acesso a dados via SQLite (stdlib `sqlite3`), criação de schema e CRUD de eventos. |
| `app/models.py` | Modelos Pydantic (schemas de request/response) e dataclasses internas. |
| `app/cli.py` | Interface de linha de comando para processar arquivos de log em lote. |
| `app/config.py` | Leitura de variáveis de ambiente (`ANTHROPIC_API_KEY`, `DB_PATH`, etc.). |

## 3. Decisão de arquitetura: motor duplo (LLM + heurístico)

**Contexto:** a vaga pede uso de LLMs para apoiar triagem, mas o projeto precisa "ficar
rodando e testável" sem exigir que quem avalie o portfólio configure uma chave de API paga.

**Decisão:** `TriageService` seleciona o engine em tempo de execução:
- Se `ANTHROPIC_API_KEY` estiver presente no ambiente → usa `LLMClient` (chamada real à
  API do Claude, modelo configurável via `ANTHROPIC_MODEL`, default `claude-sonnet-5`).
- Caso contrário → usa `HeuristicClassifier`, que aplica regras de regex conhecidas
  (ex.: `Failed password`, `Invalid user`, múltiplas tentativas do mesmo IP, portas
  sensíveis) para chegar a uma classificação, resumo e ação equivalentes em formato.

Ambos os engines implementam a mesma interface (`classify(log_line: str) -> Classification`),
então a troca é transparente para quem consome a API — o campo `engine` na resposta indica
qual foi usado.

**Consequência:** o sistema é 100% demonstrável offline/sem custo, e passa a usar IA real
assim que uma chave for adicionada ao `.env`, sem mudança de código.

## 4. Modelo de dados (SQLite)

Tabela `events`:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER PK | Identificador autoincremental |
| `log_line` | TEXT | Linha de log original |
| `classification` | TEXT | `SUSPEITO` / `NORMAL` / `CRITICO` |
| `summary` | TEXT | Resumo em linguagem natural |
| `suggested_action` | TEXT | `bloquear_ip` / `investigar_usuario` / `ignorar` / `escalar` |
| `engine` | TEXT | `llm` ou `heuristic` |
| `created_at` | TEXT (ISO 8601) | Timestamp de processamento |

## 5. Contrato da API (resumo)

`POST /events/analyze`
```json
// request
{ "log_line": "Failed password for root from 203.0.113.9 port 51321 ssh2" }

// response 200
{
  "id": 1,
  "classification": "SUSPEITO",
  "summary": "Tentativa de login falhou para o usuário 'root' a partir do IP 203.0.113.9.",
  "suggested_action": "bloquear_ip",
  "engine": "heuristic",
  "created_at": "2026-07-15T12:00:00"
}
```

`GET /events?classification=SUSPEITO` → lista de eventos no mesmo formato.

`GET /events/stats` → `{"SUSPEITO": 3, "NORMAL": 10, "CRITICO": 1}`

## 6. Tratamento de erros

- Falha na chamada ao LLM (timeout, rate limit, resposta malformada) → captura de
  exceção em `LLMClient` e *fallback automático* para `HeuristicClassifier` naquela
  requisição específica, registrando `engine = "heuristic_fallback"`. Isso atende ao
  RNF05 (nunca retornar 500 ao usuário por indisponibilidade do provedor).
- Linha de log vazia → `422 Unprocessable Entity` (validação Pydantic).

## 7. Empacotamento e execução

- Imagem baseada em `python:3.12-slim`.
- Dependências mínimas: `fastapi`, `uvicorn`, `pydantic`, `anthropic`, `pytest`,
  `httpx` (cliente de teste).
- `docker-compose.yml` expõe a porta `8001` e monta `./data` como volume (dados de
  exemplo) e um volume nomeado para persistir o SQLite entre reinícios.
