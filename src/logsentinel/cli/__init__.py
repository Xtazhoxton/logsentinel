from pathlib import Path
from typing import Optional
import typer
from logsentinel import __version__
from enum import Enum

app = typer.Typer(name="logsentinel", help="logsentinel CLI tool", add_completion=False)


class Format(str, Enum):
    cloudwatch = "cloudwatch"


@app.command()
def version():
    typer.echo("LogSentinel v{}".format(__version__))


valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@app.command()
def parse(
    file: Path = typer.Argument(exists=True),
    format: Format = typer.Option(Format.cloudwatch, "--format"),
    level: Optional[str] = typer.Option(None, "--level"),
    search: Optional[str] = typer.Option(None, "--search")
):
    if level is not None:
        if level.upper() not in valid_levels:
            typer.echo("Error: invalid level {}".format(level), err=True)
            raise typer.Exit(code=1)
    typer.echo("Parsing {} with format {}...".format(file, format.value))

