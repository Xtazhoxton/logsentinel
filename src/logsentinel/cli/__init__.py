from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from logsentinel import __version__
from logsentinel.filters import LevelFilter, SearchFilter
from logsentinel.formatters import TableFormatter
from logsentinel.models import LogLevel, LogEntry
from logsentinel.parsers import CloudWatchParser

app = typer.Typer(name="logsentinel", help="logsentinel CLI tool", add_completion=False)


class Format(str, Enum):
    cloudwatch = "cloudwatch"


@app.command()
def version() -> None:
    typer.echo("LogSentinel v{}".format(__version__))


valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@app.command()
def parse(
    file: Path = typer.Argument(exists=True),
    format: Format = typer.Option(Format.cloudwatch, "--format"),
    level: Optional[str] = typer.Option(None, "--level"),
    search: Optional[str] = typer.Option(None, "--search")
) -> None:
    if level is not None:
        if level.upper() not in valid_levels:
            typer.echo("Error: invalid level {}".format(level), err=True)
            raise typer.Exit(code=1)
    parser = CloudWatchParser()
    try:
        result = parser.parse_file(file)
    except FileNotFoundError:
        typer.echo("Error: file {} not found".format(file), err=True)
        raise typer.Exit(code=1)
    except ValueError:
        typer.echo("Error: file {} not valid".format(file), err=True)
        raise typer.Exit(code=1)
    if len(result) == 0:
        typer.echo("No log entries found.")
        raise typer.Exit(code=0)

    if level is not None:
        min_level = LogLevel[level.upper()]
        level_filter = LevelFilter(min_level)
        result = level_filter.apply(result)

    if search is not None:
        result = SearchFilter(search).apply(result)

    table = TableFormatter().format(entries=result)
    Console().print(table)


