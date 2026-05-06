import logging
from collections.abc import Callable
from typing import Any

import pandas as pd

from orders_master.aggregation.aggregator import aggregate, build_master_products
from orders_master.app_services.session_state import FileInventoryEntry, SessionState
from orders_master.constants import Columns
from orders_master.exceptions import FileError, InfoprexEncodingError, InfoprexSchemaError
from orders_master.ingestion.brands_parser import parse_brands_csv
from orders_master.ingestion.codes_txt_parser import parse_codes_txt
from orders_master.ingestion.infoprex_parser import parse_infoprex_file

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


def load_infoprex_files(  # noqa: PLR0913
    files: list[Any],
    state: SessionState,
    lista_cla: list[str],
    lista_codigos: list[int],
    locations_aliases: dict[str, str],
    progress_callback: Callable[[float, str], None] | None = None,
) -> list[pd.DataFrame]:
    """
    Processa uma lista de ficheiros Infoprex, preenche o estado com erros tipados
    e o inventário de ficheiros. Retorna a lista de DataFrames válidos.
    """
    dfs = []
    n = len(files)

    for i, file_like in enumerate(files):
        filename = getattr(file_like, "name", "desconhecido")

        if progress_callback:
            progress_callback((i + 1) / n, f"A processar '{filename}' ({i+1}/{n})")

        try:
            df, entry = parse_infoprex_file(file_like, lista_cla, lista_codigos, locations_aliases)

            # Adiciona anomalias de preço (contagem) ao FileInventoryEntry
            if Columns.PRICE_ANOMALY in df.columns:
                anomalies = df[Columns.PRICE_ANOMALY].sum()
                if anomalies > 0:
                    prefix = " | " if entry.avisos else ""
                    entry.avisos += f"{prefix}Anomalias de preço: {anomalies}"

            state.file_inventory.append(entry)
            dfs.append(df)

        except InfoprexEncodingError as e:
            msg = str(e)
            state.file_errors.append(FileError(filename, "encoding", msg))
            state.file_inventory.append(
                FileInventoryEntry(filename=filename, status="error", error_message=msg)
            )
        except InfoprexSchemaError as e:
            msg = str(e)
            state.file_errors.append(FileError(filename, "schema", msg))
            state.file_inventory.append(
                FileInventoryEntry(filename=filename, status="error", error_message=msg)
            )
        except Exception as e:
            msg = f"Erro inesperado: {e}"
            logger.exception("Erro inesperado ao processar o ficheiro %s", filename)
            state.file_errors.append(FileError(filename, "unknown", msg))
            state.file_inventory.append(
                FileInventoryEntry(filename=filename, status="error", error_message=msg)
            )

    return dfs
