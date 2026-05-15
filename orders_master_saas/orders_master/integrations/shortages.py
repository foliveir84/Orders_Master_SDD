import logging
from datetime import datetime

import numpy as np
import pandas as pd

from orders_master.constants import Columns
try:
    from orders_master.integrations.django_cache import django_cache_decorator
    # django_cache_decorator(timeout=..., key_prefix=...) returns a decorator directly
    cache_decorator = django_cache_decorator(timeout=3600, key_prefix="shortages")
except ImportError:
    # Fallback: use generic cache_decorator (Streamlit or no-op)
    # Wrap it so @cache_decorator works without parentheses
    from orders_master.integrations.cache_decorator import cache_decorator as _cache_factory  # noqa: F401

    def cache_decorator(func):  # type: ignore[misc]
        return _cache_factory(ttl=3600)(func)
from orders_master.schemas import ShortageRecordSchema

logger = logging.getLogger(__name__)


@cache_decorator
def fetch_shortages_db(url: str, codigos_visible: set[int] | None = None) -> pd.DataFrame:
    """
    Lê a Google Sheet de Esgotados, valida o schema e recalcula o TimeDelta.
    """
    empty_df = pd.DataFrame(
        columns=[
            "Número de registo",
            "Data de início de rutura",
            "Data prevista para reposição",
            Columns.TIME_DELTA,
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

    today = pd.Timestamp(datetime.now().date())
    delta = (df["Data prevista para reposição"] - today)
    df[Columns.TIME_DELTA] = np.where(
        delta.notna(),
        delta.dt.days,
        pd.NA,
    ).astype("Int64")

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

    # Remover colunas de integração pré-inicializadas para evitar _x/_y após merge
    pre_init_cols = [c for c in [Columns.DIR, Columns.DPR, Columns.DATA_OBS, Columns.TIME_DELTA] if c in df_out.columns]
    if pre_init_cols:
        df_out = df_out.drop(columns=pre_init_cols)

    # left join
    df_out = df_out.merge(
        df_shortages, left_on="CÓDIGO_STR", right_on="Número de registo", how="left"
    )

    # Renomear e formatar DIR/DPR
    if "Data de início de rutura" in df_out.columns:
        df_out[Columns.DIR] = df_out["Data de início de rutura"].dt.strftime("%d-%m-%Y")
    else:
        df_out[Columns.DIR] = pd.NA

    if "Data prevista para reposição" in df_out.columns:
        df_out[Columns.DPR] = df_out["Data prevista para reposição"].dt.strftime("%d-%m-%Y")
    else:
        df_out[Columns.DPR] = pd.NA

    # Manter apenas as colunas originais do sell_out + as 3 da integração necessárias
    # Isto remove automaticamente colunas extra como "Motivo", "Medida de Mitigação", etc.
    cols_base_sellout = list(df_sell_out.columns)
    cols_integracao = [Columns.DIR, Columns.DPR, Columns.TIME_DELTA]

    final_cols = [c for c in cols_base_sellout if c in df_out.columns]
    for c in cols_integracao:
        if c in df_out.columns and c not in final_cols:
            final_cols.append(c)

    return df_out[final_cols]
