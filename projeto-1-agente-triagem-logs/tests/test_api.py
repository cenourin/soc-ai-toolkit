BRUTEFORCE_LOG = "Failed password for root from 203.0.113.9 port 51321 ssh2"
NORMAL_LOG = "Accepted password for deploy from 10.0.0.5 port 40210 ssh2"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint_persists_event(client):
    response = client.post("/events/analyze", json={"log_line": BRUTEFORCE_LOG})
    assert response.status_code == 200
    body = response.json()
    assert body["classification"] in ("SUSPEITO", "CRITICO")
    assert body["engine"] in ("heuristic", "llm", "heuristic_fallback")

    listed = client.get("/events").json()
    assert any(event["id"] == body["id"] for event in listed)


def test_analyze_batch_endpoint(client):
    response = client.post(
        "/events/analyze-batch", json={"log_lines": [BRUTEFORCE_LOG, NORMAL_LOG]}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


def test_analyze_rejects_empty_log(client):
    response = client.post("/events/analyze", json={"log_line": ""})
    assert response.status_code == 422


def test_stats_endpoint(client):
    client.post("/events/analyze", json={"log_line": BRUTEFORCE_LOG})
    client.post("/events/analyze", json={"log_line": NORMAL_LOG})
    response = client.get("/events/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["NORMAL"] >= 1


def test_filter_by_classification(client):
    client.post("/events/analyze", json={"log_line": NORMAL_LOG})
    response = client.get("/events", params={"classification": "NORMAL"})
    assert response.status_code == 200
    body = response.json()
    assert all(event["classification"] == "NORMAL" for event in body)


def test_get_event_not_found(client):
    response = client.get("/events/999999")
    assert response.status_code == 404
