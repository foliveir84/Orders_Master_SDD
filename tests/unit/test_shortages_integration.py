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
