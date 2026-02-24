from typing import Protocol
from pathlib import Path
from logsentinel.models import LogEntry

class Parser(Protocol):
    def parse_file(self, path:Path) -> list[LogEntry]:...
    def parse_string(self, content:str) -> list[LogEntry]:...