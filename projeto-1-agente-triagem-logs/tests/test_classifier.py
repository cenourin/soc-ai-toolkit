from app.heuristics import HeuristicClassifier

classifier = HeuristicClassifier()


def test_heuristic_bruteforce_ssh():
    result = classifier.classify(
        "Jul 15 03:12:01 srv01 sshd[1234]: Failed password for root from 203.0.113.9 port 51321 ssh2"
    )
    assert result.classification in ("SUSPEITO", "CRITICO")
    assert result.suggested_action in ("bloquear_ip", "investigar_usuario")
    assert "203.0.113.9" in result.summary


def test_heuristic_normal_login():
    result = classifier.classify(
        "Jul 15 03:14:10 srv01 sshd[1240]: Accepted password for deploy from 10.0.0.5 port 40210 ssh2"
    )
    assert result.classification == "NORMAL"
    assert result.suggested_action == "ignorar"


def test_heuristic_port_scan():
    result = classifier.classify(
        "Jul 15 03:20:11 srv02 nmap-detector: port scan detected from 198.51.100.77 targeting ports 21,22,23,80,443,3389"
    )
    assert result.classification == "SUSPEITO"


def test_heuristic_malware_is_critical():
    result = classifier.classify(
        "Jul 15 03:25:33 edr01 agent: exploit detected: reverse shell attempt on host 10.0.0.14"
    )
    assert result.classification == "CRITICO"
    assert result.suggested_action == "escalar"
