import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd

from orders_master.aggregation.aggregator import aggregate, build_master_products
from orders_master.app_services.session_state import FileInventoryEntry, SessionState
from orders_master.constants import Columns
from orders_master.exceptions import FileError, InfoprexEncodingError, InfoprexSchemaError
from orders_master.ingestion.brands_parser import parse_brands_csv
from orders_master.ingestion.codes_txt_parser import parse_codes_txt
from orders_master.ingestion.infoprex_parser import parse_infoprex_file
from orders_master.integrations.shortages import fetch_shortages_db, merge_shortages

logger = logging.getLogger(__name__)


def process_orders_session(  # noqa: PLR0913
    files: list[Any],
    codes_file: Any | None,
    brands_files: list[Any],
    labs_selected: list[str],
    locations_aliases: dict[str, str],
    state: SessionState,
    progress_callback: Callable[[float, str], None] | None = None,
) -> None:
    """
    Orquestra o pipeline pesado: parse -> concat -> aggregate -> popular SessionState.
    """
    # 0. Actualizar snapshot de filtros (TASK-28)
    state.last_labs_selection = list(labs_selected)
    state.last_codes_file_name = getattr(codes_file, "name", None) if codes_file else None

    # 1. Parse codes TXT (se presente)
    lista_codigos = []
    lista_cla = labs_selected
    if codes_file is not None:
        lista_codigos = parse_codes_txt(codes_file)
        if lista_codigos:
            lista_cla = []  # Códigos têm prioridade sobre labs

    # 2. Parse Infoprex files
    dfs = load_infoprex_files(
        files, state, lista_cla, lista_codigos, locations_aliases, progress_callback
    )

    if not dfs:
        return

    df_full = pd.concat(dfs, ignore_index=True)

    # 2.5 Integrar BD de Rupturas (TASK-32)
    try:
        import streamlit as st  # noqa: PLC0415

        from orders_master.integrations.donotbuy import fetch_donotbuy_list, merge_donotbuy

        url_shortages = st.secrets.get("SHORTAGES_URL")
        if url_shortages:
            df_shortages = fetch_shortages_db(url_shortages)
            if not df_shortages.empty:
                # O merge injecta TimeDelta (necessário para cálculos) e DIR/DPR (para visualização)
                df_full = merge_shortages(df_full, df_shortages)

                # Guardar data da consulta para o banner
                if "Data da Consulta" in df_shortages.columns:
                    state.shortages_data_consulta = str(df_shortages["Data da Consulta"].iloc[0])

        # 2.6 Integrar lista Não Comprar (TASK-37)
        url_dnb = st.secrets.get("DONOTBUY_URL")
        if url_dnb:
            df_dnb = fetch_donotbuy_list(url_dnb, locations_aliases)
            if not df_dnb.empty:
                # O merge injecta DATA_OBS no df_full (raw/detalhado)
                df_full = merge_donotbuy(df_full, df_dnb, detailed=True)

    except Exception:
        logger.exception("Falha ao integrar bases de dados externas (Rupturas/Não Comprar)")

    state.df_raw = df_full

    # 3. Build master products + brands
    df_brands = parse_brands_csv(brands_files) if brands_files else None
    master = build_master_products(df_full, df_brands)

    # 4. Agregações (detalhada e agrupada)
    # Nota: nestes passos não calculamos propostas ainda, só estrutura
    state.df_aggregated = aggregate(df_full, detailed=False, master_products=master)
    state.df_detailed = aggregate(df_full, detailed=True, master_products=master)

    # 5. Guardar master products para recálculos futuros
    state.master_products = master

    # 6. Popular ScopeContext inicial (TASK-33)
    state.scope_context.n_produtos = len(state.df_aggregated)
    state.scope_context.n_farmacias = df_full[Columns.LOCALIZACAO].nunique()

    if codes_file:
        state.scope_context.descricao_filtro = f"Lista TXT ({len(lista_codigos)} códigos)"
    elif labs_selected:
        state.scope_context.descricao_filtro = f"Laboratórios: {', '.join(labs_selected)}"
    else:
        state.scope_context.descricao_filtro = "Sem filtros (Todos)"


def load_infoprex_files(  # noqa: PLR0913
    files: list[Any],
    state: SessionState,
    lista_cla: list[str],
    lista_codigos: list[int],
    locations_aliases: dict[str, str],
    progress_callback: Callable[[float, str], None] | None = None,
) -> list[pd.DataFrame]:
    """
    Processa uma lista de ficheiros Infoprex em paralelo.
    """
    if not files:
        return []

    def process_single_file(
        file_like: Any,
    ) -> tuple[pd.DataFrame | None, FileInventoryEntry | None, Exception | None]:
        try:
            df, entry = parse_infoprex_file(file_like, lista_cla, lista_codigos, locations_aliases)
            # Preço anomalias
            if Columns.PRICE_ANOMALY in df.columns:
                anomalies = df[Columns.PRICE_ANOMALY].sum()
                if anomalies > 0:
                    prefix = " | " if entry.avisos else ""
                    entry.avisos += f"{prefix}Anomalias de preço: {anomalies}"
            return df, entry, None
        except Exception as e:
            return None, None, e

    dfs = []
    n = len(files)

    # Usar ThreadPoolExecutor para paralelismo I/O + GIL-releasing pandas operations
    # Limitar threads para evitar overhead excessivo em máquinas pequenas
    max_workers = min(len(files), os.cpu_count() or 4)
    # Cap para evitar explosão de threads em máquinas muito grandes
    max_workers = min(max_workers, 8)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_single_file, files))

    for i, (df, entry, error) in enumerate(results):
        filename = getattr(files[i], "name", f"ficheiro_{i+1}")

        if error:
            msg = str(error)
            error_type = "unknown"
            if isinstance(error, InfoprexEncodingError):
                error_type = "encoding"
            elif isinstance(error, InfoprexSchemaError):
                error_type = "schema"

            state.file_errors.append(FileError(filename, error_type, msg))
            state.file_inventory.append(
                FileInventoryEntry(filename=filename, status="error", error_message=msg)
            )
            if error_type == "unknown":
                logger.exception("Erro inesperado ao processar o ficheiro %s", filename)
        elif df is not None and entry is not None:
            state.file_inventory.append(entry)
            dfs.append(df)

        if progress_callback:
            progress_callback((i + 1) / n, f"Concluído '{filename}' ({i+1}/{n})")

    return dfs
