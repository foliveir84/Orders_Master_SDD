import json
import logging
import os
import re
from pathlib import Path

import streamlit as st
from pydantic import RootModel, model_validator

from orders_master.exceptions import ConfigError

logger = logging.getLogger(__name__)


class LocationsConfig(RootModel[dict[str, str]]):
    """
    Schema for localizacoes.json validation.
    Maps Search Term -> Alias.
    """

    root: dict[str, str]

    @model_validator(mode="after")
    def validate_locations(self) -> "LocationsConfig":
        """
        Validates location search terms.
        Ensures search terms have at least 3 characters to avoid weak matches.
        """
        for term, alias in self.root.items():
            if len(term) < 3:
                raise ValueError(
                    f"O termo de pesquisa '{term}' deve ter pelo menos 3 caracteres "
                    "para evitar correspondências por substring frágeis."
                )
        return self


def get_file_mtime(path: Path) -> float:
    """
    Returns the modification time of a file.

    Args:
        path (Path): Path to the file.

    Returns:
        float: Modification time or 0.0 if error.
    """
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


@st.cache_data
def load_locations(mtime: float, path: Path = Path("config/localizacoes.json")) -> LocationsConfig:
    """
    Loads and validates localizacoes.json.
    Uses mtime to invalidate cache in Streamlit.

    Args:
        mtime (float): File modification time (used as cache key).
        path (Path): Path to the JSON file.

    Returns:
        LocationsConfig: Validated configuration object.

    Raises:
        ConfigError: If file not found, invalid JSON, or schema validation fails.
    """
    if not path.exists():
        # Optional: return empty config if not found?
        # The task says "Raise ConfigError for file not found" in labs_loader,
        # following the same pattern.
        raise ConfigError(f"Ficheiro de configuração não encontrado: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON inválido em {path}: {e}")
    except Exception as e:
        raise ConfigError(f"Erro ao ler {path}: {e}")

    try:
        # Pydantic validation
        config = LocationsConfig(root=data)
        return config
    except Exception as e:
        raise ConfigError(f"Falha na validação do schema para {path}: {e}")


def map_location(name: str, aliases: dict[str, str]) -> str:
    """
    Maps a raw location name to its alias using case-insensitive word-boundary matching.

    Args:
        name (str): Raw location name from Infoprex file.
        aliases (Dict[str, str]): Dictionary of search terms to aliases.

    Returns:
        str: Mapped alias (Title Case) or the original name in Title Case if no match.
    """
    if not name:
        return ""

    name_lower = name.lower().strip()

    # 1. Exact match (case-insensitive)
    for term, alias in aliases.items():
        if term.lower() == name_lower:
            return alias.title()

    # 2. Word boundary matching
    # re.search(r'\b' + term + r'\b', name_lower)
    matches = []
    for term, alias in aliases.items():
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, name_lower):
            matches.append(alias.title())

    if matches:
        if len(matches) > 1:
            logger.warning(
                "Múltiplas correspondências de localização para '%s': %s. Usando a primeira: %s",
                name,
                matches,
                matches[0],
            )
        return matches[0]

    # 3. Fallback
    return name.title()
