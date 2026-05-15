import os
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Standardized secret key names (Django settings compatible)
SHORTAGES_SHEET_URL = "SHORTAGES_SHEET_URL"
DONOTBUY_SHEET_URL = "DONOTBUY_SHEET_URL"

# Load .env file if it exists
load_dotenv()


def get_secret(key: str, env_var: str | None = None) -> str | None:
    """
    Retrieves a secret from multiple sources with a defined hierarchy:
    1. Django settings (django.conf.settings)
    2. Environment variables (including those from .env)

    Args:
        key (str): Secret key name (e.g., "SHORTAGES_SHEET_URL").
                   For Django settings, dot-separated keys are supported
                   (e.g., "GOOGLE.SERVICE_ACCOUNT" navigates settings.GOOGLE["SERVICE_ACCOUNT"]).
        env_var (str, optional): Name of the environment variable as fallback.
                                 If None, uses the key as the env var name directly.

    Returns:
        Optional[str]: The secret value if found, else None.
    """
    # 1. Try Django settings
    try:
        from django.conf import settings

        parts = key.split(".")
        value = getattr(settings, parts[0].upper(), None)
        for part in parts[1:]:
            if value is None:
                break
            value = value.get(part) if isinstance(value, dict) else getattr(value, part, None)
        if value is not None:
            return str(value)
    except Exception:
        pass

    # 2. Try Environment Variables
    if env_var is None:
        env_var = key

    return os.getenv(env_var)
