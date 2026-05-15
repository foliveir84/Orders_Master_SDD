import json
import logging
import os
from pathlib import Path

from pydantic import RootModel, model_validator

from orders_master.exceptions import ConfigError
from orders_master.integrations.cache_decorator import cache_decorator

logger = logging.getLogger(__name__)


class LabsConfig(RootModel[dict[str, list[str]]]):
    """
    Schema for laboratorios.json validation.
    Maps Laboratory Name -> List of CLA codes.
    """

    root: dict[str, list[str]]

    @model_validator(mode="after")
    def validate_labs(self) -> "LabsConfig":
        """
        Validates laboratory names and CLA codes.
        Performs automatic deduplication of codes and warns about duplicates.
        """
        new_root = {}
        all_codes: dict[str, list[str]] = {}

        for lab_name, cla_codes in self.root.items():
            # Validate Lab Name: min length 2, starts with uppercase
            if len(lab_name) < 2:
                raise ValueError(
                    f"O nome do laboratório '{lab_name}' deve ter pelo menos 2 caracteres."
                )
            if not lab_name[0].isupper():
                raise ValueError(
                    f"O nome do laboratório '{lab_name}' deve começar com uma letra maiúscula."
                )

            # Validate CLA codes: alphanumeric, max 10 chars
            seen_codes = set()
            unique_codes = []
            for code in cla_codes:
                if not code.isalnum():
                    logger.warning(
                        "O código CLA '%s' no laboratório '%s' não é alfanumérico.",
                        code,
                        lab_name,
                    )
                if len(code) > 10:
                    raise ValueError(
                        f"O código CLA '{code}' no laboratório '{lab_name}' excede 10 caracteres."
                    )

                if code in seen_codes:
                    logger.warning(
                        "Código CLA duplicado '%s' encontrado no laboratório '%s'. Removendo duplicado.",
                        code,
                        lab_name,
                    )
                else:
                    seen_codes.add(code)
                    unique_codes.append(code)

                    # Track codes across all labs for warnings
                    if code in all_codes:
                        all_codes[code].append(lab_name)
                    else:
                        all_codes[code] = [lab_name]

            new_root[lab_name] = unique_codes

        # Warn about same CLA in multiple labs
        for code, labs in all_codes.items():
            if len(labs) > 1:
                logger.warning(
                    "O código CLA '%s' aparece em múltiplos laboratórios: %s", code, labs
                )

        # Update root with cleaned data
        object.__setattr__(self, "root", new_root)
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


@cache_decorator()
def load_labs(mtime: float, path: Path = Path("config/laboratorios.json")) -> LabsConfig:
    """
    Loads and validates laboratorios.json.
    Uses mtime to invalidate cache in Streamlit.

    Args:
        mtime (float): File modification time (used as cache key).
        path (Path): Path to the JSON file.

    Returns:
        LabsConfig: Validated configuration object.

    Raises:
        ConfigError: If file not found, invalid JSON, or schema validation fails.
    """
    if not path.exists():
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
        config = LabsConfig(root=data)
        return config
    except Exception as e:
        raise ConfigError(f"Falha na validação do schema para {path}: {e}")
