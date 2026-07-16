import logging

import httpx

from app.config import settings
from app.models import ReputationResult

logger = logging.getLogger(__name__)


def format_alert_message(result: ReputationResult) -> str:
    categorias = ", ".join(result.categories) if result.categories else "sem categoria"
    return (
        f"🚨 Indicador malicioso detectado: {result.indicator} "
        f"(tipo: {result.indicator_type}, score: {result.score}, fonte: {result.source}, "
        f"categorias: {categorias})"
    )


class Notifier:
    """Envia o alerta para Slack ou Discord (o que estiver configurado, Slack tem
    prioridade). Se nenhum webhook estiver configurado, ou se o envio falhar, o alerta
    e apenas registrado (modo console) e o fluxo principal segue normalmente."""

    def notify(self, message: str) -> tuple[str, bool]:
        if settings.slack_webhook_url:
            delivered = self._post_webhook(settings.slack_webhook_url, {"text": message})
            if delivered:
                return "slack", True
        if settings.discord_webhook_url:
            delivered = self._post_webhook(settings.discord_webhook_url, {"content": message})
            if delivered:
                return "discord", True

        logger.info("[console-notifier] %s", message)
        return "console", False

    @staticmethod
    def _post_webhook(url: str, payload: dict) -> bool:
        try:
            response = httpx.post(url, json=payload, timeout=5.0)
            response.raise_for_status()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao enviar webhook, registrando em modo console: %s", exc)
            return False
