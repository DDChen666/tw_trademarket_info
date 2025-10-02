"""Catalog registry for available data categories and metadata."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import json

from .storage import DEFAULT_STORAGE_MAP, StoragePlan

CATALOG_PATH = Path(__file__).with_name("catalog.json")


@dataclass(slots=True)
class CatalogMetadata:
    """High level metadata for the loaded catalog."""

    version: str
    generated_at: str
    timezone: str
    notes: Iterable[str]


@dataclass(slots=True)
class Source:
    """Representation of a data source (TWSE, TPEx, TAIFEX, MOPS)."""

    id: str
    name: str
    base_urls: Iterable[str]
    discovery: Mapping[str, Any] | None
    raw: Mapping[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "base_urls": list(self.base_urls),
            "discovery": dict(self.discovery) if self.discovery else None,
        }


@dataclass(slots=True)
class CatalogEntry:
    """Normalized endpoint entry derived from the catalog JSON."""

    id: str
    raw: Dict[str, Any]
    source: Source
    global_defaults: Mapping[str, Any]

    @property
    def name(self) -> str:
        return self.raw.get("name", self.id)

    @property
    def storage_plan(self) -> StoragePlan | None:
        return DEFAULT_STORAGE_MAP.get(self.id)

    def expand(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        context = dict(params)
        http_defaults: Dict[str, Any] = dict(self.global_defaults.get("http", {}))
        scheduling_defaults: Dict[str, Any] = dict(self.global_defaults.get("scheduling", {}))

        method = self.raw.get("method", "GET").upper()
        url_template = self.raw.get("url_template")
        if not url_template:
            raise ValueError(f"Catalog entry '{self.id}' is missing 'url_template'.")

        expanded_url = _apply_template(url_template, context)
        query_template = self.raw.get("query_template") or {}
        expanded_query = _apply_template(query_template, context)
        payload_template = self.raw.get("payload_template") or {}
        expanded_payload = _apply_template(payload_template, context)
        header_template = self.raw.get("headers") or {}
        endpoint_headers = _apply_template(header_template, context)

        headers = {**http_defaults.get("headers", {}), **endpoint_headers}
        timeout_seconds = self.raw.get("timeout_seconds", http_defaults.get("timeout_seconds"))
        retries = _merge_dicts(http_defaults.get("retries"), self.raw.get("retries"))
        rate_limit = _merge_dicts(http_defaults.get("rate_limit"), self.raw.get("rate_limit"))
        scheduling = _merge_dicts(scheduling_defaults, self.raw.get("scheduling"))
        parser = self.raw.get("parser") or _parser_from_response(self.raw.get("response"))

        request: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "source": self.source.to_dict(),
            "method": method,
            "endpoint": expanded_url,
            "parser": parser,
            "response": self.raw.get("response"),
            "rate_limit": rate_limit,
            "retries": retries,
            "scheduling": scheduling,
        }

        if expanded_query:
            request["query"] = expanded_query
        if expanded_payload:
            request["payload"] = expanded_payload
        if headers:
            request["headers"] = headers
        if timeout_seconds is not None:
            request["timeout_seconds"] = timeout_seconds

        storage_plan = self.storage_plan
        if storage_plan is not None:
            request["storage"] = storage_plan.render(self.source.id, context)

        return request


@dataclass(slots=True)
class Catalog:
    """Loaded catalog container with metadata, sources and entries."""

    metadata: CatalogMetadata
    sources: Dict[str, Source]
    entries: Dict[str, CatalogEntry]

    def get_entry(self, entry_id: str) -> CatalogEntry:
        return self.entries[entry_id]

    def __getitem__(self, item: str) -> CatalogEntry:
        return self.get_entry(item)


def load_catalog(path: Path | None = None) -> Catalog:
    catalog_path = path or CATALOG_PATH
    with catalog_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    metadata = CatalogMetadata(
        version=payload.get("version", "unknown"),
        generated_at=payload.get("generated_at", ""),
        timezone=payload.get("timezone", "UTC"),
        notes=payload.get("notes", []),
    )

    defaults = payload.get("global_defaults", {})

    sources: Dict[str, Source] = {}
    entries: Dict[str, CatalogEntry] = {}

    for raw_source in payload.get("sources", []):
        source_id = raw_source["id"]
        source = Source(
            id=source_id,
            name=raw_source.get("name", source_id),
            base_urls=raw_source.get("base_urls", []),
            discovery=raw_source.get("discovery"),
            raw=raw_source,
        )
        sources[source_id] = source
        for endpoint in raw_source.get("endpoints", []):
            entry = CatalogEntry(
                id=endpoint["id"],
                raw=endpoint,
                source=source,
                global_defaults=defaults,
            )
            entries[entry.id] = entry

    return Catalog(metadata=metadata, sources=sources, entries=entries)


def substitute(value: Any, params: Mapping[str, Any]) -> Any:
    if isinstance(value, str):
        if value in params:
            return params[value]
        result = value
        for key, param_value in params.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(param_value))
        return result
    return value


def _apply_template(value: Any, params: Mapping[str, Any]) -> Any:
    if isinstance(value, dict):
        return {key: _apply_template(sub_value, params) for key, sub_value in value.items()}
    if isinstance(value, list):
        return [_apply_template(item, params) for item in value]
    return substitute(value, params)


def _merge_dicts(
    base: Mapping[str, Any] | None,
    overrides: Mapping[str, Any] | None,
) -> Dict[str, Any] | None:
    if not base and not overrides:
        return None
    merged: Dict[str, Any] = {}
    if base:
        merged.update(base)
    if overrides:
        merged.update(overrides)
    return merged


def _parser_from_response(response_meta: Mapping[str, Any] | None) -> str:
    if not response_meta:
        return "json"
    content_type = response_meta.get("content_type")
    if not content_type:
        return "json"
    normalized = str(content_type)
    for candidate in normalized.split("|"):
        mime = candidate.split(";")[0].strip().lower()
        if not mime:
            continue
        if mime in {"application/json", "text/json", "application/vnd.api+json"}:
            return "json"
        if mime in {"text/csv", "application/csv", "application/vnd.ms-excel"}:
            return "csv"
        if mime in {"application/rss+xml", "application/xml", "text/xml"}:
            return "rss"
        if mime in {"text/html", "application/xhtml+xml"}:
            return "html"
    return "json"


__all__ = [
    "Catalog",
    "CatalogEntry",
    "CatalogMetadata",
    "Source",
    "load_catalog",
    "substitute",
    "CATALOG_PATH",
]
