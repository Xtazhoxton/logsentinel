from logsentinel.models import LogLevel, LogEntry

class LevelFilter:
    def __init__(self, min_level: LogLevel):
        self.min_level = min_level
    def apply(self, entries: list[LogEntry]):
        return [entry for entry in entries if entry.level >= self.min_level or entry.level == LogLevel.UNKNOWN]