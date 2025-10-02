from datetime import datetime

import pytest

from app import parse_kv
from registry.catalog import load_catalog
from registry.storage import DEFAULT_STORAGE_MAP
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


def test_enrich_params_adds_roc_formats():
    enriched = enrich_params({"date": "2024-09-05"})
    assert enriched["YYY/MM"] == "113/09"
    assert enriched["YYYY/MM/DD"] == "2024/09/05"


def test_storage_plan_resolves_path():
    plan = DEFAULT_STORAGE_MAP["twse.exchangeReport.STOCK_DAY"]
    hint = plan.render("twse", {"stock_code": "2330"})
    assert hint["template"].endswith("{stock_code}/spot/ohlcv/daily")
    assert hint["path"].endswith("2330/spot/ohlcv/daily")


def test_catalog_loads_new_structure():
    catalog = load_catalog()
    entry = catalog.get_entry("twse.exchangeReport.STOCK_DAY")
    request = entry.expand({"stock_code": "2330", "date": "2024-09-30", "YYYYMMDD": "20240930"})
    assert request["method"] == "GET"
    assert "storage" in request
