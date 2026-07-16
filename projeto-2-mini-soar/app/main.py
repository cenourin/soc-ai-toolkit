from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app import db
from app.config import settings
from app.indicator import detect_indicator_type
from app.models import (
    LookupRequest,
    LookupResponse,
    LookupWithNotification,
    NotificationResponse,
    PlaybookRunResponse,
)
from app.models import InvalidIndicatorError
from app.queue_runner import run_queue
from app.services import SoarService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="Mini SOAR — Integracao de Ferramentas de Threat Intelligence",
    description=(
        "Recebe um IP ou hash suspeito, consulta reputacao (AbuseIPDB/VirusTotal, com "
        "fallback mock) e envia um alerta formatado para Slack/Discord (ou registra "
        "localmente em modo mock)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

soar_service = SoarService()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "threat_intel_real_enabled": bool(
            settings.abuseipdb_api_key or settings.virustotal_api_key
        ),
        "webhook_enabled": settings.webhook_enabled,
    }


@app.post("/lookup", response_model=LookupWithNotification)
def lookup(request: LookupRequest) -> dict:
    try:
        detect_indicator_type(request.indicator)
    except InvalidIndicatorError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    lookup_record, notification_record = soar_service.lookup(request.indicator)
    return {"lookup": lookup_record, "notification": notification_record}


@app.get("/lookups", response_model=list[LookupResponse])
def list_lookups(malicious: bool | None = None) -> list[dict]:
    return db.list_lookups(malicious=malicious)


@app.get("/lookups/{lookup_id}", response_model=LookupResponse)
def get_lookup(lookup_id: int) -> dict:
    record = db.get_lookup(lookup_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Consulta nao encontrada")
    return record


@app.get("/notifications", response_model=list[NotificationResponse])
def list_notifications() -> list[dict]:
    return db.list_notifications()


@app.post("/playbook/run-queue", response_model=PlaybookRunResponse)
def playbook_run_queue() -> dict:
    return run_queue(soar_service)
