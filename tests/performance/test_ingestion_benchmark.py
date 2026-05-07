"""
tests/performance/test_ingestion_benchmark.py — TASK-39.

Benchmarks de performance para validar NFR-P1 (ingestão <= 15s).
"""

import io
import pytest
from orders_master.app_services.session_service import load_infoprex_files
from orders_master.app_services.session_state import SessionState

@pytest.fixture
def realistic_infoprex_content() -> bytes:
    """Gera conteúdo de um ficheiro Infoprex realista (25.000 linhas)."""
    header = "CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\tV0\tV1\tV2\tV3\n"
    # 25000 linhas por ficheiro
    row = "2000001\tPRODUTO TESTE\tFARMACIA_A\t10\t20.0\t15.0\t100\t2026-01-01\tLAB1\t15/05/2024\t5\t5\t5\t5\n"
    content = header + (row * 25000)
    return content.encode("utf-16")

@pytest.mark.benchmark(group="ingestion")
def test_ingestion_benchmark_4_files(benchmark, realistic_infoprex_content):
    """
    Benchmark de ingestão de 4 ficheiros de 25.000 linhas cada (total 100k linhas).
    Target: <= 15s.
    """
    def run_ingestion():
        state = SessionState()
        files = [io.BytesIO(realistic_infoprex_content) for _ in range(4)]
        for i, f in enumerate(files):
            f.name = f"store_{i}.txt"
        
        from orders_master.app_services.session_service import process_orders_session
        from unittest.mock import patch
        
        with patch("streamlit.secrets", {}):
            with patch("orders_master.app_services.session_service.fetch_shortages_db", return_value=None):
                with patch("orders_master.integrations.donotbuy.fetch_donotbuy_list", return_value=None):
                    process_orders_session(
                        files=files,
                        codes_file=None,
                        brands_files=[],
                        labs_selected=[],
                        labs_config=None,
                        locations_aliases={},
                        state=state
                    )
        return state

    state_result = benchmark(run_ingestion)
    assert len(state_result.file_inventory) == 4
    assert not state_result.df_raw.empty
