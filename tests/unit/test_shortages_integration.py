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
    df_sell_out = pd.DataFrame({"CÓDIGO": [123, 456, 999], "STOCK": [5, 10, 0]})

    df_shortages = pd.DataFrame(
        {
            "Número de registo": ["123", "456"],
            "Data de início de rutura": pd.to_datetime(["2026-05-01", "2026-05-02"]),
            "Data prevista para reposição": pd.to_datetime(["2026-06-01", "2026-06-02"]),
            "TimeDelta": [30, 31],
            "Data da Consulta": ["2026-05-06", "2026-05-06"],
            "Nome do medicamento": ["A", "B"],
        }
    )

    df_out = merge_shortages(df_sell_out, df_shortages)

    # Check if DIR and DPR are correctly formatted
    assert "DIR" in df_out.columns
    assert "DPR" in df_out.columns
    assert df_out.loc[df_out["CÓDIGO"] == 123, "DIR"].iloc[0] == "01-05-2026"
    assert df_out.loc[df_out["CÓDIGO"] == 123, "DPR"].iloc[0] == "01-06-2026"

    # Check if auxiliary columns were dropped
    assert "Data da Consulta" not in df_out.columns
    assert "Nome do medicamento" not in df_out.columns
    assert "Número de registo" not in df_out.columns

    # Check if TimeDelta is preserved
    assert "TimeDelta" in df_out.columns
    assert df_out.loc[df_out["CÓDIGO"] == 123, "TimeDelta"].iloc[0] == 30
    assert pd.isna(df_out.loc[df_out["CÓDIGO"] == 999, "TimeDelta"].iloc[0])
