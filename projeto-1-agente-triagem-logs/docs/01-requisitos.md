# Documento de Requisitos — Agente de IA para Triagem de Logs de Segurança

## 1. Objetivo

Construir um agente que recebe logs brutos (firewall, SSH, autenticação) e utiliza um
LLM (com fallback heurístico local) para classificar cada evento, resumir em linguagem
natural o que aconteceu e sugerir uma ação de resposta, apoiando analistas de um SOC na
triagem inicial de alertas.

Projeto de portfólio pessoal, desenvolvido para explorar aplicação prática de IA em
operações de segurança (SOC).

## 2. Escopo

Dentro do escopo:
- Ingestão de logs em texto (arquivo ou requisição HTTP), um evento por linha.
- Classificação de cada evento em `SUSPEITO`, `NORMAL` ou `CRITICO`.
- Geração de um resumo em linguagem natural do evento.
- Sugestão de uma ação (`bloquear_ip`, `investigar_usuario`, `ignorar`, `escalar`).
- Persistência dos eventos processados e consulta posterior via API.
- Execução em modo real (LLM via API Anthropic) ou em modo mock (heurística local),
  selecionado automaticamente pela presença de credenciais.

Fora do escopo:
- Coleta de logs em produção (agentes de coleta, Syslog, Filebeat etc.).
- Bloqueio automático de IPs em firewall real (a ação é apenas *sugerida*, não executada).
- Interface gráfica além da documentação automática da API (Swagger/OpenAPI).

## 3. Atores

- **Analista de SOC**: consome os alertas triados via API para priorizar investigação.
- **Sistema de ingestão** (simulado): arquivo de log ou chamada HTTP que alimenta o agente.
- **Provedor de LLM** (Anthropic Claude): opcional, usado quando `ANTHROPIC_API_KEY` está
  configurada.

## 4. Requisitos Funcionais

| ID    | Descrição | Prioridade |
|-------|-----------|------------|
| RF01  | O sistema deve receber uma linha de log via `POST /events/analyze` e retornar classificação, resumo e ação sugerida. | Alta |
| RF02  | O sistema deve processar um lote de logs via `POST /events/analyze-batch`. | Alta |
| RF03  | O sistema deve processar um arquivo de log completo via CLI (`python -m app.cli --file <path>`). | Alta |
| RF04  | O sistema deve persistir cada evento processado (log original, classificação, resumo, ação, timestamp) em banco SQLite. | Alta |
| RF05  | O sistema deve expor `GET /events` para listar eventos processados, com filtro opcional por classificação (`?classification=SUSPEITO`). | Média |
| RF06  | O sistema deve expor `GET /events/{id}` para detalhar um evento específico. | Média |
| RF07  | O sistema deve expor `GET /health` para checagem de disponibilidade (liveness/readiness). | Alta |
| RF08  | Quando `ANTHROPIC_API_KEY` não estiver configurada, o sistema deve usar um classificador heurístico local (regras baseadas em padrões conhecidos de logs de firewall/SSH) sem falhar. | Alta |
| RF09  | Quando `ANTHROPIC_API_KEY` estiver configurada, o sistema deve usar o modelo Claude para classificar e resumir o evento. | Média |
| RF10  | O sistema deve disponibilizar dados de exemplo (`data/sample_logs.log`) prontos para demonstração. | Baixa |
| RF11  | O sistema deve expor `GET /events/stats` com contagem de eventos por classificação. | Baixa |

## 5. Requisitos Não Funcionais

| ID    | Descrição |
|-------|-----------|
| RNF01 | O serviço deve subir integralmente via `docker compose up` sem configuração manual adicional. |
| RNF02 | O serviço deve responder a `GET /health` em menos de 200ms em ambiente local. |
| RNF03 | O código deve ter cobertura de testes automatizados para o classificador heurístico e para os principais endpoints da API. |
| RNF04 | Nenhuma credencial deve ser versionada em texto puro; configuração via variáveis de ambiente (`.env`, não commitado — apenas `.env.example`). |
| RNF05 | O sistema deve degradar de forma previsível (modo heurístico) caso o provedor de LLM esteja indisponível ou sem chave configurada, nunca retornar erro 500 ao usuário final por esse motivo. |
| RNF06 | Logs da aplicação devem ser legíveis via `docker compose logs`. |

## 6. Casos de Uso

### UC01 — Analisar evento único
1. Cliente envia `POST /events/analyze` com `{"log_line": "..."}`.
2. Sistema seleciona motor de classificação (LLM ou heurístico).
3. Sistema classifica, resume e sugere ação.
4. Sistema persiste o resultado.
5. Sistema retorna JSON com `classification`, `summary`, `suggested_action`, `engine`.

### UC02 — Processar arquivo de logs em lote (CLI)
1. Operador executa `python -m app.cli --file data/sample_logs.log`.
2. Sistema lê cada linha, aplica UC01 internamente.
3. Sistema imprime um resumo tabular no terminal e persiste os resultados.

### UC03 — Consultar histórico de eventos
1. Analista chama `GET /events?classification=SUSPEITO`.
2. Sistema retorna lista de eventos filtrados, mais recentes primeiro.

## 7. Critérios de Aceite

- `docker compose up --build` inicia a API na porta `8001` sem erros.
- `curl http://localhost:8001/health` retorna `200 OK`.
- Enviar um log de força bruta SSH conhecido retorna `classification = "SUSPEITO"` ou
  `"CRITICO"` e uma ação sugerida diferente de vazio, tanto em modo heurístico quanto em
  modo LLM.
- `pytest` roda com sucesso dentro do container (`docker compose run --rm api pytest`).
