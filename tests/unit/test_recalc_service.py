"""
Testes unitários para recalculate_proposal — TASK-23.
"""

import time

import pandas as pd
import pytest

from orders_master.app_services.recalc_service import recalculate_proposal
from orders_master.constants import Columns, GroupLabels


@pytest.fixture
def sample_detailed_df() -> pd.DataFrame:
    """Fixture com 2 lojas, 1 produto, 5 meses de vendas."""
    data = [
        {
            Columns.CODIGO: 2001,
            Columns.DESIGNACAO: "Produto A",
            Columns.LOCALIZACAO: "FAR_A",
            Columns.STOCK: 10,
            "V0": 10, "V1": 10, "V2": 10, "V3": 10, "V4": 10,
            "T Uni": 50,
            Columns.PVP: 10.0,
            Columns.P_CUSTO: 5.0,
        },
        {
            Columns.CODIGO: 2001,
            Columns.DESIGNACAO: "Produto A",
            Columns.LOCALIZACAO: "FAR_B",
            Columns.STOCK: 5,
            "V0": 5, "V1": 5, "V2": 5, "V3": 5, "V4": 5,
            "T Uni": 25,
            Columns.PVP: 10.0,
            Columns.P_CUSTO: 5.0,
        },
    ]
    return pd.DataFrame(data)


@pytest.fixture
def master_products() -> pd.DataFrame:
    return pd.DataFrame({
        Columns.CODIGO: [2001],
        Columns.DESIGNACAO: ["Produto A"],
        Columns.MARCA: ["Marca X"],
    })


def test_recalc_months_doubles_proposal(sample_detailed_df, master_products) -> None:
    """Alterar meses de 1.0 para 2.0 deve duplicar a proposta aprox."""
    weights = (0.25, 0.25, 0.25, 0.25)
    
    # Meses = 1.0 -> Proposta = Media * 1 - Stock
    # Loja A: Media = 10, Stock = 10 -> Proposta = 0
    # Loja B: Media = 5, Stock = 5 -> Proposta = 0
    # Total: 0
    res1 = recalculate_proposal(sample_detailed_df, False, master_products, 1.0, weights)
    assert res1[Columns.PROPOSTA].iloc[0] == 0
    
    # Meses = 2.0 -> Proposta = Media * 2 - Stock
    # Loja A: Media = 10, Stock = 10 -> Proposta = 10
    # Loja B: Media = 5, Stock = 5 -> Proposta = 5
    # Total: 15
    res2 = recalculate_proposal(sample_detailed_df, False, master_products, 2.0, weights)
    assert res2[Columns.PROPOSTA].iloc[0] == 15


def test_recalc_detailed_view(sample_detailed_df, master_products) -> None:
    """Verifica que detailed_view=True retorna linhas por loja + Grupo."""
    weights = (1.0, 0, 0, 0)
    res = recalculate_proposal(sample_detailed_df, True, master_products, 1.0, weights)
    
    # 2 lojas + 1 grupo = 3 linhas
    assert len(res) == 3
    assert GroupLabels.GROUP_ROW in res[Columns.LOCALIZACAO].values


def test_recalc_performance(sample_detailed_df, master_products) -> None:
    """Performance deve ser < 500ms para 1000 linhas (simulado com repetição)."""
    # Criar 1000 linhas repetindo a fixture
    large_df = pd.concat([sample_detailed_df] * 500, ignore_index=True)
    weights = (0.4, 0.3, 0.2, 0.1)
    
    start = time.perf_counter()
    recalculate_proposal(large_df, False, master_products, 1.0, weights)
    end = time.perf_counter()
    
    duration_ms = (end - start) * 1000
    assert duration_ms < 500


def test_recalc_weights_influence(sample_detailed_df, master_products) -> None:
    """Alterar pesos deve alterar a média ponderada."""
    # Vendas: V1=10, V2=10, V3=10, V4=10 (Ignora V0 por default offset=1)
    # Weights[0] mapeia para a coluna imediatamente antes de T Uni (V4)
    df = sample_detailed_df.copy()
    df.loc[0, "V4"] = 20
    df.loc[1, "V4"] = 20
    
    # Pesos (1.0, 0, 0, 0) -> Foca em V4
    res1 = recalculate_proposal(df, False, master_products, 1.0, (1.0, 0, 0, 0))
    # Loja A: 20, Loja B: 20 -> Total 40
    assert res1[Columns.MEDIA].iloc[0] == 40
    
    # Pesos (0, 1.0, 0, 0) -> Foca em V3
    res2 = recalculate_proposal(df, False, master_products, 1.0, (0, 1.0, 0, 0))
    # Loja A: 10, Loja B: 5 -> Total 15
    assert res2[Columns.MEDIA].iloc[0] == 15
