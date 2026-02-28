from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from logsentinel.models import LogEntry, LogLevel
from logsentinel.parsers import CloudWatchParser

@pytest.fixture
def sample_entry():
    return LogEntry(
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        level=LogLevel.INFO,
        message="Connection established",
        source="/aws/lambda/my-function",
        raw="[INFO] Connection established"
    )

@pytest.fixture
def parsed_file():
    parser = CloudWatchParser()
    path = Path(__file__).resolve().parent / "fixtures" / "cloudwatch_sample.json"
    return parser.parse_file(path)


@pytest.fixture
def make_log_entry():
    def _make(
        *,
        level: LogLevel = LogLevel.INFO,
        message: str | None = None,
        minute_offset: int = 0,
        source: str = "/aws/lambda/my-function",
    ) -> LogEntry:
        base_ts = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        entry_message = message or f"{level.name} message"
        return LogEntry(
            timestamp=base_ts + timedelta(minutes=minute_offset),
            level=level,
            message=entry_message,
            source=source,
            raw=f"[{level.name}] {entry_message}",
        )

    return _make


@pytest.fixture
def entries_all_levels(make_log_entry):
    levels = [
        LogLevel.DEBUG,
        LogLevel.INFO,
        LogLevel.WARNING,
        LogLevel.ERROR,
        LogLevel.CRITICAL,
        LogLevel.UNKNOWN,
    ]
    return [
        make_log_entry(level=level, minute_offset=index)
        for index, level in enumerate(levels)
    ]


@pytest.fixture
def entries_only_unknown(make_log_entry):
    return [
        make_log_entry(level=LogLevel.UNKNOWN, message="Unknown event A", minute_offset=1),
        make_log_entry(level=LogLevel.UNKNOWN, message="Unknown event B", minute_offset=2),
    ]


@pytest.fixture
def expected_entries_min_debug(entries_all_levels):
    return entries_all_levels


@pytest.fixture
def expected_entries_min_warning(entries_all_levels):
    return [
        entry
        for entry in entries_all_levels
        if entry.level in (LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.UNKNOWN)
    ]


@pytest.fixture
def expected_entries_min_critical(entries_all_levels):
    return [
        entry
        for entry in entries_all_levels
        if entry.level in (LogLevel.CRITICAL, LogLevel.UNKNOWN)
    ]


@pytest.fixture
def entries_for_search_filter(make_log_entry):
    metadata_match_entry = LogEntry(
        timestamp=datetime(2024, 1, 15, 10, 1, 0, tzinfo=timezone.utc),
        level=LogLevel.INFO,
        message="Background task completed",
        source="/aws/lambda/my-function",
        raw="[INFO] Background task completed",
        metadata={"detail": "Database timeout on replica"},
    )

    no_match_entry = make_log_entry(
        level=LogLevel.DEBUG,
        message="Heartbeat check passed",
        minute_offset=2,
    )

    return [
        make_log_entry(level=LogLevel.ERROR, message="[ERROR] something", minute_offset=0),
        metadata_match_entry,
        no_match_entry,
    ]
