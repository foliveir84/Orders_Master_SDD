"""
Testes unitários para process_orders_session — TASK-23.
"""

from io import BytesIO, StringIO

import pytest

from orders_master.app_services.session_service import process_orders_session
from orders_master.app_services.session_state import SessionState
from orders_master.constants import Columns


@pytest.fixture
def session_state() -> SessionState:
    return SessionState()


def test_process_orders_session_success(session_state) -> None:
    """Verifica o pipeline completo de processamento."""
    # Mock de ficheiro Infoprex (Tab separated, colunas originais)
    header = "CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\tV0\tV1\n"
    row = "2001\tPROD A\tFAR1\t10\t10.0\t5.0\t100\t2026-01-01\tLAB1\t01/01/2024\t5\t5\n"
    content = header + row
    infoprex_file = BytesIO(content.encode("utf-8"))
    infoprex_file.name = "f1.csv"

    # Mock de marcas
    brands_content = "COD;MARCA\n2001;MARCA X\n"
    brands_file = StringIO(brands_content)
    brands_file.name = "marcas.csv"

    process_orders_session(
        files=[infoprex_file],
        codes_file=None,
        brands_files=[brands_file],
        labs_selected=["LAB1"],
        locations_aliases={},
        state=session_state,
    )

    assert not session_state.df_raw.empty
    assert not session_state.df_aggregated.empty
    assert not session_state.df_detailed.empty
    assert session_state.master_products[Columns.MARCA].iloc[0] == "MARCA X"
    assert session_state.df_raw[Columns.CODIGO].iloc[0] == 2001
    assert session_state.last_labs_selection == ["LAB1"]
    assert session_state.last_codes_file_name is None


def test_process_orders_session_with_codes(session_state) -> None:
    """Verifica que o filtro de códigos TXT tem prioridade."""
    header = "CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\tV0\n"
    row1 = "2001\tPROD A\tFAR1\t10\t10.0\t5.0\t100\t2026-01-01\tLAB1\t01/01/2024\t5\n"
    row2 = "3001\tPROD B\tFAR1\t10\t10.0\t5.0\t100\t2026-01-01\tLAB2\t01/01/2024\t5\n"
    content = header + row1 + row2
    infoprex_file = BytesIO(content.encode("utf-8"))

    codes_content = "2001\n"
    codes_file = BytesIO(codes_content.encode("utf-8"))
    codes_file.name = "codes.txt"

    process_orders_session(
        files=[infoprex_file],
        codes_file=codes_file,
        brands_files=[],
        labs_selected=["LAB2"],  # Deveria ser ignorado
        locations_aliases={},
        state=session_state,
    )

    # Apenas o produto 2001 deve estar presente
    assert len(session_state.df_raw) == 1
    assert session_state.df_raw[Columns.CODIGO].iloc[0] == 2001
    assert session_state.last_codes_file_name == "codes.txt"
