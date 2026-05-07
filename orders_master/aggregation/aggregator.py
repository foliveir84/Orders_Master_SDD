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
    Reordena as colunas do DataFrame conforme a vista solicitada.
    Ordem: CÓDIGO, DESIGNAÇÃO, LOCALIZACAO, PVP / PVP_Médio, P.CUSTO / P.CUSTO_Médio, DUC, DTVAL, STOCK, [Meses], T Uni, Proposta, DIR, DPR, DATA_OBS
    """
    # 1. Definir blocos de colunas estáticas (como strings para comparação robusta)
    before_months = [
        str(Columns.CODIGO),
        str(Columns.DESIGNACAO),
        str(Columns.LOCALIZACAO),
        str(Columns.PVP),
        "PVP_Médio",
        str(Columns.P_CUSTO),
        "P.CUSTO_Médio",
        str(Columns.DUC),
        str(Columns.DTVAL),
        str(Columns.STOCK),
    ]
    
    after_months = [
        str(Columns.T_UNI),
        str(Columns.PROPOSTA),
        str(Columns.DIR),
        str(Columns.DPR),
        str(Columns.DATA_OBS),
        str(Columns.TIME_DELTA),
    ]

    # 2. Identificar colunas presentes
    # Convertemos todas as colunas do DF para string para a comparação
    current_cols = [str(c) for c in df.columns]
    col_map = {str(c): c for c in df.columns} # mapeia de volta para o objecto original (StrEnum ou str)

    existing_before_strs = [c for c in before_months if c in current_cols]
    existing_after_strs = [c for c in after_months if c in current_cols]
    
    # 3. Meses dinâmicos
    tech_cols_strs = {
        str(Columns.SORT_KEY), str(Columns.CLA), "CÓDIGO_STR", "price_anomaly", 
        str(Columns.MEDIA), str(Columns.MARCA), str(Columns.PRICE_ANOMALY)
    }
    
    months_strs = [
        c for c in current_cols 
        if c not in existing_before_strs 
        and c not in existing_after_strs 
        and c not in tech_cols_strs
    ]

    # 4. Concatenar na ordem certa (usando os objectos originais das colunas)
    final_order_strs = existing_before_strs + months_strs + existing_after_strs
    final_order = [col_map[s] for s in final_order_strs]
    
    # Adicionar colunas técnicas ao fim
    for s in tech_cols_strs:
        if s in col_map and col_map[s] not in final_order:
            final_order.append(col_map[s])

    return df[final_order]


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
        
        # Preços de fallback (caso todos os preços de um grupo sejam anómalos e df_valid fique vazio para esse grupo)
        fallback_prices = df_work.groupby(group_keys_price, as_index=False)[price_cols_present].first()
    else:
        avg_prices = pd.DataFrame(columns=group_keys_price)
        fallback_prices = pd.DataFrame(columns=group_keys_price)

    # ------------------------------------------------------------------
    # Passo 4 — Agregação (soma) de stock e vendas
    # ------------------------------------------------------------------
    group_keys = [Columns.CODIGO, Columns.LOCALIZACAO] if detailed else [Columns.CODIGO]

    agg_cols = [Columns.STOCK, Columns.T_UNI, Columns.MEDIA, Columns.PROPOSTA] + sales_cols
    agg_cols_present = [c for c in agg_cols if c in df_work.columns]

    # Preservar metadados e colunas de integração (first)
    extra_agg: dict[str, str] = {}
    cols_to_preserve = [
        Columns.DUC, Columns.DTVAL, Columns.DIR, 
        Columns.DPR, Columns.TIME_DELTA
    ]
    if detailed:
        cols_to_preserve.append(Columns.DATA_OBS)
        
    for col in cols_to_preserve:
        if col in df_work.columns:
            extra_agg[col] = "first"

    df_agg = df_work.groupby(group_keys, as_index=False)[agg_cols_present].sum()

    if extra_agg:
        df_extra = df_work.groupby(group_keys, as_index=False).agg(extra_agg)
        df_agg = df_agg.merge(df_extra, on=group_keys, how="left")

    # Merge médias de preços e fallback
    if price_cols_present:
        if not avg_prices.empty:
            df_agg = df_agg.merge(avg_prices, on=group_keys_price, how="left")
        else:
            # Se avg_prices estiver totalmente vazio (ex: tudo anómalo), criamos as colunas com NaN para o fallback preencher
            for col in price_cols_present:
                df_agg[col] = pd.NA

        # Fallback para repor preços caso tenham ficado NaN por causa do filtro de anomalias
        df_agg = df_agg.set_index(group_keys_price)
        fallback_idx = fallback_prices.set_index(group_keys_price)
        for col in price_cols_present:
            df_agg[col] = df_agg[col].fillna(fallback_idx[col])
        df_agg = df_agg.reset_index()

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

        # Calcular PVP e P.Custo médios para a linha Grupo
        price_cols_to_avg = [c for c in [Columns.PVP, Columns.P_CUSTO] if c in df_agg.columns]
        if price_cols_to_avg:
            group_prices = df_agg.groupby(Columns.CODIGO, as_index=False)[price_cols_to_avg].mean()
            group_prices[price_cols_to_avg] = group_prices[price_cols_to_avg].round(2)
            df_group_rows = df_group_rows.merge(group_prices, on=Columns.CODIGO, how="left")

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
    # Passo 10a — Renomear PVP/P.CUSTO (conforme pedido)
    # Na vista detalhada, mantém-se PVP e P.CUSTO originais.
    # Na vista agrupada, renomeia-se para PVP_Médio e P.CUSTO_Médio.
    # ------------------------------------------------------------------
    rename_map = {}
    if not detailed:
        if Columns.PVP in df_agg.columns:
            rename_map[Columns.PVP] = "PVP_Médio"
        if Columns.P_CUSTO in df_agg.columns:
            rename_map[Columns.P_CUSTO] = "P.CUSTO_Médio"
    
    if rename_map:
        df_agg = df_agg.rename(columns=rename_map)

    # ------------------------------------------------------------------
    # Passo 10b — Reordenar colunas (DEVE SER O ÚLTIMO PASSO)
    # ------------------------------------------------------------------
    df_agg = reorder_columns(df_agg, detailed)

    return df_agg
