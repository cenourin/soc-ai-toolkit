from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

Classification = Literal["SUSPEITO", "NORMAL", "CRITICO"]
SuggestedAction = Literal["bloquear_ip", "investigar_usuario", "ignorar", "escalar"]
Engine = Literal["llm", "heuristic", "heuristic_fallback"]


@dataclass
class ClassificationResult:
    classification: Classification
    summary: str
    suggested_action: SuggestedAction
    engine: Engine


class AnalyzeRequest(BaseModel):
    log_line: str = Field(min_length=1, description="Linha de log bruta a ser analisada")


class AnalyzeBatchRequest(BaseModel):
    log_lines: list[str] = Field(min_length=1)


class EventResponse(BaseModel):
    id: int
    log_line: str
    classification: Classification
    summary: str
    suggested_action: SuggestedAction
    engine: Engine
    created_at: str


class StatsResponse(BaseModel):
    SUSPEITO: int = 0
    NORMAL: int = 0
    CRITICO: int = 0
