"""
tests/unit/test_column_ordering.py — TASK-36.

Garante que o invariante posicional de colunas é mantido (ADR-004).
"""

import pandas as pd
import pytest

from orders_master.aggregation.aggregator import reorder_columns
from orders_master.constants import Columns


def test_tuni_anchor_invariant_grouped() -> None:
    """Garante que em vista agrupada, o bloco de vendas precede T Uni."""
    # Simular DataFrame com colunas base + meses dinâmicos
    df = pd.DataFrame(
        {
            Columns.CODIGO: [1],
            Columns.DESIGNACAO: ["A"],
            Columns.MARCA: ["M"],
            "Jan-24": [10],
            "Fev-24": [20],
            "Mar-24": [30],
            "Abr-24": [40],
            "Maio-24": [50],
            Columns.T_UNI: [100],
            Columns.STOCK: [5],
            Columns.PVP_MEDIO: [10.0],
            Columns.P_CUSTO_MEDIO: [5.0],
        }
    )

    df_reordered = reorder_columns(df, detailed=False)

    # Obter índice de T Uni
    idx_tuni = df_reordered.columns.get_loc(Columns.T_UNI)

    # De acordo com §5.4.1, o bloco de 4 vendas (janela base)
    # deve estar imediatamente antes de T Uni.
    # Se offset=1 (mês actual), então T Uni - 1 deve ser Maio-24.

    # Verificação: T Uni deve estar APÓS os meses dinâmicos
    # No reorder_columns actual, T Uni vem antes dos meses dinâmicos (bug detectado)
    assert df_reordered.columns[idx_tuni - 1] == "Maio-24"
    assert df_reordered.columns[idx_tuni - 2] == "Abr-24"
    assert df_reordered.columns[idx_tuni - 3] == "Mar-24"
    assert df_reordered.columns[idx_tuni - 4] == "Fev-24"


def test_tuni_anchor_invariant_detailed() -> None:
    """Garante que em vista detalhada, o bloco de vendas precede T Uni."""
    df = pd.DataFrame(
        {
            Columns.CODIGO: [1],
            Columns.DESIGNACAO: ["A"],
            Columns.MARCA: ["M"],
            Columns.LOCALIZACAO: ["F1"],
            "Jan-24": [10],
            "Fev-24": [20],
            "Mar-24": [30],
            "Abr-24": [40],
            "Maio-24": [50],
            Columns.T_UNI: [100],
            Columns.STOCK: [5],
            Columns.PVP: [10.0],
            Columns.P_CUSTO: [5.0],
            Columns.DUC: ["100"],
            Columns.DTVAL: ["2026-01-01"],
        }
    )

    df_reordered = reorder_columns(df, detailed=True)
    idx_tuni = df_reordered.columns.get_loc(Columns.T_UNI)

    assert df_reordered.columns[idx_tuni - 1] == "Maio-24"
    assert df_reordered.columns[idx_tuni - 2] == "Abr-24"
