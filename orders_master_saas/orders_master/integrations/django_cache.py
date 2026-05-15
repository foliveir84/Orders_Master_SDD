"""
Django cache decorator that replaces @st.cache_data with Django's cache framework.

Use this in Django views, management commands, and background tasks where
the Streamlit-based ``cache_decorator`` would be a no-op.
"""

import hashlib
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def _make_cache_key(key_prefix: str, args, kwargs) -> str:
    """Build a deterministic, namespaced cache key from the prefix and call args."""
    key_data = f"{key_prefix}:{args}:{sorted(kwargs.items())}"
    return f"omc:{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"


def django_cache_decorator(timeout: int = 3600, key_prefix: str = ""):
    """
    Cache decorator backed by ``django.core.cache``.

    Mirrors the interface of the Streamlit ``@st.cache_data`` decorator but
    uses Django's configured cache backend instead.

    Args:
        timeout: Cache TTL in seconds (default 1 hour).
        key_prefix: Prefix for cache keys.  Defaults to the wrapped
            function's ``__name__`` when empty.

    Returns:
        A decorator that caches the wrapped function's return value.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from django.core.cache import cache

            cache_key = _make_cache_key(key_prefix or func.__name__, args, kwargs)
            result = cache.get(cache_key)
            if result is not None:
                logger.debug("Cache hit: %s", cache_key)
                return result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            logger.debug("Cache miss: %s", cache_key)
            return result

        return wrapper

    return decorator