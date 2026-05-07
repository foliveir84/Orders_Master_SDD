"""
tests/integration/test_pipeline_e2e.py — TASK-37.

Valida o fluxo end-to-end: Ingestão -> Integração -> Agregação -> Recálculo.
"""

import io
from unittest.mock import patch

import pandas as pd
import pytest

from orders_master.app_services.recalc_service import recalculate_proposal
from orders_master.app_services.session_service import process_orders_session
from orders_master.app_services.session_state import SessionState
from orders_master.constants import Columns


@pytest.fixture
def mock_infoprex_content() -> bytes:
    """Gera conteúdo binário simulando exportação Infoprex (UTF-16 LE + BOM)."""
    # CPR '2234567' (não começa por '1' para evitar descarte por código local)
    header = "CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\tV0\tV1\tV2\tV3\n"
    row = "2234567\tPRODUTO TESTE\tFARMACIA_A\t10\t20.0\t15.0\t100\t2026-01-01\tLAB1\t15/05/2024\t5\t5\t5\t5\n"
    content = header + row
    return content.encode("utf-16")


@pytest.fixture
def mock_brands_content() -> bytes:
    """Gera conteúdo binário simulando CSV de marcas."""
    content = "COD;MARCA\n2234567;MARCA_TESTE\n"
    return content.encode("utf-8")


def test_pipeline_full_flow(mock_infoprex_content, mock_brands_content) -> None:
    """Testa o pipeline completo com mocks de ficheiros e integrações."""
    state = SessionState()

    # Mocks de ficheiros
    file1 = io.BytesIO(mock_infoprex_content)
    file1.name = "farmacia_a.txt"

    brands_file = io.BytesIO(mock_brands_content)
    brands_file.name = "marcas.csv"

    # Patch streamlit.secrets para retornar None
    with patch("streamlit.secrets") as mock_secrets:
        mock_secrets.get.return_value = None
        process_orders_session(
            files=[file1],
            codes_file=None,
            brands_files=[brands_file],
            labs_selected=[],
            labs_config=None,
            locations_aliases={},
            state=state,
        )

    # 1. Verificar Ingestão
    assert not state.df_raw.empty, "df_raw should not be empty"
    assert len(state.file_inventory) == 1
    assert state.file_inventory[0].status == "ok"
    assert "MARCA_TESTE" in state.master_products[Columns.MARCA].values

    # 2. Verificar Agregação Inicial
    assert not state.df_aggregated.empty, f"df_aggregated is empty. Raw: {state.df_raw}"
    assert Columns.T_UNI in state.df_aggregated.columns

    cols = list(state.df_aggregated.columns)
    idx_tuni = cols.index(Columns.T_UNI)
    # Procurar o bloco de meses (MAI deve estar logo antes de T Uni)
    assert cols[idx_tuni - 1] == "MAI", f"Expected MAI before T Uni. Columns: {cols}"

    # 3. Verificar Recálculo
    weights = (1.0, 0.0, 0.0, 0.0)
    df_final = recalculate_proposal(
        df_detailed=state.df_raw,
        detailed_view=False,
        master_products=state.master_products,
        months=4.0,
        weights=weights,
        scope_context=state.scope_context,
    )

    row = df_final[df_final[Columns.CODIGO] == 2234567].iloc[0]
    # MAI=5, Meses=4 -> 20. Stock=10 -> Proposta=10.
    assert row[Columns.PROPOSTA] == 10.0


def test_pipeline_with_integration_mocks(mock_infoprex_content) -> None:
    """Testa o pipeline com dados injectados de rupturas e do-not-buy."""
    state = SessionState()
    file1 = io.BytesIO(mock_infoprex_content)
    file1.name = "f1.txt"

    df_shortages = pd.DataFrame(
        {
            "Número de registo": ["2234567"],
            "TimeDelta": [30],
            "DIR": ["2024-05-01"],
            "DPR": ["2024-06-01"],
            "Data da Consulta": ["2024-05-15"],
        }
    )

    df_dnb = pd.DataFrame(
        {"CNP": ["2234567"], "FARMACIA": ["Farmacia_A"], "DATA": [pd.Timestamp("2024-05-10")]}
    )

    with patch("streamlit.secrets") as mock_secrets:

        def mock_get(key, default=None):
            if key == "SHORTAGES_URL":
                return "http://fake_shortages"
            if key == "DONOTBUY_URL":
                return "http://fake_dnb"
            return default

        mock_secrets.get.side_effect = mock_get

        with patch(
            "orders_master.app_services.session_service.fetch_shortages_db",
            return_value=df_shortages,
        ):
            with patch(
                "orders_master.integrations.donotbuy.fetch_donotbuy_list", return_value=df_dnb
            ):
                process_orders_session(
                    files=[file1],
                    codes_file=None,
                    brands_files=[],
                    labs_selected=[],
                    labs_config=None,
                    locations_aliases={},
                    state=state,
                )

    # Verificar se dados foram injectados
    assert (
        state.shortages_data_consulta == "2024-05-15"
    ), f"Consultation date mismatch. State: {state.shortages_data_consulta}"
    assert Columns.DATA_OBS in state.df_raw.columns
    assert Columns.DIR in state.df_raw.columns
    assert state.df_raw[Columns.DATA_OBS].iloc[0] == "10-05-2024"
    assert state.df_raw[Columns.TIME_DELTA].iloc[0] == 30
