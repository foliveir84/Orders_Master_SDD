import logging
from collections.abc import Callable
from typing import Any

import pandas as pd

from orders_master.app_services.session_state import FileInventoryEntry, SessionState
from orders_master.constants import Columns
from orders_master.exceptions import FileError, InfoprexEncodingError, InfoprexSchemaError
from orders_master.ingestion.infoprex_parser import parse_infoprex_file

logger = logging.getLogger(__name__)


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
