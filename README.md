# tw_trademarket_info

Utility scripts and data pipelines for gathering Taiwan market reference information.

## Getting Started
1. Copy `.env.example` to `.env` and fill in secrets such as `FINMIND_TOKEN` and a custom `USER_AGENT` that points to your GitHub profile.
2. Install dependencies using `pip install -e .[dev]` (or your preferred environment manager).
3. Run the lightweight smoke tests with `pytest`.

## Command Line Interface

The project exposes a small CLI for ad-hoc pulls:

```bash
python -m src.app pull twse.stock_day --param date=2024-01-05 --param stockNo=2330
```

Configuration overrides can be supplied inline:

```bash
python -m src.app pull mops.material_info_rss --config USER_AGENT="my-project/0.1"
```

Results are printed as JSON and contain metadata about the source, fetch time, and raw payload.

## Catalog Driven Sources

Available categories are declared in `src/registry/catalog.json`. Each entry defines the endpoint, HTTP method, query/payload templates, and parsing strategy (`json`, `csv`, or `rss`). The CLI resolves placeholders such as `{YYYYMMDD}` based on parameters you provide.

## Configuration
Environment variables are loaded from `.env`:

- `TZ`: Local timezone for scheduling.
- `HTTP_TIMEOUT`, `HTTP_MAX_RETRIES`, `HTTP_BACKOFF_BASE`: HTTP client tuning knobs.
- `USER_AGENT`: Replace `<yourname>` with your GitHub handle or project URL.
- `FINMIND_TOKEN`: API token for FinMind data access.
- `PROXY_URL`: Optional proxy server.

Update this README as the project evolves.
