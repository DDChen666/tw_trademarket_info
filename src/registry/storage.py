"""Storage planning utilities for catalogued endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional


def _as_path(*segments: str) -> Path:
    path = Path()
    for segment in segments:
        if not segment:
            continue
        path /= segment
    return path


def _placeholder(key: str) -> str:
    return f"{{{key}}}"


@dataclass(slots=True)
class StoragePlan:
    """Describe where a dataset should live on disk and how to derive the path."""

    scope: str
    dataset: str
    instrument_type: str | None = None
    parameter_key: str | None = None
    derivative_key: str | None = None
    frequency: str | None = None
    timezone: str | None = None
    notes: str | None = None

    def template(self, source_id: str) -> str:
        """Return the path template (with placeholders) for the plan."""
        template_path = self._build_path(source_id, placeholder=True)
        return str(template_path)

    def resolve(self, source_id: str, params: Mapping[str, Any]) -> Optional[str]:
        """Resolve the storage path using provided parameters if possible."""
        resolved = self._build_path(source_id, placeholder=False, params=params)
        return str(resolved) if resolved is not None else None

    def render(self, source_id: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Return a serialisable hint that contains template, metadata and resolved path."""
        if self.derivative_key:
            group = "derivatives"
        elif self.scope == "market":
            group = "market"
        elif self.scope == "source":
            group = "source"
        else:
            group = "spot"
        return {
            "scope": self.scope,
            "dataset": self.dataset,
            "group": group,
            "instrument_type": self.instrument_type,
            "frequency": self.frequency,
            "timezone": self.timezone,
            "template": self.template(source_id),
            "path": self.resolve(source_id, params),
            "parameter_key": self.parameter_key,
            "derivative_key": self.derivative_key,
            "notes": self.notes,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_path(
        self,
        source_id: str,
        *,
        placeholder: bool,
        params: Mapping[str, Any] | None = None,
    ) -> Optional[Path]:
        dataset_segments = [segment for segment in self.dataset.split("/") if segment]
        base = Path(source_id)

        if self.scope == "instrument":
            symbol_segment = self._segment(self.parameter_key, placeholder, params)
            if symbol_segment is None:
                return None
            if self.derivative_key:
                underlying_segment = self._segment(self.derivative_key, placeholder, params)
                if underlying_segment is None:
                    return None
                base = _as_path(base, underlying_segment, "derivatives", self.instrument_type or "derivative", symbol_segment)
            else:
                base = _as_path(base, symbol_segment, "spot")
        elif self.scope == "market":
            base = _as_path(base, "market")
        elif self.scope == "source":
            base = Path(source_id)
        else:
            base = _as_path(base, self.scope)

        for segment in dataset_segments:
            base /= segment
        return base

    def _segment(
        self,
        key: str | None,
        placeholder: bool,
        params: Mapping[str, Any] | None,
    ) -> Optional[str]:
        if key is None:
            return None if not placeholder else _placeholder("symbol")
        if placeholder:
            return _placeholder(key)
        if params is None:
            return None
        value = params.get(key)
        if value is None:
            return None
        return str(value)


DEFAULT_STORAGE_MAP: MutableMapping[str, StoragePlan] = {
    "twse.exchangeReport.STOCK_DAY": StoragePlan(
        scope="instrument",
        dataset="ohlcv/daily",
        instrument_type="equity",
        parameter_key="stock_code",
        frequency="1d",
        timezone="Asia/Taipei",
        notes="上市個股日成交資訊，統一寫入 spot/ohlcv/daily。",
    ),
    "twse.exchangeReport.STOCK_DAY_ALL": StoragePlan(
        scope="market",
        dataset="equities/ohlcv/daily/full",
        frequency="1d",
        timezone="Asia/Taipei",
    ),
    "twse.exchangeReport.BWIBBU_ALL": StoragePlan(
        scope="market",
        dataset="equities/valuation/daily",
        frequency="1d",
        timezone="Asia/Taipei",
    ),
    "twse.exchangeReport.MI_INDEX": StoragePlan(
        scope="market",
        dataset="market/index/daily",
        frequency="1d",
        timezone="Asia/Taipei",
    ),
    "twse.exchangeReport.MI_MARGN": StoragePlan(
        scope="market",
        dataset="credit/margin/daily",
        frequency="1d",
        timezone="Asia/Taipei",
    ),
    "twse.fund.T86_legacy": StoragePlan(
        scope="market",
        dataset="investors/top3/daily",
        frequency="1d",
        timezone="Asia/Taipei",
        notes="保留 legacy 投信/外資買賣超資訊。",
    ),
    "tpex.stock.daily_close_csv_legacy": StoragePlan(
        scope="instrument",
        dataset="ohlcv/daily",
        instrument_type="equity",
        parameter_key="stock_code",
        frequency="1d",
        timezone="Asia/Taipei",
    ),
    "taifex.openapi.samples.daily_report": StoragePlan(
        scope="market",
        dataset="derivatives/summary/daily",
        frequency="1d",
        timezone="Asia/Taipei",
    ),
    "taifex.download.prev30_ticks_notice": StoragePlan(
        scope="market",
        dataset="derivatives/ticks/landing",
        timezone="Asia/Taipei",
        notes="官網僅提供下載入口，實際檔案需另行抓取。",
    ),
    "mops.rss.material_information": StoragePlan(
        scope="source",
        dataset="disclosures/rss/material-information",
        timezone="Asia/Taipei",
    ),
    "mops.rss.shareholders_meetings": StoragePlan(
        scope="source",
        dataset="disclosures/rss/shareholders-meetings",
        timezone="Asia/Taipei",
    ),
    "mops.rss.ex_rights_dividends": StoragePlan(
        scope="source",
        dataset="disclosures/rss/ex-rights-dividends",
        timezone="Asia/Taipei",
    ),
    "mops.web.t05st01": StoragePlan(
        scope="instrument",
        dataset="disclosures/material/html",
        parameter_key="stock_code",
        timezone="Asia/Taipei",
        notes="備援查詢頁，與 RSS 存放在同一標的資料夾中。",
    ),
}


__all__ = ["StoragePlan", "DEFAULT_STORAGE_MAP"]
