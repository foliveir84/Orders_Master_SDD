"""
Generic cache decorator that works with or without Streamlit.

When Streamlit is available, delegates to ``st.cache_data`` for full
backward compatibility with the existing Streamlit app.  When Streamlit
is not available (e.g. Django, CLI, tests), falls back to an identity
decorator so the function runs uncached.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def cache_decorator(
    ttl: int = 3600,
    show_spinner: str | None = None,
) -> Callable[[F], F]:
    """
    Return a caching decorator that tries Streamlit first, else is a no-op.

    Args:
        ttl: Time-to-live in seconds for the cache entry (Streamlit only).
        show_spinner: Optional spinner text shown while computing (Streamlit only).

    Returns:
        A decorator that wraps the target function.
    """
    try:
        import streamlit as st  # noqa: PLC0415 — optional dependency

        kwargs: dict[str, Any] = {"ttl": ttl}
        if show_spinner is not None:
            kwargs["show_spinner"] = show_spinner
        return st.cache_data(**kwargs)  # type: ignore[no-any-return]
    except ImportError:
        import logging
        logging.getLogger(__name__).debug(
            "Streamlit not available; cache_decorator is a no-op. "
            "Consider configuring Django's cache framework."
        )

    # Fallback: identity decorator (no caching)
    def _identity(func: F) -> F:
        return func

    return _identity