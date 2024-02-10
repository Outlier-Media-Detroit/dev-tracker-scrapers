import pytest  # noqa
from tracker.utils import clean_spaces, parse_addresses


def test_clean_spaces():
    assert clean_spaces(" test\r\n   \n\t test  \t") == "test test"


def test_parse_addresses_parts():
    assert parse_addresses("13 test 1234, and 23 Main St test") == [
        "1234 Main St",
        "23 Main St",
    ]
