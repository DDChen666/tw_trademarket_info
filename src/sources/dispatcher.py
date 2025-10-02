"""Dispatch utilities for executing catalog entries."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple, TYPE_CHECKING

try:  # pragma: no cover - optional dependency guard
    import feedparser
except ModuleNotFoundError:  # pragma: no cover - fallback when optional dep missing
    feedparser = None  # type: ignore[assignment]

from src.core.csv_json import parse_csv

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from src.core.http import HTTPClient
    from src.registry.catalog import CatalogEntry

DATE_FORMATS: Tuple[str, ...] = ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d")


def enrich_params(params: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(params)
    date_value = params.get("date")
    if date_value:
        dt = _coerce_date(date_value)
        if dt:
            enriched.setdefault("YYYYMMDD", dt.strftime("%Y%m%d"))
            enriched.setdefault("YYYYMM", dt.strftime("%Y%m"))
            enriched.setdefault("YYYY", dt.strftime("%Y"))
            enriched.setdefault("MM", dt.strftime("%m"))
            enriched.setdefault("DD", dt.strftime("%d"))
            enriched.setdefault("YYYY/MM/DD", dt.strftime("%Y/%m/%d"))
            roc_year = dt.year - 1911
            if roc_year > 0:
                enriched.setdefault("ROC_YEAR", f"{roc_year:03d}")
                enriched.setdefault("ROC_YY", f"{roc_year:02d}")
                enriched.setdefault("YYY", f"{roc_year:03d}")
                enriched.setdefault("YY", f"{roc_year:02d}")
                enriched.setdefault("YYYMM", f"{roc_year:03d}{dt.month:02d}")
                enriched.setdefault("YYY/MM", f"{roc_year:03d}/{dt.month:02d}")
                enriched.setdefault("YYYMMDD", f"{roc_year:03d}{dt.month:02d}{dt.day:02d}")
                enriched.setdefault("YYY/MM/DD", f"{roc_year:03d}/{dt.month:02d}/{dt.day:02d}")
    return enriched


def _coerce_date(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def execute_entry(
    entry: "CatalogEntry",
    params: Dict[str, Any],
    client: "HTTPClient" | None = None,
) -> Dict[str, Any]:
    if client is None:
        from src.core.http import HTTPClient  # local import to avoid optional dependency at import time

        http_client = HTTPClient()
    else:
        http_client = client
    enriched = enrich_params(params)
    request_config = entry.expand(enriched)
    method = request_config.get("method", "GET").upper()
    url = request_config["endpoint"]
    parser = request_config.get("parser", "json")
    request_kwargs: Dict[str, Any] = {}
    if "query" in request_config:
        request_kwargs["params"] = request_config["query"]
    if "payload" in request_config:
        request_kwargs["data"] = request_config["payload"]
    if "headers" in request_config:
        request_kwargs["headers"] = request_config["headers"]
    if "timeout_seconds" in request_config:
        request_kwargs["timeout"] = request_config["timeout_seconds"]

    response = http_client.request(method, url, **request_kwargs)

    if parser == "json":
        payload = response.json()
    elif parser == "csv":
        df = parse_csv(response.content)
        if hasattr(df, "to_dict"):
            payload = df.to_dict(orient="records")  # type: ignore[call-arg]
        else:
            payload = list(df)
    elif parser == "rss":
        if feedparser is None:  # pragma: no cover - defensive branch
            raise RuntimeError("feedparser dependency is required for RSS parsing")
        feed = feedparser.parse(response.content.decode("utf-8", errors="ignore"))
        payload = {
            "feed": dict(feed.feed),
            "entries": [dict(entry) for entry in feed.entries],
        }
    else:
        payload = response.text

    return {
        "category": entry.id,
        "name": entry.name,
        "source": request_config.get("source"),
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "params": params,
        "payload": payload,
        "storage": request_config.get("storage"),
    }


__all__ = ["execute_entry", "enrich_params"]
