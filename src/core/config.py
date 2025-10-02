"""Application configuration utilities."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict

try:  # pragma: no cover - optional dependency guard
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - fallback during minimal environments
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:  # type: ignore[override]
        return False

load_dotenv()


@dataclass(slots=True)
class AppConfig:
    """Central application configuration loaded from environment variables."""

    timezone: str = "Asia/Taipei"
    http_timeout: float = 15.0
    http_max_retries: int = 5
    http_backoff_base: float = 0.5
    user_agent: str = "taiwan-markets-db/0.1 (+https://github.com/DDChen666)"
    finmind_token: str | None = None
    proxy_url: str | None = None

    def __init__(self, **overrides: Any) -> None:
        values: Dict[str, Any] = {
            "timezone": os.getenv("TZ", self.timezone),
            "http_timeout": float(os.getenv("HTTP_TIMEOUT", self.http_timeout)),
            "http_max_retries": int(os.getenv("HTTP_MAX_RETRIES", self.http_max_retries)),
            "http_backoff_base": float(os.getenv("HTTP_BACKOFF_BASE", self.http_backoff_base)),
            "user_agent": os.getenv("USER_AGENT", self.user_agent),
            "finmind_token": os.getenv("FINMIND_TOKEN", self.finmind_token),
            "proxy_url": os.getenv("PROXY_URL", self.proxy_url),
        }
        values.update(overrides)
        object.__setattr__(self, "timezone", values["timezone"])
        object.__setattr__(self, "http_timeout", float(values["http_timeout"]))
        object.__setattr__(self, "http_max_retries", int(values["http_max_retries"]))
        object.__setattr__(self, "http_backoff_base", float(values["http_backoff_base"]))
        object.__setattr__(self, "user_agent", str(values["user_agent"]))
        object.__setattr__(self, "finmind_token", values.get("finmind_token") or None)
        object.__setattr__(self, "proxy_url", values.get("proxy_url") or None)

    @property
    def proxies(self) -> Dict[str, str]:
        """Return a Requests-compatible proxies dictionary."""

        if not self.proxy_url:
            return {}
        return {"http": self.proxy_url, "https": self.proxy_url}

    def headers(self) -> Dict[str, str]:
        """Construct default HTTP headers."""

        headers = {"User-Agent": self.user_agent}
        if self.finmind_token:
            headers["X-FinMind-Token"] = self.finmind_token
        return headers


@lru_cache(maxsize=1)
def get_config(**overrides: Any) -> AppConfig:
    """Return a cached application configuration instance."""

    return AppConfig(**overrides)


__all__ = ["AppConfig", "get_config"]
