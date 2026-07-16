"""HTTP helper with retry, timeout, response caching and graceful
fallback. Provider failures never raise to the caller; they return None
or a fallback value and are logged."""

import logging
import time
from functools import wraps
from typing import Callable, Optional

import requests
from requests_cache import CachedSession

from .config import settings

logger = logging.getLogger("provider.http")


def _build_session() -> CachedSession:
    return CachedSession(
        cache_name=settings.http_cache_dir,
        backend="sqlite",
        expire_after=settings.http_cache_ttl,
        allowable_methods=("GET",),
    )


_SESSION = _build_session()


def request_json(
    url: str,
    *,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    timeout: Optional[float] = None,
    retries: Optional[int] = None,
    fallback: Callable[[], object] = lambda: None,
    provider: str = "http",
) -> object:
    """GET a JSON endpoint with retries + caching. On any failure returns
    fallback() result and logs the error (never raises)."""
    timeout = timeout or settings.http_timeout
    retries = retries if retries is not None else settings.http_max_retries
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            resp = _SESSION.get(url, headers=headers, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_err = exc
            logger.warning(
                "[%s] request failed (attempt %d/%d): %s %s -> %s",
                provider, attempt, retries, url, params, exc,
            )
            time.sleep(min(2 ** attempt, 10))
    logger.error("[%s] request exhausted retries for %s: %s", provider, url, last_err)
    return fallback()


def get_session() -> CachedSession:
    return _SESSION
