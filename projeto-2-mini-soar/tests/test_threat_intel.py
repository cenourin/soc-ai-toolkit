from app.threat_intel_client import ThreatIntelClient


def test_mock_reputation_known_malicious_ip():
    client = ThreatIntelClient()
    result = client.lookup("203.0.113.9")
    assert result.malicious is True
    assert result.source == "mock"
    assert result.score > 0


def test_mock_reputation_unknown_indicator():
    client = ThreatIntelClient()
    result = client.lookup("1.2.3.4")
    assert result.malicious is False
    assert result.score == 0


def test_mock_reputation_known_hash():
    client = ThreatIntelClient()
    result = client.lookup("44d88612fea8a8f36de82e1278abb02f")
    assert result.indicator_type == "hash"
    assert result.malicious is True
