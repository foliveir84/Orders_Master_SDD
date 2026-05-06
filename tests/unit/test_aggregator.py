"""
Testes unitários do motor de agregação — TASK-14.
Cobre todos os critérios de aceitação definidos em tasks.md.

Nota: Códigos que comecem por '1' são considerados locais e descartados (PRD §5.1.10).
      Os fixtures usam códigos que começam por '2', '3', etc.
"""
import inspect

import pandas as pd
import pytest

from orders_master.aggregation.aggregator import aggregate, build_master_products, reorder_columns
from orders_master.constants import Columns, GroupLabels


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SALES_COLS = ["JAN", "FEV", "MAR", "ABR"]

# Use codes NOT starting with '1' (those are local codes and get discarded)
CODE_A = 2001
CODE_B = 3001
CODE_C = 4001


def make_df(rows: list[dict]) -> pd.DataFrame:
    """Cria um DataFrame de ingestão mínimo para os testes."""
    base: dict = {
        Columns.CODIGO: CODE_A,
        Columns.DESIGNACAO: "PRODUTO TESTE",
        Columns.LOCALIZACAO: "FARMACIA A",
        Columns.STOCK: 10,
        Columns.PVP: 5.00,
        Columns.P_CUSTO: 3.00,
        Columns.DUC: "01/2026",
        Columns.DTVAL: "12/2026",
        Columns.T_UNI: 20,
        Columns.PRICE_ANOMALY: False,
    }
    records = []
    for row in rows:
        r = {**base, **row}
        for sc in SALES_COLS:
            r.setdefault(sc, 5)
        records.append(r)
    return pd.DataFrame(records)


@pytest.fixture
def master() -> pd.DataFrame:
    """Master products com três produtos."""
    return pd.DataFrame(
        {
            Columns.CODIGO: [CODE_A, CODE_B, CODE_C],
            Columns.DESIGNACAO: ["Produto Alfa", "Produto Beta", "Produto Gama"],
            Columns.MARCA: ["Marca A", "Marca B", "Marca C"],
        }
    )


@pytest.fixture
def df_two_stores() -> pd.DataFrame:
    """Produto CODE_A em duas lojas, produto CODE_C em uma loja."""
    return make_df(
        [
            {Columns.CODIGO: CODE_A, Columns.LOCALIZACAO: "FAR_A", Columns.STOCK: 5, Columns.T_UNI: 10},
            {Columns.CODIGO: CODE_A, Columns.LOCALIZACAO: "FAR_B", Columns.STOCK: 3, Columns.T_UNI: 8},
            {Columns.CODIGO: CODE_C, Columns.LOCALIZACAO: "FAR_A", Columns.STOCK: 2, Columns.T_UNI: 4},
        ]
    )


# ---------------------------------------------------------------------------
# Tests — Vista Agrupada (detailed=False)
# ---------------------------------------------------------------------------


def test_grouped_one_row_per_code(df_two_stores: pd.DataFrame, master: pd.DataFrame) -> None:
    result = aggregate(df_two_stores, detailed=False, master_products=master)
    assert result[Columns.CODIGO].nunique() == len(result)


def test_grouped_sales_summed(df_two_stores: pd.DataFrame, master: pd.DataFrame) -> None:
    result = aggregate(df_two_stores, detailed=False, master_products=master)
    row_a = result[result[Columns.CODIGO] == CODE_A].iloc[0]
    assert row_a[Columns.STOCK] == 8
    assert row_a[Columns.T_UNI] == 18


def test_grouped_pvp_medio_rounded(master: pd.DataFrame) -> None:
    """PVP_Médio deve ser a média dos PVPs (excluindo anomalias), arredondado a 2 casas."""
    df = make_df(
        [
            {Columns.CODIGO: CODE_A, Columns.LOCALIZACAO: "A", Columns.PVP: 5.111, Columns.PRICE_ANOMALY: False},
            {Columns.CODIGO: CODE_A, Columns.LOCALIZACAO: "B", Columns.PVP: 3.333, Columns.PRICE_ANOMALY: False},
        ]
    )
    result = aggregate(df, detailed=False, master_products=master)
    pvp_medio = result.loc[result[Columns.CODIGO] == CODE_A, Columns.PVP_MEDIO].iloc[0]
    assert round(pvp_medio, 2) == pvp_medio  # rounded to 2 decimals
    assert pvp_medio == pytest.approx((5.111 + 3.333) / 2, abs=0.01)


def test_grouped_pvp_renamed(df_two_stores: pd.DataFrame, master: pd.DataFrame) -> None:
    result = aggregate(df_two_stores, detailed=False, master_products=master)
    assert Columns.PVP_MEDIO in result.columns
    assert Columns.P_CUSTO_MEDIO in result.columns
    assert Columns.PVP not in result.columns
    assert Columns.P_CUSTO not in result.columns


# ---------------------------------------------------------------------------
# Tests — Vista Detalhada (detailed=True)
# ---------------------------------------------------------------------------


def test_detailed_has_grupo_row(df_two_stores: pd.DataFrame, master: pd.DataFrame) -> None:
    result = aggregate(df_two_stores, detailed=True, master_products=master)
    grupo_rows = result[result[Columns.LOCALIZACAO] == GroupLabels.GROUP_ROW]
    # One Grupo row per unique CÓDIGO
    unique_codes = df_two_stores[Columns.CODIGO].nunique()
    assert len(grupo_rows) == unique_codes


def test_detailed_n_lines_per_code_plus_grupo(df_two_stores: pd.DataFrame, master: pd.DataFrame) -> None:
    result = aggregate(df_two_stores, detailed=True, master_products=master)
    # CODE_A: 2 stores + 1 Grupo = 3 rows
    rows_a = result[result[Columns.CODIGO] == CODE_A]
    assert len(rows_a) == 3


def test_detailed_grupo_row_last(df_two_stores: pd.DataFrame, master: pd.DataFrame) -> None:
    result = aggregate(df_two_stores, detailed=True, master_products=master)
    for codigo in df_two_stores[Columns.CODIGO].unique():
        code_rows = result[result[Columns.CODIGO] == codigo]
        # Last row should be Grupo
        assert code_rows.iloc[-1][Columns.LOCALIZACAO] == GroupLabels.GROUP_ROW


def test_detailed_sort_key_values(df_two_stores: pd.DataFrame, master: pd.DataFrame) -> None:
    result = aggregate(df_two_stores, detailed=True, master_products=master)
    grupo_mask = result[Columns.LOCALIZACAO] == GroupLabels.GROUP_ROW
    assert (result.loc[grupo_mask, Columns.SORT_KEY] == 1).all()
    assert (result.loc[~grupo_mask, Columns.SORT_KEY] == 0).all()


# ---------------------------------------------------------------------------
# Tests — Filtros e Anomalias
# ---------------------------------------------------------------------------


def test_zombie_rows_removed(master: pd.DataFrame) -> None:
    """Linhas com STOCK=0 e T_UNI=0 devem ser removidas."""
    df = make_df(
        [
            {Columns.CODIGO: CODE_A, Columns.STOCK: 0, Columns.T_UNI: 0},
            {Columns.CODIGO: CODE_C, Columns.STOCK: 5, Columns.T_UNI: 10},
        ]
    )
    result = aggregate(df, detailed=False, master_products=master)
    assert CODE_A not in result[Columns.CODIGO].values
    assert CODE_C in result[Columns.CODIGO].values


def test_zombie_aggregated_removed(master: pd.DataFrame) -> None:
    """Código com stock e vendas zero em TODAS as lojas deve ser removido pós-agregação."""
    df = make_df(
        [
            {Columns.CODIGO: CODE_A, Columns.LOCALIZACAO: "A", Columns.STOCK: 0, Columns.T_UNI: 0},
            {Columns.CODIGO: CODE_A, Columns.LOCALIZACAO: "B", Columns.STOCK: 0, Columns.T_UNI: 0},
            {Columns.CODIGO: CODE_C, Columns.STOCK: 5, Columns.T_UNI: 10},
        ]
    )
    result = aggregate(df, detailed=False, master_products=master)
    assert CODE_A not in result[Columns.CODIGO].values
    assert CODE_C in result[Columns.CODIGO].values


def test_price_anomaly_excluded_from_average(master: pd.DataFrame) -> None:
    """Linhas com price_anomaly=True não devem influenciar a média PVP."""
    df = make_df(
        [
            {Columns.CODIGO: CODE_A, Columns.PVP: 10.00, Columns.PRICE_ANOMALY: False},
            {Columns.CODIGO: CODE_A, Columns.PVP: 0.00, Columns.PRICE_ANOMALY: True},  # anomaly
        ]
    )
    result = aggregate(df, detailed=False, master_products=master)
    pvp_medio = result.loc[result[Columns.CODIGO] == CODE_A, Columns.PVP_MEDIO].iloc[0]
    # Only the non-anomaly row should count: PVP_Médio should be 10.00, not 5.00
    assert pvp_medio == pytest.approx(10.00, abs=0.01)


# ---------------------------------------------------------------------------
# Tests — Master Products e Marca
# ---------------------------------------------------------------------------


def test_master_products_injects_designacao_and_marca(
    df_two_stores: pd.DataFrame, master: pd.DataFrame
) -> None:
    result = aggregate(df_two_stores, detailed=False, master_products=master)
    row = result[result[Columns.CODIGO] == CODE_A].iloc[0]
    assert row[Columns.DESIGNACAO] == "Produto Alfa"
    assert row[Columns.MARCA] == "Marca A"


def test_build_master_products_without_brands() -> None:
    df = make_df(
        [
            {Columns.CODIGO: CODE_A, Columns.DESIGNACAO: "Produto Alfa"},
        ]
    )
    master = build_master_products(df)
    assert Columns.CODIGO in master.columns
    assert Columns.DESIGNACAO in master.columns
    assert Columns.MARCA in master.columns
    assert master.iloc[0][Columns.MARCA] == ""


def test_build_master_products_with_brands() -> None:
    df = make_df([{Columns.CODIGO: CODE_A, Columns.DESIGNACAO: "Produto Alfa"}])
    df_brands = pd.DataFrame({"COD": [CODE_A], "MARCA": ["SuperBrands"]})
    master = build_master_products(df, df_brands=df_brands)
    row = master[master[Columns.CODIGO] == CODE_A].iloc[0]
    assert row[Columns.MARCA] == "SuperBrands"


# ---------------------------------------------------------------------------
# Tests — Descarte de Códigos Locais
# ---------------------------------------------------------------------------


def test_local_codes_discarded(master: pd.DataFrame) -> None:
    """Códigos que começam por '1' devem ser descartados (PRD §5.1.10)."""
    local_code = 10001  # starts with '1' → local
    df = make_df(
        [
            {Columns.CODIGO: local_code, Columns.STOCK: 5, Columns.T_UNI: 10},
            {Columns.CODIGO: CODE_C, Columns.STOCK: 5, Columns.T_UNI: 10},
        ]
    )
    result = aggregate(df, detailed=False, master_products=master)
    assert local_code not in result[Columns.CODIGO].values
    assert CODE_C in result[Columns.CODIGO].values


# ---------------------------------------------------------------------------
# Tests — Ordenação determinística
# ---------------------------------------------------------------------------


def test_deterministic_sort_grouped(master: pd.DataFrame) -> None:
    """Vista agrupada deve estar ordenada por DESIGNAÇÃO."""
    df = make_df(
        [
            {Columns.CODIGO: CODE_C, Columns.DESIGNACAO: "Zzz Produto"},
            {Columns.CODIGO: CODE_A, Columns.DESIGNACAO: "Aaa Produto"},
        ]
    )
    result = aggregate(df, detailed=False, master_products=master)
    # After merge with master, designations come from master_products
    designacoes = result[Columns.DESIGNACAO].tolist()
    assert designacoes == sorted(designacoes)


def test_no_structural_duplication() -> None:
    """Deve existir uma única função aggregate — sem duplicação."""
    from orders_master.aggregation import aggregator

    module_functions = [name for name, _ in inspect.getmembers(aggregator, inspect.isfunction)]
    assert "aggregate" in module_functions
    assert module_functions.count("aggregate") == 1
