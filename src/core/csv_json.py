"""Utilities for parsing CSV and JSON payloads with encoding detection."""
from __future__ import annotations

import io
import json
from typing import Any, Dict, Iterable, Optional

try:  # pragma: no cover - optional dependency guard
    import chardet
except ModuleNotFoundError:  # pragma: no cover - fallback when optional dep missing
    chardet = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency guard
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - fallback when optional dep missing
    pd = None  # type: ignore[assignment]


def detect_encoding(payload: bytes, fallback: str = "utf-8") -> str:
    """Detect the encoding of the given payload."""

    if chardet is None:  # pragma: no cover - fallback
        return fallback
    detection = chardet.detect(payload)
    encoding = detection.get("encoding") or fallback
    return encoding


def parse_json(text: str | bytes) -> Any:
    """Parse a JSON payload from a string or bytes."""

    if isinstance(text, bytes):
        encoding = detect_encoding(text)
        text = text.decode(encoding)
    return json.loads(text)


def parse_csv(
    payload: bytes,
    *,
    dtype: Optional[Dict[str, Any]] = None,
    parse_dates: Optional[Iterable[str]] = None,
    encoding: Optional[str] = None,
    **kwargs: Any,
):
    """Parse CSV payload into a DataFrame-like structure with encoding detection."""

    enc = encoding or detect_encoding(payload, fallback="utf-8")
    buffer = io.BytesIO(payload)
    if pd is None:  # pragma: no cover - fallback path
        import csv

        reader = csv.DictReader(io.TextIOWrapper(buffer, encoding=enc))
        return list(reader)
    df = pd.read_csv(
        buffer,
        dtype=dtype,
        parse_dates=list(parse_dates) if parse_dates else None,
        encoding=enc,
        **kwargs,
    )
    return df


__all__ = ["detect_encoding", "parse_json", "parse_csv"]
