"""Lightweight validation helpers for ingested payloads."""
from __future__ import annotations

from typing import Iterable, Mapping, Sequence


class ValidationError(RuntimeError):
    """Raised when payload validation fails."""


def require_keys(record: Mapping[str, object], required: Iterable[str]) -> None:
    missing = [key for key in required if key not in record]
    if missing:
        raise ValidationError(f"Missing required keys: {', '.join(missing)}")


def ensure_non_negative(record: Mapping[str, object], fields: Iterable[str]) -> None:
    negatives = []
    for field in fields:
        value = record.get(field)
        if value is None:
            continue
        try:
            if float(value) < 0:
                negatives.append(field)
        except (TypeError, ValueError):
            continue
    if negatives:
        raise ValidationError(f"Negative values in fields: {', '.join(negatives)}")


def validate_records(
    records: Sequence[Mapping[str, object]],
    *,
    required: Iterable[str] | None = None,
    non_negative: Iterable[str] | None = None,
) -> None:
    for record in records:
        if required:
            require_keys(record, required)
        if non_negative:
            ensure_non_negative(record, non_negative)


__all__ = ["ValidationError", "require_keys", "ensure_non_negative", "validate_records"]
