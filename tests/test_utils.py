from datetime import datetime

import pytest

from app import parse_kv
from sources.dispatcher import enrich_params


def test_parse_kv_parses_pairs():
    result = parse_kv(["foo=bar", "baz=1"])
    assert result == {"foo": "bar", "baz": "1"}


@pytest.mark.parametrize("value,expected", [
    ("2024-01-02", "20240102"),
    ("20240102", "20240102"),
    (datetime(2023, 12, 31), "20231231"),
])
def test_enrich_params_adds_derived_dates(value, expected):
    enriched = enrich_params({"date": value})
    assert enriched["YYYYMMDD"] == expected
