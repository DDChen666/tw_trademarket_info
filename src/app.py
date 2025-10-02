"""Command line interface for fetching catalogued data categories."""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from core.config import get_config


def parse_kv(pairs: list[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"Invalid param '{pair}'. Use key=value format.")
        key, value = pair.split("=", 1)
        result[key] = value
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Taiwan markets data ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pull_parser = subparsers.add_parser("pull", help="Fetch a category payload")
    pull_parser.add_argument("category", help="Catalog category name, e.g. twse.stock_day")
    pull_parser.add_argument(
        "--param",
        dest="params",
        action="append",
        default=[],
        help="Parameter in key=value form. Repeat for multiple parameters.",
    )
    pull_parser.add_argument(
        "--config",
        dest="config_overrides",
        action="append",
        default=[],
        help="Override configuration values using key=value.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "pull":
        params = parse_kv(args.params)
        config_overrides = parse_kv(args.config_overrides)
        config = get_config(**config_overrides)
        from core.http import HTTPClient
        from registry.catalog import load_catalog
        from sources.dispatcher import execute_entry

        catalog = load_catalog()
        try:
            entry = catalog[args.category]
        except KeyError as exc:
            parser.error(f"Unknown category: {args.category}")
            raise exc

        client = HTTPClient(config)
        try:
            result = execute_entry(entry, params, client)
        finally:
            client.close()
        print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
        return 0

    parser.error("Unsupported command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
