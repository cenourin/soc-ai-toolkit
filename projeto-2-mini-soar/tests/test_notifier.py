from app.notifier import Notifier, format_alert_message
from app.models import ReputationResult


def test_console_notifier_records_message():
    notifier = Notifier()
    channel, delivered = notifier.notify("mensagem de teste")
    assert channel == "console"
    assert delivered is False


def test_format_alert_message_contains_indicator():
    result = ReputationResult(
        indicator="203.0.113.9",
        indicator_type="ip",
        malicious=True,
        score=97,
        source="mock",
        categories=["ssh-bruteforce"],
    )
    message = format_alert_message(result)
    assert "203.0.113.9" in message
    assert "97" in message
