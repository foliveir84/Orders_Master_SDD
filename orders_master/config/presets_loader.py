"""
orders_master/config/presets_loader.py — Carregamento de configurações de pesos.
"""

import logging
from pathlib import Path
import yaml
from pydantic import RootModel, ValidationError

logger = logging.getLogger(__name__)

class PresetsConfig(RootModel):
    """Schema para validação dos presets de pesos."""
    root: dict[str, dict[str, list[float]]]

def load_presets_config(path: str | Path) -> dict[str, list[float]]:
    """
    Lê o ficheiro YAML de presets e valida a estrutura.
    Retorna o dicionário de presets (nome -> lista de 4 pesos).
    """
    path = Path(path)
    if not path.exists():
        logger.warning(f"Ficheiro de presets não encontrado em {path}. Usando padrões fixos.")
        return {
            "Conservador": [0.5, 0.3, 0.15, 0.05],
            "Padrão": [0.4, 0.3, 0.2, 0.1],
            "Agressivo": [0.25, 0.25, 0.25, 0.25],
        }

    try:
        with open(path, encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
        
        # O ficheiro tem formato { presets: { ... } }
        # Mas o RootModel espera o dict directo se for RootModel(dict)
        # Vamos validar a estrutura
        if "presets" not in raw_data:
            raise ValueError("Chave 'presets' não encontrada no ficheiro YAML.")
            
        presets = raw_data["presets"]
        for name, weights in presets.items():
            if len(weights) != 4:
                 logger.error(f"Preset '{name}' deve ter exactamente 4 pesos. Ignorado.")
                 continue
            if abs(sum(weights) - 1.0) > 1e-3:
                 logger.warning(f"Soma dos pesos no preset '{name}' não é 1.0 ({sum(weights)}).")

        return presets

    except (yaml.YAMLError, ValidationError, ValueError) as e:
        logger.error(f"Erro ao carregar presets de {path}: {e}")
        return {
            "Conservador": [0.5, 0.3, 0.15, 0.05],
            "Padrão": [0.4, 0.3, 0.2, 0.1],
            "Agressivo": [0.25, 0.25, 0.25, 0.25],
        }
