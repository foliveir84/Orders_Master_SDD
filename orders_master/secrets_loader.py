import os

from dotenv import load_dotenv

# Standardized secret key names (Django settings compatible)
SHORTAGES_SHEET_URL = "SHORTAGES_SHEET_URL"
DONOTBUY_SHEET_URL = "DONOTBUY_SHEET_URL"

# Load .env file if it exists
load_dotenv()


def get_secret(key: str, env_var: str | None = None) -> str | None:
    """
    Retrieves a secret from multiple sources with a defined hierarchy:
    1. Streamlit secrets (st.secrets) — using flat key names
    2. Environment variables (including those from .env)

    Args:
        key (str): Secret key name (e.g., "SHORTAGES_SHEET_URL").
        env_var (str, optional): Name of the environment variable as fallback.
                                 If None, uses the key as the env var name directly.

    Returns:
        Optional[str]: The secret value if found, else None.
    """
    # 1. Try Streamlit secrets
    try:
        import streamlit as st  # noqa: PLC0415

        return str(st.secrets[key])
    except (ImportError, KeyError, AttributeError, FileNotFoundError):
        # Streamlit not available or secret not found in st.secrets
        pass

    # 2. Try Environment Variables
    if env_var is None:
        env_var = key

    return os.getenv(env_var)
