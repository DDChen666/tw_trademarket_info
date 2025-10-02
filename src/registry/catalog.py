"""Catalog registry for available data categories."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import json

CATALOG_PATH = Path(__file__).with_name("catalog.json")


@dataclass(slots=True)
class CatalogEntry:
    name: str
    raw: Dict[str, Any]

    @property
    def endpoint(self) -> str:
        return self.raw["endpoint"]

    @property
    def method(self) -> str:
        return self.raw.get("method", "GET").upper()

    def expand(self, params: Dict[str, Any]) -> Dict[str, Any]:
        expanded = {}
        for key, value in self.raw.items():
            if isinstance(value, dict):
                expanded[key] = {
                    sub_key: substitute(sub_value, params)
                    for sub_key, sub_value in value.items()
                }
            else:
                expanded[key] = substitute(value, params)
        return expanded


def load_catalog(path: Path | None = None) -> Dict[str, CatalogEntry]:
    catalog_path = path or CATALOG_PATH
    with catalog_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return {name: CatalogEntry(name=name, raw=data) for name, data in payload.items()}


def substitute(value: Any, params: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        result = value
        for key, param_value in params.items():
            result = result.replace(f"{{{key}}}", str(param_value))
        return result
    return value


__all__ = ["CatalogEntry", "load_catalog", "substitute", "CATALOG_PATH"]
