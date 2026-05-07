"""
tests/integration/test_boundary_year.py — TASK-37.

Valida a renomeação de colunas de meses quando o histórico atravessa fronteiras de ano
ou ultrapassa 12 meses (gerando sufixos .1).
"""

import io

from orders_master.ingestion.infoprex_parser import parse_infoprex_file


def test_month_names_across_years():
    """
    Testa se DUV em Janeiro de 2026 com 15 meses gera nomes correctos
    (JAN a JAN.1).
    """
    # Header com 15 colunas de vendas (V0 a V14)
    v_cols = "\t".join([f"V{i}" for i in range(15)])
    v_data = "\t".join(["1"] * 15)

    header = f"CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\t{v_cols}\n"
    # DUV = 15/01/2026
    row = f"1234567\tPROD\tLOC1\t10\t20.0\t15.0\t100\t2026-01-01\tLAB1\t15/01/2026\t{v_data}\n"
    content = (header + row).encode("utf-16")

    file_like = io.BytesIO(content)
    file_like.name = "test_boundary.txt"

    df, _ = parse_infoprex_file(file_like, [], [], {})

    # Ordem esperada (vendas_invertidas: V14, V13, ..., V0)
    # V14: NOV.1
    # V13: DEZ.1
    # V12: JAN.1
    # ...
    # V1: DEZ
    # V0: JAN

    cols = list(df.columns)

    # Meses devem estar no fim (antes de T Uni que é adicionado depois)
    # Na verdade, o parser coloca as colunas base + vendas_invertidas

    assert "JAN" in cols
    assert "JAN.1" in cols
    assert "DEZ" in cols
    assert "DEZ.1" in cols
    assert "NOV.1" in cols

    # Verificar ordem posicional no df_filtered (antes do aggregator)
    # O parser faz: base_cols + vendas_invertidas
    # Vendas invertidas = V14, V13, ..., V0
    idx_v14 = cols.index("NOV.1")
    idx_v0 = cols.index("JAN")

    assert idx_v14 < idx_v0
    assert cols[idx_v0 - 1] == "DEZ"
    assert cols[idx_v0 - 12] == "JAN.1"


def test_no_duplicate_month_names_collision():
    """Garante que não há colisões de nomes se tivermos muitos meses."""
    v_cols = "\t".join([f"V{i}" for i in range(5)])  # 0,1,2,3,4
    v_data = "\t".join(["1"] * 5)
    header = f"CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\t{v_cols}\n"
    row = f"123\tP\tL\t1\t1\t1\t1\t1\t1\t15/01/2026\t{v_data}\n"
    content = (header + row).encode("utf-16")

    df, _ = parse_infoprex_file(io.BytesIO(content), [], [], {})

    # V0=JAN, V1=DEZ, V2=NOV, V3=OUT, V4=SET
    assert "JAN" in df.columns
    assert "DEZ" in df.columns
    assert "SET" in df.columns
    assert len(df.columns) == len(set(df.columns))  # Sem duplicados
