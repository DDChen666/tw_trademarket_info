# tw_trademarket_info

Utility scripts and data pipelines for gathering Taiwan market reference information.

## Getting Started
1. Copy `.env` and fill in secrets such as `FINMIND_TOKEN` and a custom `USER_AGENT` that points to your GitHub profile.
2. Install dependencies (add instructions once requirements are defined).

## Configuration
Environment variables are loaded from `.env`:

- `TZ`: Local timezone for scheduling.
- `HTTP_TIMEOUT`, `HTTP_MAX_RETRIES`, `HTTP_BACKOFF_BASE`: HTTP client tuning knobs.
- `USER_AGENT`: Replace `<yourname>` with your GitHub handle or project URL.
- `FINMIND_TOKEN`: API token for FinMind data access.
- `PROXY_URL`: Optional proxy server.

Update this README as the project evolves.
