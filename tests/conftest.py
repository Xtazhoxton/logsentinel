from logsentinel.models import LogEntry, LogLevel
from logsentinel.parsers import CloudWatchParser
from pathlib import Path
from datetime import datetime, timezone
import pytest

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
