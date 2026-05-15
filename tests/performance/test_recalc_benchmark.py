"""
tests/performance/test_recalc_benchmark.py — TASK-39.

Benchmarks de performance para validar NFR-P2 (recálculo <= 500ms).
"""

import pandas as pd
import pytest
from orders_master.app_services.recalc_service import recalculate_proposal
from orders_master.app_services.session_state import ScopeContext
from orders_master.constants import Columns

@pytest.fixture
def large_aggregated_df() -> pd.DataFrame:
    """Gera um DataFrame com 5.000 produtos para benchmark."""
    n = 5000
    data = {
        Columns.CODIGO: range(2000001, 2000001 + n),
        Columns.LOCALIZACAO: ["FARMACIA_A"] * n,
        Columns.DESIGNACAO: ["PRODUTO TESTE"] * n,
        Columns.MARCA: ["MARCA X"] * n,
        "JAN": [5] * n,
        "FEV": [5] * n,
        "MAR": [5] * n,
        "ABR": [5] * n,
        "MAI": [5] * n,
        "JUN": [5] * n,
        "JUL": [5] * n,
        "AGO": [5] * n,
        Columns.T_UNI: [20] * n,
        Columns.STOCK: [10] * n,
    }
    return pd.DataFrame(data)

@pytest.fixture
def df_master_products(large_aggregated_df) -> pd.DataFrame:
    """Mock do df_master_products."""
    return large_aggregated_df[[Columns.CODIGO, Columns.DESIGNACAO, Columns.MARCA]].copy()

@pytest.mark.benchmark(group="recalc")
def test_recalculate_proposal_benchmark(benchmark, large_aggregated_df, df_master_products):
    """
    Benchmark do recálculo de proposta para 5.000 produtos.
    Target: <= 500ms.
    """
    scope = ScopeContext()
    
    def run_recalc():
        return recalculate_proposal(
            df_detailed=large_aggregated_df,
            detailed_view=False,
            df_master_products=df_master_products,
            months=2.0,
            weights=(0.4, 0.3, 0.2, 0.1),
            use_previous_month=False,
            scope_context=scope
        )

    result = benchmark(run_recalc)
    assert not result.empty
    assert Columns.PROPOSTA in result.columns
