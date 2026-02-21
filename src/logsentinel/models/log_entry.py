from datetime import datetime, timezone, UTC
from enum import IntEnum
from dataclasses import dataclass, field

class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    UNKNOWN = 60

@dataclass(frozen=True)
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    raw: str = field(compare=False)
    correlation_id: str | None = field(compare=False, default=None)
    request_id: str | None = field(compare=False, default=None)
    metadata: dict[str, str] = field(compare=False, default_factory=dict)

    def is_error(self) -> bool:
        return self.level == LogLevel.ERROR or self.level == LogLevel.CRITICAL

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is not UTC:
            raise ValueError("timestamp must be in UTC")