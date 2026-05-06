import pandas as pd
import pytest

from orders_master.constants import Columns, GroupLabels, Weights
from orders_master.schemas import (
    AggregatedRowSchema,
    BrandRecordSchema,
    DetailedRowSchema,
    DoNotBuyRecordSchema,
    InfoprexRowSchema,
    ShortageRecordSchema,
)


def test_constants_weights():
    assert Weights.PADRAO == (0.4, 0.3, 0.2, 0.1)
    assert sum(Weights.PADRAO) == pytest.approx(1.0)


def test_constants_group_labels():
    assert GroupLabels.GROUP_ROW == "Grupo"
    assert GroupLabels.GROUP_ROW != "Zgrupo_Total"


def test_infoprex_row_schema_valid():
    df = pd.DataFrame(
        {
            Columns.CODIGO: [123],
            Columns.DESIGNACAO: ["Teste"],
            Columns.LOCALIZACAO: ["Loja 1"],
            Columns.STOCK: [10],
            Columns.PVP: [5.0],
            Columns.P_CUSTO: [3.0],
            Columns.T_UNI: [20],
        }
    )
    # Não deve lançar erro
    InfoprexRowSchema.validate_df(df)


def test_infoprex_row_schema_invalid():
    df = pd.DataFrame({Columns.CODIGO: [123]})
    with pytest.raises(ValueError, match="Colunas obrigatórias em falta"):
        InfoprexRowSchema.validate_df(df)


def test_aggregated_row_schema_valid():
    df = pd.DataFrame(
        {
            Columns.CODIGO: [123],
            Columns.DESIGNACAO: ["Teste"],
            Columns.PVP_MEDIO: [5.0],
            Columns.P_CUSTO_MEDIO: [3.0],
            Columns.T_UNI: [20],
            Columns.STOCK: [10],
        }
    )
    AggregatedRowSchema.validate_df(df)


def test_detailed_row_schema_valid():
    df = pd.DataFrame(
        {
            Columns.CODIGO: [123],
            Columns.DESIGNACAO: ["Teste"],
            Columns.LOCALIZACAO: ["Loja 1"],
            Columns.PVP_MEDIO: [5.0],
            Columns.P_CUSTO: [3.0],
            Columns.T_UNI: [20],
            Columns.STOCK: [10],
        }
    )
    DetailedRowSchema.validate_df(df)


def test_shortage_record_schema_valid():
    df = pd.DataFrame(
        {
            "Número de registo": ["123"],
            "Data de início de rutura": [pd.Timestamp("2024-01-01")],
            "Data prevista para reposição": [pd.Timestamp("2024-02-01")],
        }
    )
    ShortageRecordSchema.validate_df(df)


def test_donotbuy_record_schema_valid():
    df = pd.DataFrame(
        {
            "CNP": ["123"],
            "FARMACIA": ["Loja 1"],
            "DATA": [pd.Timestamp("2024-01-01")],
        }
    )
    DoNotBuyRecordSchema.validate_df(df)


def test_brand_record_schema_valid():
    df = pd.DataFrame({"COD": [123], "MARCA": ["Marca X"]})
    BrandRecordSchema.validate_df(df)
