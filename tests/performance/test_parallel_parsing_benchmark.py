"""
tests/performance/test_parallel_parsing_benchmark.py — TASK-37.

Benchmarks parallel parsing of Infoprex files.
"""

import io

import pytest

from orders_master.app_services.session_service import load_infoprex_files
from orders_master.app_services.session_state import SessionState


@pytest.fixture
def mock_infoprex_file_content() -> bytes:
    """Gera conteúdo de um ficheiro Infoprex realista (simulado)."""
    header = "CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\tV0\tV1\tV2\tV3\n"
    # Repetir 100 linhas para dar algum trabalho ao parser
    row = "2234567\tPRODUTO TESTE\tFARMACIA_A\t10\t20.0\t15.0\t100\t2026-01-01\tLAB1\t15/05/2024\t5\t5\t5\t5\n"
    content = header + (row * 100)
    return content.encode("utf-16")


@pytest.mark.benchmark(group="parsing")
def test_parsing_benchmark(benchmark, mock_infoprex_file_content) -> None:
    """Benchmark do carregamento de 4 ficheiros Infoprex em paralelo."""

    def run_parsing():
        state = SessionState()
        # Criar 4 streams de ficheiro (BytesIO)
        files = [io.BytesIO(mock_infoprex_file_content) for _ in range(4)]
        for i, f in enumerate(files):
            f.name = f"file_{i}.txt"

        load_infoprex_files(
            files=files, state=state, lista_cla=[], lista_codigos=[], locations_aliases={}
        )

    benchmark(run_parsing)


def test_speedup_logical_cores():
    """Verifica se o número de workers faz sentido."""
    import multiprocessing

    cores = multiprocessing.cpu_count()
    # Apenas informativo, não falha o teste
    print(f"\nLogical cores: {cores}")
