import pytest
import pandas as pd
from datetime import datetime
from orders_master.integrations.donotbuy import fetch_donotbuy_list, merge_donotbuy
from orders_master.constants import Columns

def test_fetch_donotbuy_list_success(monkeypatch):
    mock_df = pd.DataFrame({
        "CNP": ["123", "123", "456"],
        "FARMACIA": ["ilha", "ilha", "Souto"],
        "DATA": ["01-05-2026", "10-05-2026", "05-05-2026"]
    })
    
    aliases = {"ilha": "Ilha", "souto": "Souto"}
    
    monkeypatch.setattr("pandas.read_excel", lambda *args, **kwargs: mock_df)
    
    df = fetch_donotbuy_list("http://mock-url-1", aliases)
    
    assert not df.empty
    assert len(df) == 2  # Dedup de CNP+FARMACIA deve manter a mais recente
    
    # Verifica se "ilha" foi mapeada para "Ilha"
    assert "Ilha" in df["FARMACIA"].values
    
    # Verifica se a data mais recente foi mantida para "123" e "Ilha"
    row_123 = df[df["CNP"] == "123"].iloc[0]
    assert row_123["DATA"].strftime("%d-%m-%Y") == "10-05-2026"

def test_fetch_donotbuy_list_http_error(monkeypatch):
    def mock_raise(*args, **kwargs):
        raise Exception("HTTP 500")
    monkeypatch.setattr("pandas.read_excel", mock_raise)
    
    df = fetch_donotbuy_list("http://mock-url-2", {})
    assert df.empty
    assert "CNP" in df.columns

def test_fetch_donotbuy_list_schema_error(monkeypatch):
    mock_df = pd.DataFrame({"CNP": ["123"]}) # Missing columns
    monkeypatch.setattr("pandas.read_excel", lambda *args, **kwargs: mock_df)
    
    df = fetch_donotbuy_list("http://mock-url-3", {})
    assert df.empty
    assert "CNP" in df.columns

def test_merge_donotbuy_aggregated():
    df_sell_out = pd.DataFrame({
        "CÓDIGO": [123, 456, 789]
    })
    
    df_donotbuy = pd.DataFrame({
        "CNP": ["123", "123", "456"],
        "FARMACIA": ["Ilha", "Souto", "Ilha"],
        "DATA": pd.to_datetime(["2026-05-01", "2026-05-15", "2026-05-10"])
    })
    
    # No merge agrupado, deve deduplicar CNP e manter a DATA mais recente, independentemente da farmácia
    df_out = merge_donotbuy(df_sell_out, df_donotbuy, detailed=False)
    
    assert Columns.DATA_OBS in df_out.columns
    assert "CNP" not in df_out.columns
    
    # Para o 123, a data mais recente é 2026-05-15
    assert df_out.loc[df_out["CÓDIGO"] == 123, Columns.DATA_OBS].iloc[0] == "15-05-2026"
    # Para o 456, é 2026-05-10
    assert df_out.loc[df_out["CÓDIGO"] == 456, Columns.DATA_OBS].iloc[0] == "10-05-2026"
    # Para o 789, pd.NA
    assert pd.isna(df_out.loc[df_out["CÓDIGO"] == 789, Columns.DATA_OBS].iloc[0])

def test_merge_donotbuy_detailed():
    df_sell_out = pd.DataFrame({
        "CÓDIGO": [123, 123, 456],
        "LOCALIZACAO": ["Ilha", "Souto", "Ilha"]
    })
    
    df_donotbuy = pd.DataFrame({
        "CNP": ["123", "456"],
        "FARMACIA": ["Ilha", "Souto"],
        "DATA": pd.to_datetime(["2026-05-01", "2026-05-10"])
    })
    
    df_out = merge_donotbuy(df_sell_out, df_donotbuy, detailed=True)
    
    assert Columns.DATA_OBS in df_out.columns
    
    # 123 na Ilha -> 2026-05-01
    mask_123_ilha = (df_out["CÓDIGO"] == 123) & (df_out["LOCALIZACAO"] == "Ilha")
    assert df_out.loc[mask_123_ilha, Columns.DATA_OBS].iloc[0] == "01-05-2026"
    
    # 123 no Souto -> NA (não está na lista Não Comprar)
    mask_123_souto = (df_out["CÓDIGO"] == 123) & (df_out["LOCALIZACAO"] == "Souto")
    assert pd.isna(df_out.loc[mask_123_souto, Columns.DATA_OBS].iloc[0])
    
    # 456 na Ilha -> NA (a lista tem 456 no Souto)
    mask_456_ilha = (df_out["CÓDIGO"] == 456) & (df_out["LOCALIZACAO"] == "Ilha")
    assert pd.isna(df_out.loc[mask_456_ilha, Columns.DATA_OBS].iloc[0])

def test_merge_donotbuy_empty():
    df_sell_out = pd.DataFrame({"CÓDIGO": [123]})
    df_donotbuy = pd.DataFrame(columns=["CNP", "FARMACIA", "DATA"])
    
    df_out = merge_donotbuy(df_sell_out, df_donotbuy, detailed=False)
    assert Columns.DATA_OBS in df_out.columns
    assert pd.isna(df_out[Columns.DATA_OBS].iloc[0])
