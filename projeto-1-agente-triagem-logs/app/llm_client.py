import json
import logging

from app.config import settings
from app.models import ClassificationResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Voce e um analista de SOC (Security Operations Center) experiente. "
    "Analise a linha de log de seguranca fornecida e responda APENAS com um JSON "
    "no formato exato: "
    '{"classification": "SUSPEITO|NORMAL|CRITICO", "summary": "resumo curto em '
    'portugues do que aconteceu", "suggested_action": "bloquear_ip|investigar_usuario|'
    'ignorar|escalar"}. '
    "Nao inclua nenhum texto fora do JSON."
)


class LLMClassificationError(Exception):
    pass


class LLMClient:
    """Cliente para o modelo Claude (Anthropic). Ativado apenas quando ANTHROPIC_API_KEY
    esta configurada; ver app/services.py para a logica de fallback para o classificador
    heuristico em caso de falha ou ausencia de chave."""

    name = "llm"

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def classify(self, log_line: str) -> ClassificationResult:
        try:
            client = self._get_client()
            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=300,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": log_line}],
            )
            text = "".join(
                block.text for block in response.content if getattr(block, "type", "") == "text"
            )
            data = json.loads(text)
            return ClassificationResult(
                classification=data["classification"],
                summary=data["summary"],
                suggested_action=data["suggested_action"],
                engine="llm",
            )
        except Exception as exc:  # noqa: BLE001 - qualquer falha do provedor vira fallback
            logger.warning("Falha ao classificar via LLM, acionando fallback: %s", exc)
            raise LLMClassificationError(str(exc)) from exc
