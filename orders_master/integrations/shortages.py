import logging
from datetime import datetime

import pandas as pd

from orders_master.schemas import ShortageRecordSchema

logger = logging.getLogger(__name__)

try:
    import streamlit as st

    cache_decorator = st.cache_data(ttl=3600, show_spinner="A carregar BD de Rupturas...")
except ImportError:

    from collections.abc import Callable
    from typing import Any, TypeVar

    F = TypeVar("F", bound=Callable[..., Any])

    def cache_decorator(func: F) -> F:
        return func


@cache_decorator  # type: ignore
def fetch_shortages_db(url: str, codigos_visible: set[int] | None = None) -> pd.DataFrame:
    """
    Lê a Google Sheet de Esgotados, valida o schema e recalcula o TimeDelta.
    """
    empty_df = pd.DataFrame(
        columns=[
            "Número de registo",
            "Data de início de rutura",
            "Data prevista para reposição",
            "TimeDelta",
            "Data da Consulta",
        ]
    )

    try:
        df = pd.read_excel(url, dtype={"Número de registo": str})
    except Exception as e:
        logger.warning(f"Não foi possível carregar a BD de Rupturas a partir de {url}: {e}")
        return empty_df

    try:
        ShortageRecordSchema.validate_df(df)
    except ValueError as e:
        logger.error(f"Schema inesperado na BD de Rupturas: {e}")
        return empty_df

    # Recalcula TimeDelta = (Data_Prevista_Reposição - datetime.now().date()).days
    df["Data prevista para reposição"] = pd.to_datetime(
        df["Data prevista para reposição"], errors="coerce"
    )
    df["Data de início de rutura"] = pd.to_datetime(df["Data de início de rutura"], errors="coerce")

    today = datetime.now().date()
    df["TimeDelta"] = (df["Data prevista para reposição"].dt.date - today).apply(
        lambda x: x.days if pd.notnull(x) else pd.NA
    )

    if codigos_visible is not None:
        df = df[
            df["Número de registo"].astype(str).str.strip().isin([str(c) for c in codigos_visible])
        ].copy()

    return df


def merge_shortages(df_sell_out: pd.DataFrame, df_shortages: pd.DataFrame) -> pd.DataFrame:
    """
    Faz merge da BD Esgotados no DataFrame de sell out.
    """
    if "CÓDIGO" not in df_sell_out.columns:
        return df_sell_out

    df_out = df_sell_out.copy()
    df_out["CÓDIGO_STR"] = df_out["CÓDIGO"].astype(str)

    # left join
    df_out = df_out.merge(
        df_shortages, left_on="CÓDIGO_STR", right_on="Número de registo", how="left"
    )

    # Renomear e formatar DIR/DPR
    if "Data de início de rutura" in df_out.columns:
        df_out["DIR"] = df_out["Data de início de rutura"].dt.strftime("%d-%m-%Y")
    else:
        df_out["DIR"] = pd.NA

    if "Data prevista para reposição" in df_out.columns:
        df_out["DPR"] = df_out["Data prevista para reposição"].dt.strftime("%d-%m-%Y")
    else:
        df_out["DPR"] = pd.NA

    # Drop auxiliary columns (TimeDelta NOT dropped here, as it's used in compute_shortage_proposal)
    cols_to_drop = [
        "CÓDIGO_STR",
        "Número de registo",
        "Nome do medicamento",
        "Data de início de rutura",
        "Data prevista para reposição",
        "Data da Consulta",
    ]

    cols_to_drop = [c for c in cols_to_drop if c in df_out.columns]
    df_out = df_out.drop(columns=cols_to_drop)

    return df_out
