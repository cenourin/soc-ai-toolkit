from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

IndicatorType = Literal["ip", "hash"]
Source = Literal["abuseipdb", "virustotal", "mock"]
Channel = Literal["slack", "discord", "console"]


class InvalidIndicatorError(ValueError):
    pass


@dataclass
class ReputationResult:
    indicator: str
    indicator_type: IndicatorType
    malicious: bool
    score: int
    source: Source
    categories: list[str] = field(default_factory=list)


class LookupRequest(BaseModel):
    indicator: str = Field(min_length=3, description="Endereço IPv4 ou hash MD5/SHA1/SHA256")


class LookupResponse(BaseModel):
    id: int
    indicator: str
    indicator_type: IndicatorType
    malicious: bool
    score: int
    source: Source
    categories: list[str]
    created_at: str


class NotificationResponse(BaseModel):
    id: int
    lookup_id: int | None
    indicator: str
    channel: Channel
    message: str
    delivered: bool
    created_at: str


class LookupWithNotification(BaseModel):
    lookup: LookupResponse
    notification: NotificationResponse | None


class PlaybookRunResponse(BaseModel):
    processed: int
    malicious: int
    notifications_sent: int
