import logging

import pandas as pd

from orders_master.config.locations_loader import map_location
from orders_master.constants import Columns
from orders_master.schemas import DoNotBuyRecordSchema

logger = logging.getLogger(__name__)

try:
    import streamlit as st

    cache_decorator = st.cache_data(ttl=3600, show_spinner="A carregar lista Não Comprar...")
except ImportError:

    from collections.abc import Callable
    from typing import Any, TypeVar

    F = TypeVar("F", bound=Callable[..., Any])

    def cache_decorator(func: F) -> F:
        return func


@cache_decorator
def fetch_donotbuy_list(url: str, aliases: dict[str, str]) -> pd.DataFrame:
    """
    Lê a Google Sheet de produtos Não Comprar, formata datas e alinha nomes de farmácia.
    """
    empty_df = pd.DataFrame(columns=["CNP", "FARMACIA", "DATA"])

    try:
        df = pd.read_excel(url, dtype={"CNP": str})
    except Exception as e:
        logger.warning(f"Não foi possível carregar a lista Não Comprar a partir de {url}: {e}")
        return empty_df

    try:
        DoNotBuyRecordSchema.validate_df(df)
    except ValueError as e:
        logger.error(f"Schema inesperado na lista Não Comprar: {e}")
        return empty_df

    # Parse dates
    df["DATA"] = pd.to_datetime(df["DATA"], format="%d-%m-%Y", errors="coerce")

    # Map locations
    df["FARMACIA"] = df["FARMACIA"].apply(
        lambda x: map_location(str(x), aliases) if pd.notna(x) else ""
    )

    # Sort and drop duplicates, keeping the most recent data
    df = df.sort_values(by=["CNP", "FARMACIA", "DATA"], ascending=[True, True, False])
    df = df.drop_duplicates(subset=["CNP", "FARMACIA"], keep="first")

    return df


def merge_donotbuy(
    df_sell_out: pd.DataFrame, df_donotbuy: pd.DataFrame, detailed: bool
) -> pd.DataFrame:
    """
    Faz merge da lista Não Comprar com o DataFrame de sell out.
    """
    if "CÓDIGO" not in df_sell_out.columns or df_donotbuy.empty:
        df_out = df_sell_out.copy()
        if Columns.DATA_OBS not in df_out.columns:
            df_out[Columns.DATA_OBS] = pd.NA
        return df_out

    df_out = df_sell_out.copy()
    df_out["CÓDIGO_STR"] = df_out["CÓDIGO"].astype(str)

    if detailed:
        if "LOCALIZACAO" not in df_out.columns:
            df_out[Columns.DATA_OBS] = pd.NA
            return df_out.drop(columns=["CÓDIGO_STR"])

        df_out = df_out.merge(
            df_donotbuy,
            left_on=["CÓDIGO_STR", "LOCALIZACAO"],
            right_on=["CNP", "FARMACIA"],
            how="left",
        )
    else:
        df_donotbuy_agg = df_donotbuy.sort_values("DATA", ascending=False).drop_duplicates(
            "CNP", keep="first"
        )

        df_out = df_out.merge(df_donotbuy_agg, left_on="CÓDIGO_STR", right_on="CNP", how="left")

    if "DATA" in df_out.columns:
        df_out[Columns.DATA_OBS] = df_out["DATA"].dt.strftime("%d-%m-%Y")
    else:
        df_out[Columns.DATA_OBS] = pd.NA

    cols_to_drop = ["CÓDIGO_STR", "CNP", "FARMACIA", "DATA"]
    cols_to_drop = [c for c in cols_to_drop if c in df_out.columns]

    df_out = df_out.drop(columns=cols_to_drop)

    return df_out
