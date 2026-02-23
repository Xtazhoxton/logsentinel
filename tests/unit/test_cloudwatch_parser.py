from logsentinel.models import LogLevel
from logsentinel.parsers import CloudWatchParser
from pathlib import Path
import pytest

path = Path(__file__).resolve().parent.parent / "fixtures" / "cloudwatch_sample.json"
parser = CloudWatchParser()

def test_parse_file_success(parsed_file):
    assert len(parsed_file) == 5
    assert parsed_file[0].level == LogLevel.UNKNOWN
    assert parsed_file[1].level == LogLevel.ERROR
    assert parsed_file[1].request_id is None
    assert parsed_file[3].request_id == 'req-001'
    assert [entry.timestamp.tzinfo is not None for entry in parsed_file]

def test_parse_string_success():
    path_content = path.read_text()
    parsed_content = parser.parse_string(path_content)
    assert len(parsed_content) == 5

def test_parse_file_failure_on_non_existent_file():
    with pytest.raises(FileNotFoundError):
        parser.parse_file(Path('"nonexistent.json"'))

def test_parse_string_failure_on_miss_event():
    with pytest.raises(ValueError):
        parser.parse_string('{"id": "001", "timestamp": 1705312245123, "message": "START RequestId: req-001 Version: $LATEST"}')

def test_parse_string_return_empty_list():
    assert parser.parse_string('{"logGroupName": "/aws/lambda/my-function","logStreamName": "2024/01/15/[$LATEST]abc123","logEvents": []}') == []
