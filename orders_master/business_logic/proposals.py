"""
Fórmula base de proposta — TASK-20.

Implementa ``compute_base_proposal`` seguindo PRD §5.4.3:
    Proposta = round(Media × meses_previsao − STOCK)

Propostas negativas são mantidas (stock excedente é informação valiosa).
"""

import pandas as pd

from orders_master.constants import Columns


def compute_base_proposal(df: pd.DataFrame, meses_previsao: float) -> pd.DataFrame:
    """
    Calcula a proposta base de encomenda para cada linha do DataFrame.

    Fórmula: ``Proposta = round(Media × meses_previsao − STOCK)``

    Propostas negativas são preservadas — indicam excedente de stock e
    constituem informação relevante para o utilizador (não se faz clamp a zero).

    Args:
        df: DataFrame com pelo menos as colunas ``Media`` e ``STOCK``.
        meses_previsao: Número de meses de previsão (ex: 1.0, 1.5, 2.0).

    Returns:
        DataFrame com a coluna ``Proposta`` adicionada (valores inteiros).

    Raises:
        KeyError: Se as colunas ``Media`` ou ``STOCK`` não existirem.
    """
    df_out = df.copy()
    df_out[Columns.PROPOSTA] = (
        (df_out[Columns.MEDIA] * meses_previsao - df_out[Columns.STOCK]).round(0).astype(int)
    )
    return df_out


def compute_shortage_proposal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a proposta para produtos em rutura (falta de stock).

    Apenas linhas com ``TimeDelta`` não-nulo são processadas. A fórmula de rutura
    sobrescreve o valor anterior da coluna ``Proposta``.

    Fórmula: ``Proposta = round((Media / 30) × TimeDelta − STOCK)``

    Args:
        df: DataFrame com colunas ``Media``, ``STOCK``, ``Proposta`` e ``TimeDelta``.

    Returns:
        DataFrame com a coluna ``Proposta`` actualizada onde aplicável.
    """
    df_out = df.copy()
    if Columns.TIME_DELTA not in df_out.columns:
        return df_out

    mask = df_out[Columns.TIME_DELTA].notna()
    if not mask.any():
        return df_out

    # Cálculo da proposta de rutura
    # round(0) garante arredondamento para o inteiro mais próximo
    df_out.loc[mask, Columns.PROPOSTA] = (
        (
            (df_out.loc[mask, Columns.MEDIA] / 30.0) * df_out.loc[mask, Columns.TIME_DELTA]
            - df_out.loc[mask, Columns.STOCK]
        )
        .round(0)
        .astype(int)
    )

    return df_out
