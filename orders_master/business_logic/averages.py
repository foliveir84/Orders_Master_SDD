import pandas as pd
import yaml
from typing import Dict, Tuple, List
from pathlib import Path

def select_window(df: pd.DataFrame, use_previous_month: bool, weights_len: int = 4) -> List[str]:
    """
    Helper para extrair nomes das colunas-alvo usando a âncora 'T Uni'.
    """
    if 'T Uni' not in df.columns:
        raise ValueError("A coluna âncora 'T Uni' não está presente no DataFrame.")
        
    idx_tuni = df.columns.get_loc('T Uni')
    offset = 2 if use_previous_month else 1
    
    col_indices = [idx_tuni - offset - i for i in range(weights_len)]
    
    if any(idx < 0 for idx in col_indices):
        raise AssertionError("A janela de cálculo ultrapassa o início do histórico disponível.")
        
    cols = [df.columns[idx] for idx in col_indices]
    return cols

def weighted_average(df: pd.DataFrame, weights: Tuple[float, ...], use_previous_month: bool) -> pd.Series:
    """
    Calcula a média ponderada baseada nos pesos e no toggle do mês anterior.
    """
    assert abs(sum(weights) - 1.0) < 1e-3, f"A soma dos pesos deve ser 1.0 (encontrado {sum(weights)})"
    
    if df.empty:
        return pd.Series(dtype=float)
        
    cols = select_window(df, use_previous_month, len(weights))
    
    return df[cols].fillna(0).dot(weights)

def load_presets(path: str | Path) -> Dict[str, Tuple[float, ...]]:
    """
    Loader de config/presets.yaml.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro de presets não encontrado: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    presets = data.get('presets', {})
    
    result = {}
    for name, weights in presets.items():
        result[name] = tuple(float(w) for w in weights)
        
    return result
