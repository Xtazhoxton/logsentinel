from typer.testing import CliRunner
from logsentinel.cli import app
runner = CliRunner()
path = '/Users/arthur/Documents/logsentinel/tests/fixtures/cloudwatch_sample.json'
def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == "LogSentinel v0.1.0"

def test_parse_non_existent_file():
    result = runner.invoke(app, ["parse tests/fixtures/cloudwatch/log.json"])
    assert result.exit_code != 0

def test_parse_invalid_format():
    result = runner.invoke(app, ["parse", str(path), "--format", "invalid_format"])
    assert result.exit_code != 0

def test_parse_invalid_level():
    result = runner.invoke(app, ["parse", str(path), "--level", "INVALID"])
    assert result.exit_code == 1
    assert result.output.strip() is not None

def test_parse_valid_level():
    result = runner.invoke(app, ["parse", str(path), "--level", "DEBUG"])
    assert result.exit_code == 0