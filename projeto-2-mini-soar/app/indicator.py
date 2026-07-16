import re

from app.models import IndicatorType, InvalidIndicatorError

_IPV4_RE = re.compile(
    r"^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$"
)
_HASH_RE = re.compile(r"^[a-fA-F0-9]{32}$|^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$")


def detect_indicator_type(indicator: str) -> IndicatorType:
    indicator = indicator.strip()
    if _IPV4_RE.match(indicator):
        return "ip"
    if _HASH_RE.match(indicator):
        return "hash"
    raise InvalidIndicatorError(
        f"'{indicator}' nao e um IPv4 valido nem um hash MD5/SHA1/SHA256 valido"
    )
