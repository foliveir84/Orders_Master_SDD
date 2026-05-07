"""
Motor de agregação único — TASK-14.

Implementa a função ``aggregate`` que produz tanto a vista agrupada como a
detalhada a partir de um DataFrame pós-ingestão, seguindo os 10 passos do PRD §5.3.3.
"""

import pandas as pd

from orders_master.business_logic.cleaners import (
    clean_designation_vectorized,
    remove_zombie_aggregated,
    remove_zombie_rows,
)
from orders_master.constants import Columns, GroupLabels

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_master_products(
    df: pd.DataFrame,
    df_brands: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Constrói a tabela de produtos-mestre a partir do DataFrame de ingestão.

    Para cada CÓDIGO guarda a DESIGNAÇÃO canónica (mais frequente) e, se
    fornecido, injeta a MARCA proveniente de um CSV de marcas.

    Args:
        df: DataFrame pós-ingestão com pelo menos CÓDIGO e DESIGNAÇÃO.
        df_brands: DataFrame opcional com colunas ``COD`` (int) e ``MARCA`` (str).

    Returns:
        DataFrame com colunas CÓDIGO, DESIGNAÇÃO e MARCA.
    """
    # Designação mais frequente por código
    master = (
        df.groupby(Columns.CODIGO)[Columns.DESIGNACAO]
        .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
        .reset_index()
    )
    master[Columns.DESIGNACAO] = clean_designation_vectorized(master[Columns.DESIGNACAO])
    master[Columns.MARCA] = ""

    if df_brands is not None and not df_brands.empty:
        brands_clean = df_brands.rename(columns={"COD": Columns.CODIGO})[
            [Columns.CODIGO, Columns.MARCA]
        ].drop_duplicates(subset=[Columns.CODIGO])
        master = master.merge(brands_clean, on=Columns.CODIGO, how="left", suffixes=("_old", ""))
        if "MARCA_old" in master.columns:
            master = master.drop(columns=["MARCA_old"])
        master[Columns.MARCA] = master[Columns.MARCA].fillna("")

    return master[[Columns.CODIGO, Columns.DESIGNACAO, Columns.MARCA]]


def reorder_columns(df: pd.DataFrame, detailed: bool) -> pd.DataFrame:
    """
    Reordena as colunas do DataFrame conforme a vista.

    Args:
        df: DataFrame agregado.
        detailed: Se True, inclui colunas de detalhe (DUC, DTVAL, LOCALIZACAO).

    Returns:
        DataFrame com colunas reordenadas.
    """
    # Colunas que vêm obrigatoriamente ANTES dos meses dinâmicos
    before_months_grouped = [
        Columns.CODIGO,
        Columns.DESIGNACAO,
        Columns.MARCA,
        Columns.PVP_MEDIO,
        Columns.P_CUSTO_MEDIO,
    ]
    before_months_detailed = [
        Columns.CODIGO,
        Columns.DESIGNACAO,
        Columns.MARCA,
        Columns.LOCALIZACAO,
        Columns.PVP,
        Columns.P_CUSTO,
        Columns.DUC,
        Columns.DTVAL,
    ]

    # Colunas que vêm obrigatoriamente DEPOIS dos meses dinâmicos
    after_months = [
        Columns.T_UNI,
        Columns.STOCK,
        Columns.MEDIA,
        Columns.PROPOSTA,
        Columns.DIR,
        Columns.DPR,
        Columns.DATA_OBS,
        Columns.SORT_KEY,
    ]

    before = before_months_detailed if detailed else before_months_grouped
    existing_before: list[str] = [str(c) for c in before if c in df.columns]
    existing_after: list[str] = [str(c) for c in after_months if c in df.columns]

    # Meses dinâmicos são os que não estão em 'before' nem em 'after'
    months: list[str] = [
        str(c) for c in df.columns if c not in existing_before and c not in existing_after
    ]

    return df[existing_before + months + existing_after]


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


def aggregate(
    df: pd.DataFrame,
    detailed: bool,
    master_products: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produz a vista agrupada (``detailed=False``) ou a vista detalhada
    (``detailed=True``) a partir de um DataFrame pós-ingestão.

    Pipeline (PRD §5.3.3):
    1. Descartar códigos locais (prefixo '1').
    2. Remover linhas zombie individuais.
    3. Calcular médias de preços excluindo anomalias.
    4. Agregar (sum) colunas de vendas e stock.
    5. Injectar designações canónicas e marcas de master_products.
    6. Remover zombies pós-agregação (grupo total == 0).
    7. Se detalhada: adicionar linhas de Grupo.
    8. Calcular _sort_key.
    9. Ordenação determinística.
    10. Reordenar colunas.

    Args:
        df: DataFrame pós-ingestão.
        detailed: True → inclui linhas por loja + linha Grupo; False → 1 linha/código.
        master_products: Tabela mestre de produtos (CÓDIGO, DESIGNAÇÃO, MARCA).

    Returns:
        DataFrame agregado conforme a vista pedida.
    """
    if df.empty:
        return df.copy()

    # ------------------------------------------------------------------
    # Passo 1 — Descartar códigos locais (prefixo '1')
    # ------------------------------------------------------------------
    df_work = df[~df[Columns.CODIGO].astype(str).str.startswith("1")].copy()

    # ------------------------------------------------------------------
    # Passo 2 — Remover zombies individuais
    # ------------------------------------------------------------------
    df_work = remove_zombie_rows(df_work)

    # ------------------------------------------------------------------
    # Identificar colunas de vendas mensais (tudo excepto as conhecidas)
    # ------------------------------------------------------------------
    known_non_sales = {
        Columns.CODIGO,
        Columns.DESIGNACAO,
        Columns.LOCALIZACAO,
        Columns.STOCK,
        Columns.PVP,
        Columns.P_CUSTO,
        Columns.DUC,
        Columns.DTVAL,
        Columns.CLA,
        Columns.T_UNI,
        Columns.PRICE_ANOMALY,
        Columns.MARCA,
        Columns.MEDIA,
        Columns.PROPOSTA,
        Columns.DIR,
        Columns.DPR,
        Columns.DATA_OBS,
        Columns.TIME_DELTA,
        Columns.SORT_KEY,
    }
    sales_cols = [c for c in df_work.columns if c not in known_non_sales]

    # ------------------------------------------------------------------
    # Passo 3 — Médias de preços (excluindo anomalias)
    # ------------------------------------------------------------------
    if Columns.PRICE_ANOMALY in df_work.columns:
        df_valid = df_work[~df_work[Columns.PRICE_ANOMALY]]
    else:
        df_valid = df_work

    group_keys_price = [Columns.CODIGO, Columns.LOCALIZACAO] if detailed else [Columns.CODIGO]

    price_cols_present = [c for c in [Columns.PVP, Columns.P_CUSTO] if c in df_work.columns]
    if price_cols_present:
        avg_prices = df_valid.groupby(group_keys_price, as_index=False)[price_cols_present].mean()
        avg_prices[price_cols_present] = avg_prices[price_cols_present].round(2)
    else:
        avg_prices = pd.DataFrame(columns=group_keys_price)

    # ------------------------------------------------------------------
    # Passo 4 — Agregação (soma) de stock e vendas
    # ------------------------------------------------------------------
    group_keys = [Columns.CODIGO, Columns.LOCALIZACAO] if detailed else [Columns.CODIGO]

    agg_cols = [Columns.STOCK, Columns.T_UNI, Columns.MEDIA, Columns.PROPOSTA] + sales_cols
    agg_cols_present = [c for c in agg_cols if c in df_work.columns]

    # Para detalhado, preservar DUC e DTVAL na linha de detalhe (first)
    extra_agg: dict[str, str] = {}
    if detailed:
        for col in [Columns.DUC, Columns.DTVAL]:
            if col in df_work.columns:
                extra_agg[col] = "first"

    df_agg = df_work.groupby(group_keys, as_index=False)[agg_cols_present].sum()

    if extra_agg:
        df_extra = df_work.groupby(group_keys, as_index=False).agg(extra_agg)
        df_agg = df_agg.merge(df_extra, on=group_keys, how="left")

    # Merge médias de preços
    if not avg_prices.empty and price_cols_present:
        df_agg = df_agg.merge(avg_prices, on=group_keys_price, how="left")

    # ------------------------------------------------------------------
    # Passo 5 — Injectar master_products (designação canónica + marca)
    # ------------------------------------------------------------------
    df_agg = df_agg.merge(master_products, on=Columns.CODIGO, how="left")

    # ------------------------------------------------------------------
    # Passo 6 — Remover zombies pós-agregação
    # ------------------------------------------------------------------
    df_agg = remove_zombie_aggregated(df_agg)

    if df_agg.empty:
        return df_agg

    # ------------------------------------------------------------------
    # Passo 7 — Vista detalhada: adicionar linhas de Grupo
    # ------------------------------------------------------------------
    if detailed:
        group_agg_cols = [Columns.STOCK, Columns.T_UNI, Columns.PROPOSTA, Columns.MEDIA] + sales_cols
        group_agg_cols_present = [c for c in group_agg_cols if c in df_agg.columns]
        df_group_rows = df_agg.groupby(Columns.CODIGO, as_index=False)[group_agg_cols_present].sum()

        # Preencher campos da linha Grupo
        df_group_rows[Columns.LOCALIZACAO] = GroupLabels.GROUP_ROW

        # Copiar designação e marca do primeiro registo
        meta_cols = [Columns.DESIGNACAO, Columns.MARCA]
        for col in meta_cols:
            if col in df_agg.columns:
                meta = df_agg.groupby(Columns.CODIGO)[col].first().reset_index()
                df_group_rows = df_group_rows.merge(meta, on=Columns.CODIGO, how="left")

        # DUC e DTVAL ficam NaN na linha Grupo (por design)
        df_agg = pd.concat([df_agg, df_group_rows], ignore_index=True)

    # ------------------------------------------------------------------
    # Passo 8 — Calcular _sort_key (0 = detalhe, 1 = Grupo)
    # ------------------------------------------------------------------
    if detailed and Columns.LOCALIZACAO in df_agg.columns:
        df_agg[Columns.SORT_KEY] = (df_agg[Columns.LOCALIZACAO] == GroupLabels.GROUP_ROW).astype(
            int
        )
    else:
        df_agg[Columns.SORT_KEY] = 0

    # ------------------------------------------------------------------
    # Passo 9 — Ordenação determinística
    # ------------------------------------------------------------------
    sort_cols = [Columns.DESIGNACAO, Columns.CODIGO, Columns.SORT_KEY]
    if detailed and Columns.LOCALIZACAO in df_agg.columns:
        sort_cols.append(Columns.LOCALIZACAO)

    sort_cols_present = [c for c in sort_cols if c in df_agg.columns]
    df_agg = df_agg.sort_values(sort_cols_present).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Passo 10a — Renomear PVP/P.CUSTO para PVP_Médio/P.CUSTO_Médio (só agrupada)
    # ------------------------------------------------------------------
    if not detailed:
        rename_map = {}
        if Columns.PVP in df_agg.columns:
            rename_map[Columns.PVP] = Columns.PVP_MEDIO
        if Columns.P_CUSTO in df_agg.columns:
            rename_map[Columns.P_CUSTO] = Columns.P_CUSTO_MEDIO
        if rename_map:
            df_agg = df_agg.rename(columns=rename_map)

    # ------------------------------------------------------------------
    # Passo 10b — Reordenar colunas
    # ------------------------------------------------------------------
    df_agg = reorder_columns(df_agg, detailed)

    return df_agg
