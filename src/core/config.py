"""Application configuration utilities."""
from __future__ import annotations

import os
from dataclasses import MISSING, dataclass, fields
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
        field_defaults: Dict[str, Any] = {}
        for field in fields(self):
            if field.default is not MISSING:
                field_defaults[field.name] = field.default
            elif field.default_factory is not MISSING:  # pragma: no cover - defensive guard
                field_defaults[field.name] = field.default_factory()
            else:  # pragma: no cover - every field currently has a default
                raise TypeError(f"Field '{field.name}' requires a default value")

        values: Dict[str, Any] = {
            "timezone": os.getenv("TZ", field_defaults["timezone"]),
            "http_timeout": os.getenv("HTTP_TIMEOUT", field_defaults["http_timeout"]),
            "http_max_retries": os.getenv("HTTP_MAX_RETRIES", field_defaults["http_max_retries"]),
            "http_backoff_base": os.getenv("HTTP_BACKOFF_BASE", field_defaults["http_backoff_base"]),
            "user_agent": os.getenv("USER_AGENT", field_defaults["user_agent"]),
            "finmind_token": os.getenv("FINMIND_TOKEN", field_defaults["finmind_token"]),
            "proxy_url": os.getenv("PROXY_URL", field_defaults["proxy_url"]),
        }
        values.update(overrides)

        timezone_value = values.get("timezone")
        user_agent_value = values.get("user_agent")

        object.__setattr__(self, "timezone", timezone_value if timezone_value is not None else field_defaults["timezone"])
        object.__setattr__(self, "http_timeout", float(values["http_timeout"]))
        object.__setattr__(self, "http_max_retries", int(values["http_max_retries"]))
        object.__setattr__(self, "http_backoff_base", float(values["http_backoff_base"]))
        object.__setattr__(self, "user_agent", user_agent_value if user_agent_value is not None else field_defaults["user_agent"])
        finmind_token = values.get("finmind_token")
        proxy_url = values.get("proxy_url")
        object.__setattr__(self, "finmind_token", finmind_token or None)
        object.__setattr__(self, "proxy_url", proxy_url or None)

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
