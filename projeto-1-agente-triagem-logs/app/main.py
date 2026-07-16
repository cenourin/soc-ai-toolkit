from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from app import db
from app.config import settings
from app.models import (
    AnalyzeBatchRequest,
    AnalyzeRequest,
    Classification,
    EventResponse,
    StatsResponse,
)
from app.services import TriageService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="Agente de IA para Triagem de Logs de Seguranca",
    description=(
        "Classifica eventos de log de seguranca (SUSPEITO/NORMAL/CRITICO), gera um "
        "resumo em linguagem natural e sugere uma acao. Usa Claude quando "
        "ANTHROPIC_API_KEY esta configurada; caso contrario, usa um classificador "
        "heuristico local."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

triage_service = TriageService()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "llm_enabled": settings.llm_enabled}


@app.post("/events/analyze", response_model=EventResponse)
def analyze(request: AnalyzeRequest) -> dict:
    return triage_service.analyze(request.log_line)


@app.post("/events/analyze-batch", response_model=list[EventResponse])
def analyze_batch(request: AnalyzeBatchRequest) -> list[dict]:
    return triage_service.analyze_batch(request.log_lines)


@app.get("/events", response_model=list[EventResponse])
def list_events(classification: Classification | None = Query(default=None)) -> list[dict]:
    return db.list_events(classification=classification)


@app.get("/events/stats", response_model=StatsResponse)
def event_stats() -> dict:
    return db.stats()


@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int) -> dict:
    event = db.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento nao encontrado")
    return event
