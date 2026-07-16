import json
import logging
import os

from app import db
from app.config import settings
from app.services import SoarService

logger = logging.getLogger(__name__)


def load_queue(path: str | None = None) -> list[str]:
    queue_path = path or settings.queue_path
    if not os.path.exists(queue_path):
        return []
    with open(queue_path, encoding="utf-8") as handle:
        entries = json.load(handle)
    return [entry["indicator"] for entry in entries]


def run_queue(service: SoarService | None = None, path: str | None = None) -> dict:
    """Processa todos os indicadores da fila que ainda nao foram consultados.
    Reutilizado pela rota POST /playbook/run-queue e pelo worker agendado."""
    service = service or SoarService()
    indicators = load_queue(path)

    processed = 0
    malicious = 0
    notifications_sent = 0

    for indicator in indicators:
        if db.indicator_already_looked_up(indicator):
            continue
        lookup_record, notification_record = service.lookup(indicator)
        processed += 1
        if lookup_record["malicious"]:
            malicious += 1
        if notification_record is not None:
            notifications_sent += 1

    logger.info(
        "playbook run-queue: processed=%s malicious=%s notifications_sent=%s",
        processed,
        malicious,
        notifications_sent,
    )
    return {
        "processed": processed,
        "malicious": malicious,
        "notifications_sent": notifications_sent,
    }
