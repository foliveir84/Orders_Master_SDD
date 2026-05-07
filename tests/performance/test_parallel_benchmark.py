"""
tests/performance/test_parallel_benchmark.py — TASK-49.

Benchmarks parallel vs sequential parsing of Infoprex files.
"""

import io
import os
import pytest
import pandas as pd
from orders_master.app_services.session_service import load_infoprex_files, parse_infoprex_file
from orders_master.app_services.session_state import SessionState
from orders_master.constants import Columns

@pytest.fixture
def colossal_infoprex_content() -> bytes:
    """Gera conteúdo de um ficheiro Infoprex colossal (100.000 linhas)."""
    header = "CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\tV0\tV1\tV2\tV3\n"
    # 100000 linhas
    row = "2234567\tPRODUTO TESTE\tFARMACIA_A\t10\t20.0\t15.0\t100\t2026-01-01\tLAB1\t15/05/2024\t5\t5\t5\t5\n"
    content = header + (row * 100000)
    return content.encode("utf-16")

def run_sequential_parsing(files):
    """Implementação sequencial."""
    dfs = []
    for f in files:
        df, _ = parse_infoprex_file(f, [], [], {})
        # Simular processamento adicional que pode estar no loop
        if Columns.PRICE_ANOMALY in df.columns:
            _ = df[Columns.PRICE_ANOMALY].sum()
        dfs.append(df)
    return dfs

@pytest.mark.benchmark(group="parallel_parsing")
def test_benchmark_sequential(benchmark, colossal_infoprex_content):
    """Benchmark do carregamento sequencial de 8 ficheiros."""
    def run():
        state = SessionState()
        files = [io.BytesIO(colossal_infoprex_content) for _ in range(8)]
        for i, f in enumerate(files):
            f.name = f"seq_{i}.txt"
        run_sequential_parsing(files)
    benchmark(run)

@pytest.mark.benchmark(group="parallel_parsing")
@pytest.mark.skipif(os.cpu_count() is not None and os.cpu_count() < 4, reason="Benchmark requires at least 4 cores")
def test_benchmark_parallel(benchmark, colossal_infoprex_content):
    """Benchmark do carregamento paralelo de 8 ficheiros."""
    def run():
        state = SessionState()
        files = [io.BytesIO(colossal_infoprex_content) for _ in range(8)]
        for i, f in enumerate(files):
            f.name = f"par_{i}.txt"
        load_infoprex_files(
            files=files, state=state, lista_cla=[], lista_codigos=[], locations_aliases={}
        )
    benchmark(run)
