import pytest

from app.indicator import detect_indicator_type
from app.models import InvalidIndicatorError


def test_detect_ipv4():
    assert detect_indicator_type("203.0.113.9") == "ip"


def test_detect_hash_md5():
    assert detect_indicator_type("44d88612fea8a8f36de82e1278abb02f") == "hash"


def test_detect_hash_sha256():
    assert detect_indicator_type("a" * 64) == "hash"


def test_detect_invalid_indicator():
    with pytest.raises(InvalidIndicatorError):
        detect_indicator_type("not-an-indicator")
