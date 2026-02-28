from logsentinel.filters import SearchFilter

def test_search_insensitive_match(entries_for_search_filter):
    result = SearchFilter("error").apply(entries_for_search_filter)
    assert len(result) == 1

def test_search_sensitive_match_null(entries_for_search_filter):
    result = SearchFilter("error", True).apply(entries_for_search_filter)
    assert len(result) == 0

def test_search_sensitive_match_not_null(entries_for_search_filter):
    result = SearchFilter("ERROR", True).apply(entries_for_search_filter)
    assert len(result) == 1

def test_search_empty_filter(entries_for_search_filter):
    result = SearchFilter("").apply(entries_for_search_filter)
    assert len(result) == 3

def test_search_match_metadata(entries_for_search_filter):
    result = SearchFilter("replica").apply(entries_for_search_filter)
    assert len(result) == 1

def test_search_not_match(entries_for_search_filter):
    result = SearchFilter("match").apply(entries_for_search_filter)
    assert len(result) == 0