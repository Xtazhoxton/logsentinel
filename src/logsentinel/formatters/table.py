from logsentinel.models import LogLevel, LogEntry
from rich.table import Table

STYLES = {
    LogLevel.ERROR: "red",
    LogLevel.CRITICAL: "red",
    LogLevel.WARNING: "yellow",
    LogLevel.INFO: "green",
    LogLevel.DEBUG: "blue",
}

class TableFormatter:
    def _level_style(self, level: LogLevel) -> str:
        return STYLES.get(level, "dim")
    def format(self, entries: list[LogEntry]) -> Table:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Timestamp")
        table.add_column("Level")
        table.add_column("Source")
        table.add_column("Message")
        for entry in entries:
            formated_timestamp = entry.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            formatted_message = entry.message
            if len(formatted_message) > 80:
                formatted_message = formatted_message[:79] + "…"
            row_style = self._level_style(entry.level)
            table.add_row(
                formated_timestamp,
                entry.level.name,
                entry.source,
                formatted_message,
                style=row_style
            )
        return table