MALICIOUS_IP = "203.0.113.9"
BENIGN_IP = "8.8.8.8"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_lookup_malicious_indicator_triggers_notification(client):
    response = client.post("/lookup", json={"indicator": MALICIOUS_IP})
    assert response.status_code == 200
    body = response.json()
    assert body["lookup"]["malicious"] is True
    assert body["notification"] is not None
    assert body["notification"]["channel"] == "console"

    notifications = client.get("/notifications").json()
    assert any(n["indicator"] == MALICIOUS_IP for n in notifications)


def test_lookup_benign_indicator_no_notification(client):
    response = client.post("/lookup", json={"indicator": BENIGN_IP})
    assert response.status_code == 200
    body = response.json()
    assert body["lookup"]["malicious"] is False
    assert body["notification"] is None


def test_lookup_rejects_invalid_indicator(client):
    response = client.post("/lookup", json={"indicator": "nao-e-indicador-valido"})
    assert response.status_code == 422


def test_playbook_run_queue(client):
    response = client.post("/playbook/run-queue")
    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 5
    assert body["malicious"] == 4
    assert body["notifications_sent"] == 4


def test_lookups_history_endpoint(client):
    client.post("/lookup", json={"indicator": MALICIOUS_IP})
    response = client.get("/lookups")
    assert response.status_code == 200
    body = response.json()
    assert any(item["indicator"] == MALICIOUS_IP for item in body)


def test_get_lookup_not_found(client):
    response = client.get("/lookups/999999")
    assert response.status_code == 404
