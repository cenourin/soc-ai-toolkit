# Documento de Requisitos — Mini SOAR de Integração de Ferramentas

## 1. Objetivo

Construir uma automação que recebe um indicador suspeito (IP ou hash de arquivo),
consulta automaticamente sua reputação em uma fonte de threat intelligence (AbuseIPDB
para IPs, VirusTotal para hashes — com fallback local mockado) e envia um alerta
formatado para um canal de notificação (Slack ou Discord via webhook), reproduzindo em
pequena escala um playbook de SOAR (Security Orchestration, Automation and Response).

Projeto de portfólio pessoal, desenvolvido para explorar automação de resposta a
incidentes de segurança.

## 2. Escopo

Dentro do escopo:
- Consulta de reputação sob demanda via API (`POST /lookup`).
- Detecção automática do tipo de indicador (IPv4 ou hash MD5/SHA1/SHA256).
- Envio de alerta formatado para Slack/Discord quando o indicador for malicioso.
- Execução de um "playbook" em lote a partir de uma fila de indicadores
  (`data/indicators_queue.json`), disparável sob demanda ou em intervalo fixo por um
  serviço worker dedicado (simulando um agendamento tipo cron).
- Histórico consultável de consultas e de notificações enviadas.
- Modo real (chaves de API configuradas) ou modo mock (sem chaves, usando uma base
  local de reputação para demonstração determinística).

Fora do escopo:
- Bloqueio automático do indicador em firewall/proxy real.
- Autenticação/autorização de usuários da API (fora do escopo de um protótipo de
  portfólio).
- Suporte a outros tipos de indicador (domínio, URL) — apenas IP e hash de arquivo.

## 3. Atores

- **Analista de SOC**: envia indicadores suspeitos para verificação e recebe alertas.
- **Fonte de Threat Intelligence** (AbuseIPDB / VirusTotal): serviço externo consultado.
- **Canal de notificação** (Slack ou Discord via webhook): destino dos alertas.
- **Worker agendado**: processa a fila de indicadores pendentes periodicamente.

## 4. Requisitos Funcionais

| ID    | Descrição | Prioridade |
|-------|-----------|------------|
| RF01  | O sistema deve receber um indicador (IP ou hash) via `POST /lookup` e retornar sua reputação (malicioso ou não, score, fonte). | Alta |
| RF02  | O sistema deve detectar automaticamente se o indicador é um IPv4 ou um hash (MD5/SHA1/SHA256) e escolher a fonte de consulta adequada. | Alta |
| RF03  | Quando o indicador for classificado como malicioso, o sistema deve enviar um alerta formatado para o webhook configurado (Slack ou Discord). | Alta |
| RF04  | O sistema deve persistir todas as consultas realizadas (`GET /lookups`, `GET /lookups/{id}`). | Alta |
| RF05  | O sistema deve persistir todas as notificações emitidas, incluindo se foram efetivamente entregues ou apenas registradas em modo mock (`GET /notifications`). | Média |
| RF06  | O sistema deve processar uma fila de indicadores pendentes a partir de `data/indicators_queue.json` via `POST /playbook/run-queue`. | Alta |
| RF07  | Um serviço worker deve reexecutar `POST /playbook/run-queue` automaticamente em um intervalo configurável, simulando um agendamento tipo cron. | Média |
| RF08  | Quando `ABUSEIPDB_API_KEY`/`VIRUSTOTAL_API_KEY` não estiverem configuradas, o sistema deve usar uma base local de reputação mockada (`data/mock_reputation.json`) sem falhar. | Alta |
| RF09  | Quando `SLACK_WEBHOOK_URL`/`DISCORD_WEBHOOK_URL` não estiverem configurados, o sistema deve registrar o alerta localmente (modo mock) em vez de falhar. | Alta |
| RF10  | O sistema deve expor `GET /health` para checagem de disponibilidade. | Alta |

## 5. Requisitos Não Funcionais

| ID    | Descrição |
|-------|-----------|
| RNF01 | O serviço deve subir integralmente via `docker compose up` sem configuração manual adicional (API + worker). |
| RNF02 | Falha ao consultar a fonte de threat intel real deve degradar automaticamente para o modo mock, nunca retornar erro 500 ao usuário por esse motivo. |
| RNF03 | Falha ao entregar o webhook não deve interromper o fluxo de consulta — a consulta e seu resultado devem ser sempre retornados e persistidos. |
| RNF04 | Nenhuma credencial deve ser versionada em texto puro; configuração via variáveis de ambiente (apenas `.env.example` é commitado). |
| RNF05 | O código deve ter cobertura de testes automatizados para detecção de tipo de indicador, cliente de threat intel (mockado) e notificador (mockado), sem dependência de rede real nos testes. |

## 6. Casos de Uso

### UC01 — Consultar reputação de um indicador
1. Analista envia `POST /lookup` com `{"indicator": "203.0.113.9"}`.
2. Sistema detecta o tipo (IP) e consulta a fonte adequada (real ou mock).
3. Sistema persiste o resultado da consulta.
4. Se malicioso, sistema formata e envia alerta ao canal configurado (ou registra em
   modo mock) e persiste a notificação.
5. Sistema retorna o resultado consolidado (reputação + status da notificação).

### UC02 — Executar playbook em lote
1. Operador (ou worker agendado) chama `POST /playbook/run-queue`.
2. Sistema lê `data/indicators_queue.json`.
3. Para cada indicador ainda não consultado, executa UC01 internamente.
4. Sistema retorna um resumo: total processado, quantos maliciosos, quantas
   notificações enviadas.

### UC03 — Automação periódica (worker)
1. Serviço `worker` aguarda `PLAYBOOK_INTERVAL_SECONDS` (default 60s).
2. Chama o endpoint `POST /playbook/run-queue` da API.
3. Registra no log o resumo da execução.
4. Repete indefinidamente enquanto o container estiver ativo.

## 7. Critérios de Aceite

- `docker compose up --build` inicia API (porta `8002`) e worker sem erros.
- `curl http://localhost:8002/health` retorna `200 OK`.
- `POST /lookup` com um IP presente na base mock maliciosa retorna `malicious: true` e
  gera uma entrada em `GET /notifications`.
- `POST /playbook/run-queue` processa todos os indicadores de `data/indicators_queue.json`
  e retorna um resumo consistente com `GET /lookups`.
- `pytest` roda com sucesso dentro do container, sem acessar rede externa.
