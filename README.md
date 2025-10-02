# tw_trademarket_info

Utility scripts and data pipelines for gathering Taiwan market reference information.

## Overview 概述

This repository bundles reusable extractors, validators, and a CLI for pulling reference and market structure data from TWSE, TPEx, TAIFEX, and MOPS APIs. Outputs are returned as JSON or CSV records that can be piped into downstream analytics jobs.

此專案整合台灣證券交易所（TWSE）、櫃買中心（TPEx）、期交所（TAIFEX）與公開資訊觀測站（MOPS）的資料擷取流程，並提供 CLI 方便批次或即時下載資料，輸出格式可直接串接後續分析流程。

## Data Coverage / 資料範圍

Available sources are centrally defined in `src/registry/catalog.json`. Each catalog entry specifies the HTTP method, payload template, parsing strategy, and validation rules.

| Catalog ID | Provider | Frequency | Format | Key Fields | Notes |
|------------|----------|-----------|--------|------------|-------|
| `twse.stock_day` | TWSE OpenAPI | Daily end-of-day | JSON | `date`, `open`, `high`, `low`, `close`, `volume` | Daily OHLCV for listed equities.<br>台股上市公司日線行情資料（含價格與成交量）。 |
| `twse.t86` | TWSE OpenAPI | Daily end-of-day | JSON | `date`, `stockNo`, `investorType` | Institutional buy/sell imbalance (三大法人).<br>三大法人買賣超統計。 |
| `twse.margin` | TWSE OpenAPI | Daily end-of-day | JSON | `date`, `stockNo`, margin metrics | Securities margin trading balances.<br>融資融券餘額資訊。 |
| `tpex.stock_day` | TPEx OpenAPI | Daily end-of-day | JSON | `Date`, `SecuritiesCompanyCode`, `Volume` | OTC equity dealer turnover.<br>櫃買中心券商成交統計。 |
| `taifex.daily_report` | TAIFEX | Daily end-of-day | CSV | `date`, `contract`, futures stats | TX futures daily market report.<br>台指期每日交易統計。 |
| `mops.material_info_rss` | MOPS | Intraday (workdays) | RSS | `guid`, `title`, `pubDate` | Material information announcements.<br>重大訊息即時 RSS。 |

## Setup / 環境設定

1. Create and activate a Python 3.11+ virtual environment (e.g. `python3 -m venv .venv` and `source .venv/bin/activate`). 建立並啟用 Python 3.11 以上的虛擬環境。
2. Install dependencies with `pip install -e .[dev]`. 使用 `pip install -e .[dev]` 安裝專案與開發套件。
3. Copy `.env.example` to `.env` and fill in `FINMIND_TOKEN`, `USER_AGENT`, and optional proxy settings. 複製 `.env.example` 為 `.env`，填入 FINMIND_TOKEN、USER_AGENT 等設定；若值包含空白或括號請以雙引號包裹。
4. Load the environment when executing commands, for example: `set -a && source .env && set +a`. 執行指令前匯入環境變數，如 `set -a && source .env && set +a`。

## Testing / 測試

- Run the smoke test suite with `pytest`. 使用 `pytest` 執行測試。
- Coverage plugins are pre-wired; append `--cov` if you need a coverage report. 已預先設定 coverage 外掛，可加 `--cov` 取得覆蓋率報告。

## Command Line Interface / 指令範例

Use the CLI for ad-hoc pulls:

```bash
python -m src.app pull twse.stock_day --param date=2024-01-05 --param stockNo=2330
```

自訂臨時抓取可透過 CLI：

```bash
python -m src.app pull mops.material_info_rss --config USER_AGENT="my-project/0.1"
```

Results are printed as JSON and contain metadata about the source, fetch time, and raw payload.

CLI 會回傳包含來源、抓取時間與原始資料的 JSON 結果，可再導入其他流程分析。

## Configuration / 設定

Environment variables are loaded from `.env`:

- `TZ`: Local timezone for scheduling. 排程使用的時區。
- `HTTP_TIMEOUT`, `HTTP_MAX_RETRIES`, `HTTP_BACKOFF_BASE`: HTTP client tuning knobs. HTTP 請求逾時與重試參數。
- `USER_AGENT`: Replace `<yourname>` with your GitHub handle or project URL. 自訂 User-Agent；建議填入 GitHub 頁面資訊。
- `FINMIND_TOKEN`: API token for FinMind data access. FinMind API 權杖。
- `PROXY_URL`: Optional proxy server. 選用的代理伺服器設定。

Update this README as the project evolves.
