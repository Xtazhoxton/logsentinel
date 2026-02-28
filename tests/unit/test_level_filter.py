from logsentinel.filters import LevelFilter
from logsentinel.models import LogLevel

def test_min_level_debug(entries_all_levels):
    level_filter = LevelFilter(LogLevel.DEBUG)
    result = level_filter.apply(entries_all_levels)
    assert len(result) == 6

def test_min_level_warning(entries_all_levels):
    level_filter = LevelFilter(LogLevel.WARNING)
    result = level_filter.apply(entries_all_levels)
    assert len(result) == 4

def test_min_level_critical(entries_all_levels):
    level_filter = LevelFilter(LogLevel.CRITICAL)
    result = level_filter.apply(entries_all_levels)
    assert len(result) == 2

def test_min_level_error(entries_all_levels):
    level_filter = LevelFilter(LogLevel.ERROR)
    result = level_filter.apply(entries_all_levels)
    assert len(result) == 3

def test_min_level_info(entries_all_levels):
    level_filter = LevelFilter(LogLevel.INFO)
    result = level_filter.apply(entries_all_levels)
    assert len(result) == 5

def test_min_level_empty_list():
    level_filter = LevelFilter(LogLevel.CRITICAL)
    result = level_filter.apply([])
    assert len(result) == 0

def test_min_level_unknown_level(entries_only_unknown):
    level_filter = LevelFilter(LogLevel.DEBUG)
    level_filter_2 = LevelFilter(LogLevel.CRITICAL)
    result = level_filter.apply(entries_only_unknown)
    result_2 = level_filter_2.apply(entries_only_unknown)
    assert len(result) == 2 and len(result_2) == 2
