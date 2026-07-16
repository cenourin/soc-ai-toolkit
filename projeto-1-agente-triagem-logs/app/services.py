from app import db
from app.config import settings
from app.heuristics import HeuristicClassifier
from app.llm_client import LLMClassificationError, LLMClient
from app.models import ClassificationResult


class TriageService:
    """Orquestra a escolha de engine (LLM real ou heuristico) e a persistencia
    do resultado. E o unico ponto de entrada usado tanto pela API quanto pelo CLI."""

    def __init__(self) -> None:
        self._heuristic = HeuristicClassifier()
        self._llm = LLMClient() if settings.llm_enabled else None

    def analyze(self, log_line: str) -> dict:
        result = self._classify(log_line)
        return db.insert_event(
            log_line=log_line,
            classification=result.classification,
            summary=result.summary,
            suggested_action=result.suggested_action,
            engine=result.engine,
        )

    def analyze_batch(self, log_lines: list[str]) -> list[dict]:
        return [self.analyze(line) for line in log_lines if line.strip()]

    def _classify(self, log_line: str) -> ClassificationResult:
        if self._llm is not None:
            try:
                return self._llm.classify(log_line)
            except LLMClassificationError:
                result = self._heuristic.classify(log_line)
                result.engine = "heuristic_fallback"
                return result
        return self._heuristic.classify(log_line)
