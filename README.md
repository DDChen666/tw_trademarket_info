# tw_trademarket_info

Utility scripts and data pipelines for gathering Taiwan market reference information.

## Overview 概述

This repository bundles reusable extractors, validators, and a CLI for pulling reference and market structure data from TWSE, TPEx, TAIFEX, and MOPS APIs. Outputs are returned as JSON or CSV records that can be piped into downstream analytics jobs.

此專案整合台灣證券交易所（TWSE）、櫃買中心（TPEx）、期交所（TAIFEX）與公開資訊觀測站（MOPS）的資料擷取流程，並提供 CLI 方便批次或即時下載資料，輸出格式可直接串接後續分析流程。

## Data Coverage / 資料範圍

The unified catalog lives in `src/registry/catalog.json`. The JSON now exposes:

- `version`, `generated_at`, `timezone`, `notes`: metadata describing the snapshot.
- `global_defaults.http`: shared timeout, retry, header, and rate-limit defaults for all endpoints.
- `sources[]`: TWSE / TPEx / TAIFEX OpenAPI blocks (with discovery URLs) and MOPS RSS templates. Each source lists its `endpoints[]` with request templates, scheduling hints, response field mappings, and licensing notes.

Key ready-to-use entries include:

| Catalog ID | Provider | Frequency | Format | Highlights |
|------------|----------|-----------|--------|------------|
| `twse.exchangeReport.STOCK_DAY` | TWSE legacy JSON | Daily 16:30+ | JSON | Per-symbol OHLCV with post-processing instructions. |
| `twse.exchangeReport.BWIBBU_ALL` | TWSE legacy JSON | Daily 16:30+ | JSON | 全市場殖利率、股價淨值比等估值指標。 |
| `tpex.stock.daily_close_csv_legacy` | TPEx legacy HTML/CSV | Daily 16:30+ | JSON/CSV | 上櫃個股日成交，含 ROC 日期轉換與欄位對映。 |
| `taifex.openapi.samples.daily_report` | TAIFEX OpenAPI | Daily 16:30+ | JSON | 期交所市場彙整樣板，可自動列舉 swagger paths 延伸。 |
| `mops.rss.material_information` | MOPS RSS | Intraday 1–3 min | RSS | 重大訊息 RSS，自動探索 feed URL。 |
| `mops.web.t05st01` | MOPS HTML | Intraday 5 min | HTML | 歷史重大訊息查詢頁面備援。 |

Because each source section references its Swagger/OpenAPI spec (`discovery.spec_url`), an ETL job can programmatically enumerate all available paths to bootstrap request templates and avoid manual omissions.

### Storage hierarchy / 資料存放層級

To keep spot symbols and their derivatives organised together, a storage planner (`registry.storage.StoragePlan`) describes where each dataset should land. Paths follow the convention:

```
data/<source>/<underlying>/spot/<dataset>/...         # 基礎標的（現貨資料）
data/<source>/<underlying>/derivatives/<type>/<id>/... # 衍生品（期貨、選擇權等）
data/<source>/market/<dataset>/...                     # 市場彙整資料
data/<source>/disclosures/...                          # 與來源相關的公告 / RSS
```

- Instrument-scoped endpoints (e.g. `twse.exchangeReport.STOCK_DAY`, `tpex.stock.daily_close_csv_legacy`) resolve to `…/<stock_code>/spot/ohlcv/daily`.
- Market-wide datasets (e.g. `twse.exchangeReport.BWIBBU_ALL`) are grouped under `…/market/…`.
- MOPS feeds remain under `mops/disclosures/...`, while per-company HTML fallbacks share the same underlying directory via the `stock_code` parameter.

The planner is extensible—add or override entries in `DEFAULT_STORAGE_MAP` to slot new derivatives (e.g. TAIFEX options) under the same underlying symbol tree. `CatalogEntry.expand()` surfaces the computed template and resolved path (if parameters suffice) in the CLI response, making downstream routing or backtesting storage pipelines deterministic.

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
python -m src.app pull twse.exchangeReport.STOCK_DAY --param stock_code=2330 --param date=2024-09-30
```

自訂臨時抓取可透過 CLI：

```bash
python -m src.app pull mops.rss.material_information --config USER_AGENT="my-project/0.1"
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
