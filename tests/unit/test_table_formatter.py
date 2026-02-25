import pytest
from pathlib import Path
from logsentinel.formatters import TableFormatter
from rich.table import Table
from datetime import datetime, UTC
from logsentinel.models.log_entry import LogEntry, LogLevel

entries = [
    LogEntry(
        timestamp=datetime(2024, 1, 15, 10, 31, 0, tzinfo=UTC),
        level=LogLevel.INFO,
        message="Service started",
        source="/aws/lambda/my-function",
        raw="[INFO] Service started",
    ),
    LogEntry(
        timestamp=datetime(2024, 1, 15, 10, 32, 0, tzinfo=UTC),
        level=LogLevel.WARNING,
        message="Retrying DB connection",
        source="/aws/lambda/my-function",
        raw="[WARNING] Retrying DB connection",
    ),
    LogEntry(
        timestamp=datetime(2024, 1, 15, 10, 33, 0, tzinfo=UTC),
        level=LogLevel.ERROR,
        message="Database connection failed after multiple retries and timeout on primary endpoint",
        source="/aws/lambda/my-function",
        raw="[ERROR] Database connection failed after multiple retries and timeout on primary endpoint",
    ),
    LogEntry(
        timestamp=datetime(2024, 1, 15, 10, 34, 0, tzinfo=UTC),
        level=LogLevel.UNKNOWN,
        message="Database connection failed after multiple retries and timeout on primary endpoint",
        source="/aws/lambda/my-function",
        raw="[ERROR] Database connection failed after multiple retries and timeout on primary endpoint",
    ),
    LogEntry(
        timestamp=datetime(2024, 1, 15, 10, 35, 0, tzinfo=UTC),
        level=LogLevel.DEBUG,
        message="Database connection failed after multiple retries and timeout on primary endpoint",
        source="/aws/lambda/my-function",
        raw="Database connection failed after multiple retries and timeout on primary endpoint",
    )
]

def test_table_formatter():
    formatter = TableFormatter()
    assert isinstance(formatter.format(entries), Table)

def test_level_style():
    formatter = TableFormatter()
    assert formatter._level_style(entries[0].level) == "green"
    assert formatter._level_style(entries[1].level) == "yellow"
    assert formatter._level_style(entries[2].level) == "red"
    assert formatter._level_style(entries[3].level) == "dim"
    assert formatter._level_style(entries[4].level) == "blue"