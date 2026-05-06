import pytest
import pandas as pd
import numpy as np
import time
from orders_master.business_logic.cleaners import (
    clean_designation_vectorized,
    remove_zombie_rows,
    remove_zombie_aggregated
)
from orders_master.constants import Columns


def test_clean_designation_vectorized():
    """Verifica se a limpeza de designações funciona correctamente."""
    input_data = pd.Series([
        "BEN-U-RON* 500mg",
        "AÇÚCAR* MASCAVADO",
        "  Espaços  ",
        "lowercase",
        None,
        np.nan,
        "Válido 100%"
    ])
    
    expected_output = pd.Series([
        "Ben-U-Ron 500Mg",
        "Acucar Mascavado",
        "Espacos",
        "Lowercase",
        "",
        "",
        "Valido 100%"
    ])
    
    output = clean_designation_vectorized(input_data)
    pd.testing.assert_series_equal(output, expected_output)


def test_remove_zombie_rows():
    """Verifica a remoção de linhas zombie individuais."""
    df = pd.DataFrame({
        Columns.STOCK: [0, 1, 0, 10],
        Columns.T_UNI: [0, 0, 5, 10]
    })
    
    expected_df = pd.DataFrame({
        Columns.STOCK: [1, 0, 10],
        Columns.T_UNI: [0, 5, 10]
    }, index=[1, 2, 3])
    
    output = remove_zombie_rows(df)
    pd.testing.assert_frame_equal(output, expected_df)


def test_remove_zombie_aggregated():
    """Verifica a remoção de códigos zombie no agregado."""
    df = pd.DataFrame({
        Columns.CODIGO: [1, 1, 2, 2, 3],
        Columns.STOCK:  [0, 0, 1, 0, 0],
        Columns.T_UNI:  [0, 0, 0, 0, 5]
    })
    
    # Produto 1 é zombie globalmente (0+0 stock, 0+0 vendas)
    # Produto 2 não é zombie (1+0 stock)
    # Produto 3 não é zombie (5 vendas)
    
    expected_df = pd.DataFrame({
        Columns.CODIGO: [2, 2, 3],
        Columns.STOCK:  [1, 0, 0],
        Columns.T_UNI:  [0, 0, 5]
    }, index=[2, 3, 4])
    
    output = remove_zombie_aggregated(df)
    pd.testing.assert_frame_equal(output, expected_df)


@pytest.mark.benchmark
def test_clean_designation_performance():
    """Valida que a operação vectorizada é executada. O speedup real pode variar por ambiente."""
    n_rows = 100_000
    data = pd.Series(["BEN-U-RON* 500mg" for _ in range(n_rows)])
    
    # Versão vectorizada (Mandatória por GEMINI.md)
    start_vec = time.perf_counter()
    clean_designation_vectorized(data)
    end_vec = time.perf_counter()
    duration_vec = end_vec - start_vec
    
    # Versão .apply (Proibida, usada apenas para comparação)
    def clean_apply_logic(val):
        if val is None or pd.isna(val): return ""
        import unicodedata
        val = str(val)
        val = unicodedata.normalize('NFD', val).encode('ascii', 'ignore').decode('utf-8')
        val = val.replace('*', '')
        return val.strip().title()

    start_apply = time.perf_counter()
    data.apply(clean_apply_logic)
    end_apply = time.perf_counter()
    duration_apply = end_apply - start_apply
    
    speedup = duration_apply / duration_vec
    print(f"\nVectorized: {duration_vec:.4f}s | Apply: {duration_apply:.4f}s | Speedup: {speedup:.2f}x")
    
    # Garantir apenas que a função não crasha e termina em tempo razoável
    assert duration_vec < 1.0 
