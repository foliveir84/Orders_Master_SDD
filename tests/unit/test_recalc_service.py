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
    """
    Fixture com 2 lojas, 1 produto, 5 meses de vendas.
    Ordem real (ADR-004): V4, V3, V2, V1, V0, T Uni.
    V0 é o mês mais recente (Mês Atual).
    Indices: V4(4), V3(5), V2(6), V1(7), V0(8), T Uni(9).
    """
    data = [
        {
            Columns.CODIGO: 2001,
            Columns.DESIGNACAO: "Produto A",
            Columns.LOCALIZACAO: "FAR_A",
            Columns.STOCK: 10,
            "V4": 10,
            "V3": 10,
            "V2": 10,
            "V1": 10,
            "V0": 10,
            "T Uni": 50,
            Columns.PVP: 10.0,
            Columns.P_CUSTO: 5.0,
        },
        {
            Columns.CODIGO: 2001,
            Columns.DESIGNACAO: "Produto A",
            Columns.LOCALIZACAO: "FAR_B",
            Columns.STOCK: 5,
            "V4": 5,
            "V3": 5,
            "V2": 5,
            "V1": 5,
            "V0": 5,
            "T Uni": 25,
            Columns.PVP: 10.0,
            Columns.P_CUSTO: 5.0,
        },
    ]
    return pd.DataFrame(data)


@pytest.fixture
def df_master_products() -> pd.DataFrame:
    return pd.DataFrame(
        {
            Columns.CODIGO: [2001],
            Columns.DESIGNACAO: ["Produto A"],
            Columns.MARCA: ["Marca X"],
        }
    )


def test_recalc_months_doubles_proposal(sample_detailed_df, df_master_products) -> None:
    """Alterar meses de 1.0 para 2.0 deve duplicar a proposta aprox."""
    weights = (0.25, 0.25, 0.25, 0.25)

    # Meses = 1.0 -> Proposta = Media * 1 - Stock
    # Loja A: Media = 10, Stock = 10 -> Proposta = 0
    # Loja B: Media = 5, Stock = 5 -> Proposta = 0
    # Total: 0
    res1 = recalculate_proposal(sample_detailed_df, False, df_master_products, 1.0, weights)
    assert res1[Columns.PROPOSTA].iloc[0] == 0

    # Meses = 2.0 -> Proposta = Media * 2 - Stock
    # Loja A: Media = 10, Stock = 10 -> Proposta = 10
    # Loja B: Media = 5, Stock = 5 -> Proposta = 5
    # Total: 15
    res2 = recalculate_proposal(sample_detailed_df, False, df_master_products, 2.0, weights)
    assert res2[Columns.PROPOSTA].iloc[0] == 15


def test_recalc_detailed_view(sample_detailed_df, df_master_products) -> None:
    """Verifica que detailed_view=True retorna linhas por loja + Grupo."""
    weights = (1.0, 0, 0, 0)
    res = recalculate_proposal(sample_detailed_df, True, df_master_products, 1.0, weights)

    # 2 lojas + 1 grupo = 3 linhas
    assert len(res) == 3
    assert GroupLabels.GROUP_ROW in res[Columns.LOCALIZACAO].values


def test_recalc_performance(sample_detailed_df, df_master_products) -> None:
    """Performance deve ser < 500ms para 1000 linhas (simulado com repetição)."""
    # Criar 1000 linhas repetindo a fixture
    large_df = pd.concat([sample_detailed_df] * 500, ignore_index=True)
    weights = (0.4, 0.3, 0.2, 0.1)

    start = time.perf_counter()
    recalculate_proposal(large_df, False, df_master_products, 1.0, weights)
    end = time.perf_counter()

    duration_ms = (end - start) * 1000
    assert duration_ms < 500


def test_recalc_weights_influence(sample_detailed_df, df_master_products) -> None:
    """Alterar pesos deve alterar a média ponderada."""
    # Ordem: V4, V3, V2, V1, V0, T Uni
    # Janela default (offset=1): V0, V1, V2, V3. (V4 é ignorado).
    # weights[0] é o mais recente na janela (V0).
    df = sample_detailed_df.copy()
    df.loc[0, "V0"] = 20
    df.loc[1, "V0"] = 20

    # Pesos (1.0, 0, 0, 0) -> Foca em V0
    res1 = recalculate_proposal(df, False, df_master_products, 1.0, (1.0, 0, 0, 0))
    # Loja A: 20, Loja B: 20 -> Total 40
    assert res1[Columns.MEDIA].iloc[0] == 40

    # Pesos (0, 0, 0, 1.0) -> Foca em V3
    res2 = recalculate_proposal(df, False, df_master_products, 1.0, (0, 0, 0, 1.0))
    # Loja A: 10, Loja B: 5 -> Total 15
    assert res2[Columns.MEDIA].iloc[0] == 15


def test_recalc_brand_filtering(sample_detailed_df) -> None:
    """Verifica que o filtro por marca reduz os resultados."""
    master = pd.DataFrame(
        {
            Columns.CODIGO: [2001, 3001],
            Columns.DESIGNACAO: ["Prod A", "Prod B"],
            Columns.MARCA: ["Marca X", "Marca Y"],
        }
    )
    # Adicionar produto 3001 ao detailed_df
    row_b = sample_detailed_df.iloc[0].copy()
    row_b[Columns.CODIGO] = 3001
    df = pd.concat([sample_detailed_df, pd.DataFrame([row_b])], ignore_index=True)

    weights = (1.0, 0, 0, 0)

    # Sem filtro -> 2 produtos
    res1 = recalculate_proposal(df, False, master, 1.0, weights)
    assert len(res1) == 2

    # Com filtro -> 1 produto
    res2 = recalculate_proposal(df, False, master, 1.0, weights, marcas=["Marca X"])
    assert len(res2) == 1
    assert res2[Columns.MARCA].iloc[0] == "Marca X"


def test_recalc_use_previous_month(sample_detailed_df, df_master_products) -> None:
    """Toggle use_previous_month deve deslocar a janela de média."""
    # Ordem: V4, V3, V2, V1, V0, T Uni
    # V0 é o mais recente.
    df = sample_detailed_df.copy()
    df.loc[0, "V0"] = 100
    df.loc[1, "V0"] = 100

    # 1. use_previous_month=False -> Inclui V0.
    res1 = recalculate_proposal(df, False, df_master_products, 1.0, (1.0, 0, 0, 0), use_previous_month=False)
    # weights[0] é V0. V0=100 -> Total 200
    assert res1[Columns.MEDIA].iloc[0] == 200

    # 2. use_previous_month=True (Ignorar mês corrente) -> Janela [V4, V3, V2, V1]. Pula V0.
    res2 = recalculate_proposal(df, False, df_master_products, 1.0, (1.0, 0, 0, 0), use_previous_month=True)
    # weights[0] é V1. V1=10 -> Total 15
    assert res2[Columns.MEDIA].iloc[0] == 15


def test_recalc_scope_context_update(sample_detailed_df, df_master_products) -> None:
    """Verifica se o ScopeContext é actualizado com as métricas correctas."""
    from dataclasses import dataclass

    @dataclass
    class MockScopeContext:
        n_produtos: int = 0
        n_farmacias: int = 0
        meses: float = 0.0
        modo: str = ""
        primeiro_mes: str = ""
        ultimo_mes: str = ""

    ctx = MockScopeContext()
    recalculate_proposal(sample_detailed_df, False, df_master_products, 2.5, (0.4, 0.3, 0.2, 0.1), scope_context=ctx)

    assert ctx.n_produtos == 1
    assert ctx.n_farmacias == 2
    assert ctx.meses == 2.5
    assert ctx.modo == "Agrupada"
    # Janela default (offset=1): V3, V2, V1, V0.
    # primeiro_mes (mais antigo) = V3.
    # ultimo_mes (mais recente na janela) = V0.
    assert ctx.primeiro_mes == "V3"
    assert ctx.ultimo_mes == "V0"
