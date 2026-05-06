from typing import ClassVar

import pandas as pd
from pydantic import BaseModel, ConfigDict

from orders_master.constants import Columns


class DataFrameSchema(BaseModel):
    """Base para validação de DataFrames via Pydantic."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def validate_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida se o DataFrame cumpre os requisitos do schema.
        Lança ValueError em caso de falha.
        """
        # Esta implementação base será estendida pelos schemas específicos
        return df


class InfoprexRowSchema(DataFrameSchema):
    """Schema para validação de uma linha individual do Infoprex (pós-parsing)."""

    required_columns: ClassVar[list[str]] = [
        Columns.CODIGO,
        Columns.DESIGNACAO,
        Columns.LOCALIZACAO,
        Columns.STOCK,
        Columns.PVP,
        Columns.P_CUSTO,
        Columns.T_UNI,
    ]

    @classmethod
    def validate_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        # Verificar colunas obrigatórias
        missing = [col for col in cls.required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias em falta no Infoprex: {missing}")

        # Verificar se existe pelo menos a âncora T Uni e colunas de vendas à esquerda
        # (A validação mais profunda da âncora é feita em TASK-36)

        return df


class AggregatedRowSchema(DataFrameSchema):
    """Schema para a vista agregada (1 linha por produto)."""

    required_columns: ClassVar[list[str]] = [
        Columns.CODIGO,
        Columns.DESIGNACAO,
        Columns.PVP_MEDIO,
        Columns.P_CUSTO_MEDIO,
        Columns.T_UNI,
        Columns.STOCK,
    ]

    @classmethod
    def validate_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        missing = [col for col in cls.required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias em falta no Agregado: {missing}")
        return df


class DetailedRowSchema(DataFrameSchema):
    """Schema para a vista detalhada (loja + linha Grupo)."""

    required_columns: ClassVar[list[str]] = [
        Columns.CODIGO,
        Columns.DESIGNACAO,
        Columns.LOCALIZACAO,
        Columns.PVP_MEDIO,
        Columns.P_CUSTO,
        Columns.T_UNI,
        Columns.STOCK,
    ]

    @classmethod
    def validate_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        missing = [col for col in cls.required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias em falta no Detalhado: {missing}")
        return df


class ShortageRecordSchema(DataFrameSchema):
    """Schema para a BD de Esgotados do Infarmed."""

    # Nomes originais da Google Sheet (serão renomeados após merge)
    required_columns: ClassVar[list[str]] = [
        "Número de registo",
        "Data de início de rutura",
        "Data prevista para reposição",
    ]

    @classmethod
    def validate_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        missing = [col for col in cls.required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias em falta na BD Esgotados: {missing}")
        return df


class DoNotBuyRecordSchema(DataFrameSchema):
    """Schema para a lista "Não Comprar"."""

    required_columns: ClassVar[list[str]] = ["CNP", "FARMACIA", "DATA"]

    @classmethod
    def validate_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        missing = [col for col in cls.required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias em falta na lista Não Comprar: {missing}")
        return df


class BrandRecordSchema(DataFrameSchema):
    """Schema para os ficheiros de Marcas."""

    required_columns: ClassVar[list[str]] = ["COD", "MARCA"]

    @classmethod
    def validate_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        missing = [col for col in cls.required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias em falta na base de Marcas: {missing}")
        return df
