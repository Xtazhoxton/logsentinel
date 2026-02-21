from logsentinel.models import LogLevel, LogEntry
from datetime import datetime, timezone
from dataclasses import replace
import pytest
from tests.conftest import sample_entry


def test_creation_with_valid_fields(sample_entry):
    test_entry = sample_entry

    assert test_entry.level == LogLevel.INFO
    assert test_entry.message == "Connection established"
    assert test_entry.source == "/aws/lambda/my-function"
    assert test_entry.raw == "[INFO] Connection established"
    assert test_entry.timestamp == datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

def test_equality_ignores_specified_fields(sample_entry):
    test_entry = replace(sample_entry, raw="[INFO] Connection established test",request_id="req-001", metadata={"correlation_id": "req-001"})
    test_entry_2= replace(sample_entry, correlation_id="req-001", metadata={"correlation_id": "req-002"})

    assert test_entry == test_entry_2

def test_equality_dont_ignores_message(sample_entry):
    test_entry = sample_entry
    test_entry_2 = replace(sample_entry, message="[INFO] Connection established test")
    assert test_entry != test_entry_2

def test_error_return_true_for_errors(sample_entry):
    test_info = sample_entry
    test_debug = replace(sample_entry, level=LogLevel.DEBUG)
    test_error = replace(sample_entry, level=LogLevel.ERROR)
    test_warning = replace(sample_entry, level=LogLevel.WARNING)
    test_critical = replace(sample_entry, level=LogLevel.CRITICAL)
    test_unknown = replace(sample_entry, level=LogLevel.UNKNOWN)

    assert test_error.is_error()
    assert test_critical.is_error()
    assert not test_warning.is_error()
    assert not test_debug.is_error()
    assert not test_info.is_error()
    assert not test_unknown.is_error()

def test_raise_error_on_not_valid_datetime(sample_entry):
    with pytest.raises(ValueError):
        replace(sample_entry, timestamp=datetime(2024, 1, 15, 10, 0, 0))