from logsentinel.models import LogEntry

class SearchFilter:
    def __init__(self, keyword: str, case_sensitive: bool = False):
        self.keyword = keyword
        self.case_sensitive = case_sensitive

    def _matches_message(self, entry: LogEntry) -> bool:
        if self.case_sensitive:
            return self.keyword in entry.message
        else:
            return self.keyword.casefold() in entry.message.casefold()
    def _matches_metadata(self, entry: LogEntry) -> bool:
        if self.case_sensitive:
            return any(self.keyword in value for value in entry.metadata.values() if isinstance(value, str))
        else:
            return any(self.keyword.casefold() in value.casefold() for value in entry.metadata.values() if isinstance(value,str))

    def apply(self, entries: list[LogEntry]) -> list[LogEntry]:
        if not self.keyword:
            return entries
        return [e for e in entries if self._matches_message(e) or self._matches_metadata(e)]
