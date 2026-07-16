import os
import tempfile

import pytest

# Sobrescreve (nao apenas setdefault) para garantir que os testes nunca gravem no
# mesmo banco/volume usado pelo servico "api" quando rodado via docker-compose.
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test_soar.db")
os.environ.setdefault("QUEUE_PATH", "data/indicators_queue.json")
os.environ.setdefault("MOCK_REPUTATION_PATH", "data/mock_reputation.json")
for _key in ("ABUSEIPDB_API_KEY", "VIRUSTOTAL_API_KEY", "SLACK_WEBHOOK_URL", "DISCORD_WEBHOOK_URL"):
    os.environ.pop(_key, None)  # testes sempre usam engines mock, sem rede externa

from app import db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    db.init_db()
    with db.get_connection() as conn:
        conn.execute("DELETE FROM lookups")
        conn.execute("DELETE FROM notifications")
        conn.commit()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    return TestClient(app)
