"""
orders_master/config/presets_loader.py — Carregamento de configurações de pesos.
"""

import logging
from pathlib import Path
import yaml
from pydantic import RootModel, ValidationError

logger = logging.getLogger(__name__)

class PresetsConfig(RootModel[dict[str, dict[str, list[float]]]]):
    """Schema para validação dos presets de pesos."""

def load_presets_config(path: str | Path) -> dict[str, list[float]]:
    """
    Lê o ficheiro YAML de presets e valida a estrutura.
    Retorna o dicionário de presets (nome -> lista de 4 pesos).
    """
    path = Path(path)
    default_presets: dict[str, list[float]] = {
        "Conservador": [0.5, 0.3, 0.15, 0.05],
        "Padrão": [0.4, 0.3, 0.2, 0.1],
        "Agressivo": [0.25, 0.25, 0.25, 0.25],
    }

    if not path.exists():
        logger.warning(f"Ficheiro de presets não encontrado em {path}. Usando padrões fixos.")
        return default_presets

    try:
        with open(path, encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
        
        if not isinstance(raw_data, dict) or "presets" not in raw_data:
            raise ValueError("Estrutura inválida ou chave 'presets' não encontrada no ficheiro YAML.")
            
        presets = raw_data["presets"]
        if not isinstance(presets, dict):
            raise ValueError("'presets' deve ser um dicionário.")

        valid_presets: dict[str, list[float]] = {}
        for name, weights in presets.items():
            if not isinstance(weights, list) or len(weights) != 4:
                 logger.error(f"Preset '{name}' deve ser uma lista de exactamente 4 pesos. Ignorado.")
                 continue
            valid_presets[str(name)] = [float(w) for w in weights]
            if abs(sum(valid_presets[str(name)]) - 1.0) > 1e-3:
                 logger.warning(f"Soma dos pesos no preset '{name}' não é 1.0 ({sum(valid_presets[str(name)])}).")

        return valid_presets

    except (yaml.YAMLError, ValidationError, ValueError) as e:
        logger.error(f"Erro ao carregar presets de {path}: {e}")
        return default_presets
