import os
import tempfile

import pytest

# Sobrescreve (nao apenas setdefault) para garantir que os testes nunca gravem no
# mesmo banco/volume usado pelo servico "api" quando rodado via docker-compose.
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test_events.db")
os.environ.pop("ANTHROPIC_API_KEY", None)  # testes sempre usam o engine heuristico

from app import db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    db.init_db()
    with db.get_connection() as conn:
        conn.execute("DELETE FROM events")
        conn.commit()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    return TestClient(app)
