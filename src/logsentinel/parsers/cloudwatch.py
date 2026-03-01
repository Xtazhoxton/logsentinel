import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from logsentinel.models import LogEntry, LogLevel


class CloudWatchParser:
    @staticmethod
    def _extract_level(message: str) -> LogLevel:
        level_string = re.match(r"^\[(\w+)\]", message)
        if level_string is None:
            return LogLevel.UNKNOWN
        try:
            return LogLevel[level_string.group(1)]
        except KeyError:
            return LogLevel.UNKNOWN

    @staticmethod
    def _extract_request_id(message: str) -> str | None:
        request_id = re.search(r"RequestId:\s+(\S+)", message)
        if request_id:
            return request_id.group(1)
        return None

    def _parse_event(self, event: dict[str, Any], source: str) -> LogEntry:
        raw_message = event["message"]
        timestamp = datetime.fromtimestamp(event["timestamp"] / 1000, timezone.utc)
        level = self._extract_level(raw_message)
        request_id = self._extract_request_id(raw_message)
        return LogEntry(
            timestamp=timestamp,
            level=level,
            raw=raw_message,
            source=source,
            request_id=request_id,
            message=raw_message,
        )

    def parse_string(self, content: str) -> list[LogEntry]:
        raw_json = json.loads(content)
        if "logEvents" not in raw_json:
            raise ValueError("Missing 'logEvents' key in CloudWatch JSON")
        source = raw_json.get("logGroupName", "unknown")
        return [self._parse_event(event, source) for event in raw_json["logEvents"]]

    def parse_file(self, path: Path) -> list[LogEntry]:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        content = path.read_text(encoding="utf-8")
        return self.parse_string(content)
