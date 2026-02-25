from pathlib import Path
from typer.testing import CliRunner
from logsentinel.cli import app
runner = CliRunner()
path = Path(__file__).parent.parent / "fixtures" / "cloudwatch_sample.json"

def test_parse_command():
    result = runner.invoke(app, ["parse", str(path)])
    assert result.exit_code == 0
    assert "Timestamp" in result.output