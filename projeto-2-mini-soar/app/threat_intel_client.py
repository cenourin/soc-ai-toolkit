import json
import logging
import os

import httpx

from app.config import settings
from app.indicator import detect_indicator_type
from app.models import ReputationResult

logger = logging.getLogger(__name__)


class MockReputationSource:
    """Base local de reputacao usada quando nao ha chave de API configurada, ou quando
    a chamada real falha (timeout, rate limit, indisponibilidade). Garante que o fluxo
    de ponta a ponta seja sempre demonstravel offline e de forma deterministica."""

    def __init__(self, path: str | None = None) -> None:
        self._path = path or settings.mock_reputation_path
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, encoding="utf-8") as handle:
                self._data = json.load(handle)

    def lookup(self, indicator: str, indicator_type: str) -> ReputationResult:
        entry = self._data.get(indicator)
        if entry is None:
            return ReputationResult(
                indicator=indicator,
                indicator_type=indicator_type,
                malicious=False,
                score=0,
                source="mock",
                categories=[],
            )
        return ReputationResult(
            indicator=indicator,
            indicator_type=indicator_type,
            malicious=entry.get("malicious", False),
            score=entry.get("score", 0),
            source="mock",
            categories=entry.get("categories", []),
        )


class ThreatIntelClient:
    """Consulta reputacao de IPs via AbuseIPDB e de hashes via VirusTotal quando as
    respectivas chaves de API estao configuradas; cai para MockReputationSource em
    qualquer outro caso (sem chave ou falha da chamada real)."""

    def __init__(self) -> None:
        self._mock = MockReputationSource()

    def lookup(self, indicator: str) -> ReputationResult:
        indicator_type = detect_indicator_type(indicator)

        if indicator_type == "ip" and settings.abuseipdb_api_key:
            try:
                return self._lookup_abuseipdb(indicator)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falha ao consultar AbuseIPDB, usando mock: %s", exc)

        if indicator_type == "hash" and settings.virustotal_api_key:
            try:
                return self._lookup_virustotal(indicator)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falha ao consultar VirusTotal, usando mock: %s", exc)

        return self._mock.lookup(indicator, indicator_type)

    def _lookup_abuseipdb(self, ip: str) -> ReputationResult:
        response = httpx.get(
            "https://api.abuseipdb.com/api/v2/check",
            params={"ipAddress": ip, "maxAgeInDays": 90},
            headers={"Key": settings.abuseipdb_api_key, "Accept": "application/json"},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()["data"]
        score = int(data.get("abuseConfidenceScore", 0))
        return ReputationResult(
            indicator=ip,
            indicator_type="ip",
            malicious=score >= 50,
            score=score,
            source="abuseipdb",
            categories=["abuseipdb-report"] if score > 0 else [],
        )

    def _lookup_virustotal(self, file_hash: str) -> ReputationResult:
        response = httpx.get(
            f"https://www.virustotal.com/api/v3/files/{file_hash}",
            headers={"x-apikey": settings.virustotal_api_key},
            timeout=5.0,
        )
        response.raise_for_status()
        stats = response.json()["data"]["attributes"]["last_analysis_stats"]
        malicious_engines = int(stats.get("malicious", 0))
        total_engines = sum(stats.values()) or 1
        score = round((malicious_engines / total_engines) * 100)
        return ReputationResult(
            indicator=file_hash,
            indicator_type="hash",
            malicious=malicious_engines > 0,
            score=score,
            source="virustotal",
            categories=["malware"] if malicious_engines > 0 else [],
        )
