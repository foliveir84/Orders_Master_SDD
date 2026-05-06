import pytest
import pandas as pd
import io
from orders_master.ingestion.brands_parser import parse_brands_csv


def test_parse_brands_csv_single_file():
    """Verifica se processa um único ficheiro CSV de marcas correctamente."""
    csv_content = "COD;MARCA\n1234567;MARCA A\n2345678;MARCA B\n"
    file_like = io.StringIO(csv_content)
    file_like.name = "marcas.csv"
    
    df = parse_brands_csv([file_like])
    
    assert len(df) == 2
    assert df.iloc[0]["COD"] == 1234567
    assert df.iloc[0]["MARCA"] == "MARCA A"
    assert df.iloc[1]["COD"] == 2345678
    assert df.iloc[1]["MARCA"] == "MARCA B"


def test_parse_brands_csv_multiple_files_dedup():
    """Verifica se processa múltiplos ficheiros e deduplica mantendo a primeira ocorrência."""
    csv1 = "COD;MARCA\n1;MARCA A\n2;MARCA B\n"
    csv2 = "COD;MARCA\n2;MARCA C\n3;MARCA D\n" # COD 2 duplicado
    
    f1 = io.StringIO(csv1)
    f2 = io.StringIO(csv2)
    
    df = parse_brands_csv([f1, f2])
    
    # 3 produtos únicos
    assert len(df) == 3
    # COD 2 deve manter MARCA B (do primeiro ficheiro/ocorrência)
    assert df[df["COD"] == 2]["MARCA"].iloc[0] == "MARCA B"
    assert set(df["COD"]) == {1, 2, 3}


def test_parse_brands_csv_cleaning():
    """Verifica a limpeza de dados (espaços, NAs, tipos)."""
    csv = (
        "COD;MARCA\n"
        "1 ; MARCA COM ESPACOS \n" # Espaços
        "2;nan\n"                  # NA como string
        "3;None\n"                 # NA como string
        "abc;INVALIDO\n"           # COD inválido
        "4; \n"                    # MARCA vazia
        "5;VALIDO\n"
    )
    
    f = io.StringIO(csv)
    df = parse_brands_csv([f])
    
    assert len(df) == 2
    assert set(df["COD"]) == {1, 5}
    assert df[df["COD"] == 1]["MARCA"].iloc[0] == "MARCA COM ESPACOS"


def test_parse_brands_csv_empty_input():
    """Verifica comportamento com input vazio."""
    assert parse_brands_csv([]).empty
    
    f = io.StringIO("COD;MARCA\n")
    assert parse_brands_csv([f]).empty


def test_parse_brands_csv_bad_lines():
    """Verifica se tolera e descarta linhas malformadas ou incompletas."""
    csv = (
        "COD;MARCA\n"
        "1;MARCA;EXTRA\n" # Extra colunas (ignoradas pelo usecols, mas mantida se COD/MARCA válidos)
        "INCOMPLETO\n"    # Incompleta (será descartada pela limpeza de COD/MARCA)
        "2;OK\n"
    )
    f = io.StringIO(csv)
    df = parse_brands_csv([f])
    
    # 1;MARCA;EXTRA -> COD=1, MARCA=MARCA (VÁLIDO)
    # INCOMPLETO -> COD=INCOMPLETO, MARCA=NaN (DESCARTADO)
    # 2;OK -> COD=2, MARCA=OK (VÁLIDO)
    assert len(df) == 2
    assert set(df["COD"]) == {1, 2}
