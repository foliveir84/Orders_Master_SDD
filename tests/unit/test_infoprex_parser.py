import io

import pandas as pd
import pytest

from orders_master.constants import Columns
from orders_master.exceptions import InfoprexSchemaError
from orders_master.ingestion.infoprex_parser import parse_infoprex_file


@pytest.fixture
def infoprex_mini_content():
    header = (
        "CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\t"
        + "\t".join([f"V{i}" for i in range(15)])
        + "\n"
    )
    rows = [
        "1234567\tPROD1\tIlha\t10\t10.5\t8.0\t01/01/2026\t10/2026\tLAB1\t15/05/2026\t"
        + "\t".join(["1"] * 15),
        "1234567\tPROD1\tColmeias\t5\t10.5\t8.0\t01/01/2026\t10/2026\tLAB1\t14/05/2026\t"
        + "\t".join(["0"] * 15),
        "1000000\tLOCALPROD\tIlha\t0\t5.0\t4.0\t\t\tLAB2\t15/05/2026\t" + "\t".join(["0"] * 15),
        "ABCDEFG\tINVALID_CODE\tIlha\t1\t1.0\t0.5\t\t\tLAB1\t15/05/2026\t" + "\t".join(["0"] * 15),
        "7654321\tPROD3\tIlha\t0\t20.0\t15.0\t\t\tLAB3\t15/05/2026\t" + "\t".join(["2"] * 15),
    ]
    return header + "\n".join(rows)


def test_infoprex_parser_full_parsing(infoprex_mini_content):
    file_like = io.BytesIO(infoprex_mini_content.encode("utf-16"))
    file_like.name = "Guia.txt"

    lista_cla = []
    lista_codigos = []
    locations_aliases = {"ilha": "Farmácia da Ilha", "colmeias": "Farmácia Colmeias"}

    df, entry = parse_infoprex_file(file_like, lista_cla, lista_codigos, locations_aliases)

    # Múltiplas localizações → filtra pela com DUV.max() (Ilha)
    assert entry.farmacia == "Ilha"
    assert "Colmeias" not in df[Columns.LOCALIZACAO].values

    # Colunas renomeadas e '1' não é descartado
    assert Columns.CODIGO in df.columns
    assert 1234567 in df[Columns.CODIGO].values
    assert 1000000 in df[Columns.CODIGO].values

    # 'ABCDEFG' é inválido e removido
    assert "ABCDEFG" not in df[Columns.CODIGO].astype(str).values
    assert "Códigos inválidos ignorados: 1" in entry.avisos

    # 15 meses de nomes invertidos (V14 -> V0) com sufixos
    assert "MAR" in df.columns  # V14
    assert "ABR" in df.columns  # V13
    assert "MAI" in df.columns  # V12
    assert "MAR.1" in df.columns  # V2
    assert "ABR.1" in df.columns  # V1
    assert "MAI.1" in df.columns  # V0

    # T Uni calculado
    assert Columns.T_UNI in df.columns
    assert df.loc[df[Columns.CODIGO] == 1234567, Columns.T_UNI].iloc[0] == 15
    assert df.loc[df[Columns.CODIGO] == 7654321, Columns.T_UNI].iloc[0] == 30


def test_infoprex_schema_error():
    content = "NOM\tLOCALIZACAO\tDUV\nPROD1\tIlha\t15/05/2026"
    file_like = io.BytesIO(content.encode("utf-16"))
    file_like.name = "Bad.txt"
    with pytest.raises(InfoprexSchemaError) as excinfo:
        parse_infoprex_file(file_like, [], [], {})
    assert "CPR" in str(excinfo.value)

    content = "CPR\tNOM\tLOCALIZACAO\n1234567\tPROD1\tIlha"
    file_like = io.BytesIO(content.encode("utf-16"))
    file_like.name = "Bad.txt"
    with pytest.raises(InfoprexSchemaError) as excinfo:
        parse_infoprex_file(file_like, [], [], {})
    assert "DUV" in str(excinfo.value)


def test_infoprex_filter_txt(infoprex_mini_content):
    file_like = io.BytesIO(infoprex_mini_content.encode("utf-16"))
    file_like.name = "Guia.txt"
    # TXT filter prioritário sobre CLA
    df, _ = parse_infoprex_file(file_like, ["LAB3"], [1234567], {})
    assert len(df) == 1
    assert df.iloc[0][Columns.CODIGO] == 1234567


def test_infoprex_filter_cla(infoprex_mini_content):
    file_like = io.BytesIO(infoprex_mini_content.encode("utf-16"))
    file_like.name = "Guia.txt"
    df, _ = parse_infoprex_file(file_like, ["LAB3"], [], {})
    assert len(df) == 1
    assert df.iloc[0][Columns.CODIGO] == 7654321


def test_infoprex_idempotency(infoprex_mini_content):
    file_like1 = io.BytesIO(infoprex_mini_content.encode("utf-16"))
    file_like1.name = "Guia.txt"
    df1, _ = parse_infoprex_file(file_like1, [], [], {})

    file_like2 = io.BytesIO(infoprex_mini_content.encode("utf-16"))
    file_like2.name = "Guia.txt"
    df2, _ = parse_infoprex_file(file_like2, [], [], {})

    pd.testing.assert_frame_equal(df1, df2)
