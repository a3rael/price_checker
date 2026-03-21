from price_checker.main import format_timestamp


def test_format_timestamp_formats_iso_string():
    assert format_timestamp("2026-03-21T10:00:00+00:00") == "2026-03-21 10:00:00 UTC"


def test_format_timestamp_returns_original_for_invalid_value():
    assert format_timestamp("not-a-timestamp") == "not-a-timestamp"
