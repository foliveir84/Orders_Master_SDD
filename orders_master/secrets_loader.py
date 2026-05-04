import os
from typing import Any, Optional
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

def get_secret(key_path: str, env_var: Optional[str] = None) -> Optional[str]:
    """
    Retrieves a secret from multiple sources with a defined hierarchy:
    1. Streamlit secrets (st.secrets)
    2. Environment variables (including those from .env)
    
    Args:
        key_path (str): Dot-separated path to the secret in st.secrets (e.g., "google_sheets.shortages_url").
        env_var (str, optional): Name of the environment variable as fallback. 
                                 If None, uses a capitalized version of key_path with underscores.
    
    Returns:
        Optional[str]: The secret value if found, else None.
    """
    # 1. Try Streamlit secrets
    try:
        import streamlit as st
        # Navigate the key_path (e.g., "db.password" -> st.secrets["db"]["password"])
        value = st.secrets
        for key in key_path.split("."):
            value = value[key]
        return str(value)
    except (ImportError, KeyError, AttributeError, FileNotFoundError):
        # Streamlit not available or secret not found in st.secrets
        pass

    # 2. Try Environment Variables
    if env_var is None:
        # Default env_var name: "google_sheets.shortages_url" -> "GOOGLE_SHEETS_SHORTAGES_URL"
        env_var = key_path.replace(".", "_").upper()
    
    return os.getenv(env_var)
