from datetime import datetime, timedelta

import pandas as pd

from orders_master.integrations.shortages import fetch_shortages_db, merge_shortages


def test_fetch_shortages_db_success(monkeypatch):
    today = datetime.now()
    dpr = today + timedelta(days=30)

    mock_df = pd.DataFrame(
        {
            "Número de registo": ["123", "456"],
            "Data de início de rutura": [today - timedelta(days=10), today - timedelta(days=5)],
            "Data prevista para reposição": [dpr, dpr + timedelta(days=10)],
            "Data da Consulta": ["2026-05-06", "2026-05-06"],
        }
    )

    monkeypatch.setattr("pandas.read_excel", lambda *args, **kwargs: mock_df)

    df = fetch_shortages_db("http://mock-url-1")
    assert not df.empty
    assert "TimeDelta" in df.columns
    assert df.loc[df["Número de registo"] == "123", "TimeDelta"].iloc[0] == 30
    assert "Data da Consulta" in df.columns
    assert df["Data da Consulta"].iloc[0] == "2026-05-06"


def test_fetch_shortages_db_lazy_filter(monkeypatch):
    mock_df = pd.DataFrame(
        {
            "Número de registo": ["123", "456", "789"],
            "Data de início de rutura": [datetime.now(), datetime.now(), datetime.now()],
            "Data prevista para reposição": [datetime.now(), datetime.now(), datetime.now()],
        }
    )

    monkeypatch.setattr("pandas.read_excel", lambda *args, **kwargs: mock_df)

    df = fetch_shortages_db("http://mock-url-2", codigos_visible={123, 789})
    assert len(df) == 2
    assert "456" not in df["Número de registo"].values


def test_fetch_shortages_db_http_error(monkeypatch):
    def mock_raise(*args, **kwargs):
        raise Exception("HTTP 404")

    monkeypatch.setattr("pandas.read_excel", mock_raise)

    df = fetch_shortages_db("http://mock-url-3")
    assert df.empty
    assert "Número de registo" in df.columns
    assert "TimeDelta" in df.columns


def test_fetch_shortages_db_schema_error(monkeypatch):
    mock_df = pd.DataFrame(
        {
            "Número de registo": ["123"],
            # Missing other required columns
        }
    )
    monkeypatch.setattr("pandas.read_excel", lambda *args, **kwargs: mock_df)

    df = fetch_shortages_db("http://mock-url-4")
    assert df.empty
    assert "TimeDelta" in df.columns


def test_merge_shortages():
    today = datetime.now()
    dpr_1 = today + timedelta(days=30)
    dpr_2 = today + timedelta(days=31)

    df_sell_out = pd.DataFrame({"CÓDIGO": [123, 456, 999], "STOCK": [5, 10, 0]})

    df_shortages = pd.DataFrame(
        {
            "Número de registo": ["123", "456"],
            "Data de início de rutura": pd.to_datetime(["2026-05-01", "2026-05-02"]),
            "Data prevista para reposição": pd.to_datetime([dpr_1, dpr_2]),
            "TimeDelta": [30, 31],  # valor original da sheet (descartado e recalculado)
            "Data da Consulta": ["2026-05-06", "2026-05-06"],
            "Nome do medicamento": ["A", "B"],
        }
    )

    df_out = merge_shortages(df_sell_out, df_shortages)

    # Check if DIR and DPR are correctly formatted
    assert "DIR" in df_out.columns
    assert "DPR" in df_out.columns
    assert df_out.loc[df_out["CÓDIGO"] == 123, "DIR"].iloc[0] == "01-05-2026"
    assert df_out.loc[df_out["CÓDIGO"] == 123, "DPR"].iloc[0] == dpr_1.strftime("%d-%m-%Y")

    # Check if auxiliary columns were dropped
    assert "Data da Consulta" not in df_out.columns
    assert "Nome do medicamento" not in df_out.columns
    assert "Número de registo" not in df_out.columns

    # TimeDelta é recalculado dinamicamente a partir de DPR (Opção C)
    assert "TimeDelta" in df_out.columns
    assert df_out.loc[df_out["CÓDIGO"] == 123, "TimeDelta"].iloc[0] == 30
    assert df_out.loc[df_out["CÓDIGO"] == 456, "TimeDelta"].iloc[0] == 31
    assert pd.isna(df_out.loc[df_out["CÓDIGO"] == 999, "TimeDelta"].iloc[0])


def test_merge_shortages_preserves_timedelta_when_preinitialized():
    """Reproduz o bug do session_service: TimeDelta=NA pre-inicializado em df_sell_out.

    Contexto: session_service.py:62-64 pre-inicializa TimeDelta=pd.NA em df_full
    ANTES de chamar merge_shortages. Isto causava colisao de nomes no merge do pandas
    (TimeDelta_x / TimeDelta_y) e o TimeDelta real de df_shortages era perdido.

    Cenario real: produto 5678321 com DPR=30-10-2026, TimeDelta esperado=122 dias.
    Sintoma: compute_shortage_proposal retorna early (TimeDelta nao existe) e usa
    formula base em vez da formula de ruptura.

    Fix: merge_shortages agora recalcula TimeDelta a partir de "Data prevista para
    reposição" (Opção C), independendo de colisões de merge.
    """
    today = datetime.now()
    dpr_1 = today + timedelta(days=30)
    dpr_2 = today + timedelta(days=31)

    # df_sell_out COM TimeDelta pre-inicializado (simula session_service.py:62-64)
    df_sell_out = pd.DataFrame(
        {
            "CÓDIGO": [123, 456, 999],
            "STOCK": [5, 10, 0],
            "DIR": [pd.NA, pd.NA, pd.NA],
            "DPR": [pd.NA, pd.NA, pd.NA],
            "TimeDelta": [pd.NA, pd.NA, pd.NA],
        }
    )

    df_shortages = pd.DataFrame(
        {
            "Número de registo": ["123", "456"],
            "Data de início de rutura": pd.to_datetime(["2026-05-01", "2026-05-02"]),
            "Data prevista para reposição": pd.to_datetime([dpr_1, dpr_2]),
            "TimeDelta": [30, 31],  # valor original da sheet (descartado e recalculado)
            "Data da Consulta": ["2026-05-06", "2026-05-06"],
        }
    )

    df_out = merge_shortages(df_sell_out, df_shortages)

    # TimeDelta deve estar presente (nao colidido/dropped)
    assert "TimeDelta" in df_out.columns, (
        "TimeDelta foi perdido no merge! Colisao de nomes com df_sell_out pre-inicializado. "
        f"Colunas actuais: {list(df_out.columns)}"
    )
    # Valores recalculados a partir de DPR (Opção C)
    assert df_out.loc[df_out["CÓDIGO"] == 123, "TimeDelta"].iloc[0] == 30, (
        f"TimeDelta deveria ser 30 (recalculado de DPR), obtido: "
        f"{df_out.loc[df_out['CÓDIGO'] == 123, 'TimeDelta'].iloc[0]}"
    )
    assert df_out.loc[df_out["CÓDIGO"] == 456, "TimeDelta"].iloc[0] == 31
    # Produto sem match deve ter TimeDelta NaN
    assert pd.isna(df_out.loc[df_out["CÓDIGO"] == 999, "TimeDelta"].iloc[0])


def test_merge_shortages_timedelta_numeric_dtype_with_mixed_nulls():
    """TimeDelta deve ter dtype numérico (não object) quando há mix de matches e não-matches.

    Contexto: em produção, df_full tem ~650 produtos mas só alguns têm match na BD
    Esgotados. O meu fix inicial usava `.apply(lambda x: x.days if pd.notnull(x) else pd.NA)`
    que produz dtype OBJECT quando há mistura de int e pd.NA. Isto fazia o
    `compute_shortage_proposal` falhar com `TypeError: Expected numeric dtype, got object
    instead` no `.round(0)`, derrubando a app em produção.

    Sintoma real (streamlit app 2026-06-30):
      TypeError: Expected numeric dtype, got object instead.
        em compute_shortage_proposal:71 (.round(0))

    Causa: o dtype object não suporta operações vectorizadas numéricas (.round, astype int).
    Contramedida: usar subtracção vectorizada (dpr - pd.Timestamp(today)).dt.days que
    produz float64 com NaN, em vez de .apply(lambda) com pd.NA.
    """
    today = datetime.now()
    dpr_1 = today + timedelta(days=60)
    dpr_2 = today + timedelta(days=30)

    # df_sell_out com 3 produtos (2 com match, 1 sem match -> gera null)
    df_sell_out = pd.DataFrame(
        {
            "CÓDIGO": [1001, 1002, 1003],
            "STOCK": [5, 3, 8],
            "DIR": [pd.NA, pd.NA, pd.NA],
            "DPR": [pd.NA, pd.NA, pd.NA],
            "TimeDelta": [pd.NA, pd.NA, pd.NA],
        }
    )

    df_shortages = pd.DataFrame(
        {
            "Número de registo": ["1001", "1002"],
            "Data de início de rutura": [today - timedelta(days=10), today - timedelta(days=5)],
            "Data prevista para reposição": [dpr_1, dpr_2],
            "TimeDelta": [60, 30],  # valor original (descartado e recalculado)
            "Data da Consulta": ["2026-06-30", "2026-06-30"],
        }
    )

    df_out = merge_shortages(df_sell_out, df_shortages)

    assert "TimeDelta" in df_out.columns
    td_series = df_out["TimeDelta"]
    # dtype deve ser numérico (float64 ou Int64), NUNCA object.
    # Object dtype quebra compute_shortage_proposal (.round(0) falha).
    assert td_series.dtype != object, (
        f"TimeDelta tem dtype object (depreciado)! "
        f"Isto causa TypeError em compute_shortage_proposal. "
        f"Usar subtracção vectorizada em vez de .apply(lambda) com pd.NA. "
        f"Valores: {td_series.tolist()}"
    )
    # Valores correctos
    assert df_out.loc[df_out["CÓDIGO"] == 1001, "TimeDelta"].iloc[0] == 60
    assert df_out.loc[df_out["CÓDIGO"] == 1002, "TimeDelta"].iloc[0] == 30
    assert pd.isna(df_out.loc[df_out["CÓDIGO"] == 1003, "TimeDelta"].iloc[0])


def test_merge_shortages_then_compute_shortage_proposal_multi_row():
    """Teste e2e: merge_shortages -> compute_shortage_proposal com multi-linha.

    Reproduz o crash de producao: quando TimeDelta tem dtype object (mix de int e NA),
    compute_shortage_proposal falha com TypeError no .round(0). Este teste garante que
    o pipeline completo funciona com datasets que têm produtos com E sem ruptura.
    """
    from orders_master.business_logic.proposals import compute_shortage_proposal

    today = datetime.now()
    dpr_1 = today + timedelta(days=60)

    # 3 produtos: 1 com ruptura, 2 sem
    df_sell_out = pd.DataFrame(
        {
            "CÓDIGO": [1001, 1002, 1003],
            "STOCK": [5, 3, 8],
            "Media": [10.0, 20.0, 15.0],
            "Proposta": [5, 17, 7],  # proposta base pré-calculada
            "DIR": [pd.NA, pd.NA, pd.NA],
            "DPR": [pd.NA, pd.NA, pd.NA],
            "TimeDelta": [pd.NA, pd.NA, pd.NA],
        }
    )

    df_shortages = pd.DataFrame(
        {
            "Número de registo": ["1001"],
            "Data de início de rutura": [today - timedelta(days=10)],
            "Data prevista para reposição": [dpr_1],
            "TimeDelta": [60],  # descartado e recalculado
            "Data da Consulta": ["2026-06-30"],
        }
    )

    df_merged = merge_shortages(df_sell_out, df_shortages)

    # Este era o ponto de crash em produção
    df_result = compute_shortage_proposal(df_merged)

    # Produto 1001 (com ruptura): Proposta = round((10/30)*60 - 5) = round(15) = 15
    assert df_result.loc[df_result["CÓDIGO"] == 1001, "Proposta"].iloc[0] == 15, (
        f"Proposta de ruptura errada: "
        f"{df_result.loc[df_result['CÓDIGO'] == 1001, 'Proposta'].iloc[0]}"
    )
    # Produtos sem ruptura: proposta base mantida
    assert df_result.loc[df_result["CÓDIGO"] == 1002, "Proposta"].iloc[0] == 17
    assert df_result.loc[df_result["CÓDIGO"] == 1003, "Proposta"].iloc[0] == 7
