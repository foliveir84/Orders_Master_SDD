import io
import logging

import pandas as pd
from django.core.cache import cache

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "om:session"
_DEFAULT_TTL = 3600  # 1 hour


class ProcessingSession:
    """Redis-backed session storage for DataFrames and scalar values.

    Uses Django's cache framework so it works with LocMemCache in development
    and django-redis in production.  DataFrames are serialised as Parquet bytes.
    """

    def __init__(self, session_key: str):
        self._key = f"{_CACHE_PREFIX}:{session_key}"
        self._stored_names: set[str] = set()

    def _full_key(self, name: str) -> str:
        return f"{self._key}:{name}"

    # ── DataFrame helpers ───────────────────────────────────────────────

    def store(self, name: str, df: pd.DataFrame, ttl: int = _DEFAULT_TTL) -> None:
        cache.set(self._full_key(name), df.to_parquet(), timeout=ttl)
        self._stored_names.add(name)

    def get(self, name: str) -> pd.DataFrame | None:
        data = cache.get(self._full_key(name))
        if data is None:
            return None
        return pd.read_parquet(io.BytesIO(data))

    # ── Scalar / JSON-serialisable helpers ───────────────────────────────

    def store_value(self, name: str, value, ttl: int = _DEFAULT_TTL) -> None:
        cache.set(self._full_key(name), value, timeout=ttl)
        self._stored_names.add(name)

    def get_value(self, name):
        return cache.get(self._full_key(name))

    # ── Cleanup ──────────────────────────────────────────────────────────

    def clear(self) -> None:
        # Try the redis-native ``keys()`` first; fall back to tracked names
        # for LocMemCache compatibility (LocMemCache has no .keys() method).
        try:
            keys = cache.keys(f"{self._key}:*")
        except (AttributeError, NotImplementedError):
            keys = [self._full_key(n) for n in self._stored_names]
        if keys:
            cache.delete_many(keys)
        self._stored_names.clear()