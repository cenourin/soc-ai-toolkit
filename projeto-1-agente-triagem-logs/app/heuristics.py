import re

from app.models import ClassificationResult

_IP_RE = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
_USER_RE = re.compile(r"for invalid user\s+([A-Za-z0-9_\-\.]+)|for user\s+([A-Za-z0-9_\-\.]+)|for\s+([A-Za-z0-9_\-\.]+)")

_FAILED_LOGIN_RE = re.compile(r"failed password|authentication failure|invalid user", re.I)
_ACCEPTED_LOGIN_RE = re.compile(r"accepted password|accepted publickey|session opened", re.I)
_PORT_SCAN_RE = re.compile(r"port ?scan|multiple ports|nmap|SYN flood", re.I)
_MALWARE_RE = re.compile(r"malware|ransomware|trojan|exploit detected|reverse shell", re.I)
_FIREWALL_BLOCK_RE = re.compile(r"\bDROP\b|\bDENY\b|\bBLOCK(ED)?\b", re.I)


def _extract_ip(log_line: str) -> str | None:
    match = _IP_RE.search(log_line)
    return match.group(1) if match else None


def _extract_user(log_line: str) -> str | None:
    match = _USER_RE.search(log_line)
    if not match:
        return None
    return next((g for g in match.groups() if g), None)


class HeuristicClassifier:
    """Classificador baseado em regras, usado quando nenhuma API de LLM está configurada.

    Cobre os padrões mais comuns de logs de SSH/firewall citados na vaga (força bruta,
    port scan, malware, tráfego bloqueado) para permitir uma demonstração completa e
    determinística do fluxo de triagem sem depender de um provedor externo.
    """

    name = "heuristic"

    def classify(self, log_line: str) -> ClassificationResult:
        ip = _extract_ip(log_line)
        user = _extract_user(log_line)

        if _MALWARE_RE.search(log_line):
            return ClassificationResult(
                classification="CRITICO",
                summary=f"Indício de malware/exploração detectado no evento{f' (host {ip})' if ip else ''}.",
                suggested_action="escalar",
                engine="heuristic",
            )

        if _FAILED_LOGIN_RE.search(log_line):
            alvo = f" para o usuário '{user}'" if user else ""
            origem = f" a partir do IP {ip}" if ip else ""
            return ClassificationResult(
                classification="SUSPEITO",
                summary=f"Tentativa de autenticação falhou{alvo}{origem}.",
                suggested_action="bloquear_ip" if ip else "investigar_usuario",
                engine="heuristic",
            )

        if _PORT_SCAN_RE.search(log_line):
            origem = f" originado em {ip}" if ip else ""
            return ClassificationResult(
                classification="SUSPEITO",
                summary=f"Padrão de varredura de portas (port scan) detectado{origem}.",
                suggested_action="bloquear_ip" if ip else "investigar_usuario",
                engine="heuristic",
            )

        if _FIREWALL_BLOCK_RE.search(log_line):
            origem = f" vindo de {ip}" if ip else ""
            return ClassificationResult(
                classification="SUSPEITO",
                summary=f"Firewall bloqueou tráfego{origem}; possível tentativa de acesso indevido.",
                suggested_action="investigar_usuario",
                engine="heuristic",
            )

        if _ACCEPTED_LOGIN_RE.search(log_line):
            alvo = f" do usuário '{user}'" if user else ""
            return ClassificationResult(
                classification="NORMAL",
                summary=f"Login bem-sucedido{alvo}, sem indícios de comportamento anômalo.",
                suggested_action="ignorar",
                engine="heuristic",
            )

        return ClassificationResult(
            classification="NORMAL",
            summary="Evento sem padrões conhecidos de risco; tratado como atividade normal.",
            suggested_action="ignorar",
            engine="heuristic",
        )
