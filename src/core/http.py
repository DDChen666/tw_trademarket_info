"""HTTP client helpers with retry and sensible defaults."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, Optional

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AppConfig, get_config

DEFAULT_STATUS_FORCELIST: Iterable[int] = (429, 500, 502, 503, 504)


class HTTPClient:
    """Thin wrapper around :class:`requests.Session` with retry policies."""

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self.config = config or get_config()
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=self.config.http_max_retries,
            read=self.config.http_max_retries,
            connect=self.config.http_max_retries,
            backoff_factor=self.config.http_backoff_base,
            status_forcelist=DEFAULT_STATUS_FORCELIST,
            allowed_methods=("GET", "POST"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.config.headers())
        if self.config.proxies:
            session.proxies.update(self.config.proxies)
        session.timeout = self.config.http_timeout
        return session

    @property
    def session(self) -> requests.Session:
        return self._session

    @contextmanager
    def context(self) -> Iterator[requests.Session]:
        try:
            yield self.session
        finally:
            self.close()

    def close(self) -> None:
        self.session.close()

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        timeout = kwargs.pop("timeout", self.config.http_timeout)
        response = self.session.request(method=method, url=url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    def get_json(self, url: str, **kwargs: Any) -> Any:
        response = self.request("GET", url, **kwargs)
        return response.json()

    def get_text(self, url: str, **kwargs: Any) -> str:
        response = self.request("GET", url, **kwargs)
        response.encoding = response.encoding or "utf-8"
        return response.text


__all__ = ["HTTPClient", "DEFAULT_STATUS_FORCELIST"]
