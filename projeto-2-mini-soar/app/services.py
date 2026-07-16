from app import db
from app.notifier import Notifier, format_alert_message
from app.threat_intel_client import ThreatIntelClient


class SoarService:
    """Orquestra o playbook de um unico indicador (UC01): consulta reputacao,
    persiste, e dispara notificacao quando malicioso. Reutilizado tanto pela rota
    POST /lookup quanto pelo processamento em lote (app/queue_runner.py)."""

    def __init__(self) -> None:
        self._threat_intel = ThreatIntelClient()
        self._notifier = Notifier()

    def lookup(self, indicator: str) -> tuple[dict, dict | None]:
        result = self._threat_intel.lookup(indicator)
        lookup_record = db.insert_lookup(
            indicator=result.indicator,
            indicator_type=result.indicator_type,
            malicious=result.malicious,
            score=result.score,
            source=result.source,
            categories=result.categories,
        )

        notification_record = None
        if result.malicious:
            message = format_alert_message(result)
            channel, delivered = self._notifier.notify(message)
            notification_record = db.insert_notification(
                lookup_id=lookup_record["id"],
                indicator=result.indicator,
                channel=channel,
                message=message,
                delivered=delivered,
            )

        return lookup_record, notification_record
