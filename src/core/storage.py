"""Storage helpers for persisting raw and curated datasets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence, Mapping

import duckdb
import pandas as pd

RAW_DIR = Path("data/raw")
CURATED_DIR = Path("data/curated")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, records: Sequence[Mapping[str, object]]) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            json.dump(record, fh, ensure_ascii=False)
            fh.write("\n")


def dataframe_to_parquet(path: Path, df: pd.DataFrame) -> None:
    ensure_directory(path.parent)
    df.to_parquet(path, index=False)


def upsert_duckdb(
    table: str,
    df: pd.DataFrame,
    database: Path | str = Path("data/curated/market.duckdb"),
) -> None:
    database_path = Path(database)
    ensure_directory(database_path.parent)
    con = duckdb.connect(str(database_path))
    try:
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df LIMIT 0")
        con.register("df", df)
        con.execute(f"INSERT INTO {table} SELECT * FROM df")
    finally:
        con.unregister("df")
        con.close()


__all__ = [
    "RAW_DIR",
    "CURATED_DIR",
    "ensure_directory",
    "write_jsonl",
    "dataframe_to_parquet",
    "upsert_duckdb",
]
