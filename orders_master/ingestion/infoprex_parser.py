import typing

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta  # type: ignore

from orders_master.app_services.session_state import FileInventoryEntry
from orders_master.business_logic.price_validation import flag_price_anomalies
from orders_master.config.locations_loader import map_location
from orders_master.constants import Columns
from orders_master.exceptions import InfoprexSchemaError
from orders_master.ingestion.encoding_fallback import try_read_with_fallback_encodings


def compute_nome_mes(offset: int, data_max: pd.Timestamp) -> str:
    meses_pt = {
        1: "JAN",
        2: "FEV",
        3: "MAR",
        4: "ABR",
        5: "MAI",
        6: "JUN",
        7: "JUL",
        8: "AGO",
        9: "SET",
        10: "OUT",
        11: "NOV",
        12: "DEZ",
    }
    mes_alvo = data_max - relativedelta(months=offset)
    return meses_pt[mes_alvo.month]


def parse_infoprex_file(
    file_like: typing.Any,
    lista_cla: list[str],
    lista_codigos: list[int],
    locations_aliases: dict[str, str],
) -> tuple[pd.DataFrame, FileInventoryEntry]:

    base_cols = ["CPR", "NOM", "LOCALIZACAO", "SAC", "PVP", "PCU", "DUC", "DTVAL", "CLA", "DUV"]
    vendas_cols = [f"V{i}" for i in range(15)]
    colunas_alvo = set(base_cols + vendas_cols)

    df = try_read_with_fallback_encodings(file_like, sep="\t", usecols=lambda c: c in colunas_alvo)

    filename = getattr(file_like, "name", "desconhecido")

    if "CPR" not in df.columns or "DUV" not in df.columns:
        raise InfoprexSchemaError(
            f"Colunas estruturais em falta no ficheiro {filename}. Esperado: CPR, DUV"
        )

    vendas_presentes = [c for c in vendas_cols if c in df.columns]

    df["DUV_dt"] = pd.to_datetime(df["DUV"], format="%d/%m/%Y", errors="coerce")
    data_max = df["DUV_dt"].max()

    if pd.isna(data_max):
        df_filtered = df.copy()
        localizacao_alvo = ""
    else:
        localizacao_alvo = df.loc[df["DUV_dt"] == data_max, "LOCALIZACAO"].iloc[0]
        df_filtered = df[df["LOCALIZACAO"] == localizacao_alvo].copy()

    df_filtered = df_filtered.drop(columns=["DUV_dt"])

    if lista_codigos:
        df_filtered = df_filtered[
            df_filtered["CPR"].astype(str).str.strip().isin([str(c) for c in lista_codigos])
        ]
    elif lista_cla and "CLA" in df_filtered.columns:
        lista_cla_lower = [c.strip().lower() for c in lista_cla]
        df_filtered = df_filtered[
            df_filtered["CLA"].astype(str).str.strip().str.lower().isin(lista_cla_lower)
        ]

    vendas_invertidas = vendas_presentes[::-1]
    out_cols = [c for c in base_cols if c in df_filtered.columns] + vendas_invertidas
    df_filtered = df_filtered[out_cols].copy()

    df_filtered["T Uni"] = df_filtered[vendas_invertidas].fillna(0).sum(axis=1).astype(int)

    meses_vistos: dict[str, int] = {}
    rename_dict = {}

    for col_v in vendas_presentes:
        offset = int(col_v[1:])
        if pd.isna(data_max):
            rename_dict[col_v] = col_v
            continue

        nome_mes = compute_nome_mes(offset, data_max)
        count = meses_vistos.get(nome_mes, 0)
        novo_nome = f"{nome_mes}.{count}" if count > 0 else nome_mes
        meses_vistos[nome_mes] = count + 1
        rename_dict[col_v] = novo_nome

    df_filtered = df_filtered.rename(columns=rename_dict)

    rename_base = {
        "CPR": Columns.CODIGO,
        "NOM": Columns.DESIGNACAO,
        "SAC": Columns.STOCK,
        "PCU": Columns.P_CUSTO,
        "PVP": Columns.PVP,
        "DUC": Columns.DUC,
        "DTVAL": Columns.DTVAL,
        "CLA": Columns.CLA,
        "LOCALIZACAO": Columns.LOCALIZACAO,
    }
    df_filtered = df_filtered.rename(columns=rename_base)

    invalid_codes = []

    def convert_code(val: typing.Any) -> typing.Any:
        s = str(val).strip()
        if s.isdigit():
            return int(s)
        invalid_codes.append(s)
        return np.nan

    df_filtered[Columns.CODIGO] = df_filtered[Columns.CODIGO].apply(convert_code)
    df_filtered = df_filtered.dropna(subset=[Columns.CODIGO])
    df_filtered[Columns.CODIGO] = df_filtered[Columns.CODIGO].astype(int)

    if Columns.LOCALIZACAO in df_filtered.columns:
        df_filtered[Columns.LOCALIZACAO] = df_filtered[Columns.LOCALIZACAO].apply(
            lambda x: map_location(str(x), locations_aliases) if pd.notna(x) else ""
        )

    # Garantir que todas as colunas de vendas são numéricas
    for col_v in vendas_presentes:
        if col_v in df_filtered.columns:
            # Converter para string, trocar vírgula por ponto e depois para numérico
            df_filtered[col_v] = (
                df_filtered[col_v]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.strip()
            )
            df_filtered[col_v] = pd.to_numeric(df_filtered[col_v], errors="coerce").fillna(0.0)

    if Columns.STOCK in df_filtered.columns:
        df_filtered[Columns.STOCK] = (
            df_filtered[Columns.STOCK]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df_filtered[Columns.STOCK] = (
            pd.to_numeric(df_filtered[Columns.STOCK], errors="coerce").fillna(0).astype(int)
        )
    if Columns.PVP in df_filtered.columns:
        df_filtered[Columns.PVP] = (
            df_filtered[Columns.PVP]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df_filtered[Columns.PVP] = pd.to_numeric(df_filtered[Columns.PVP], errors="coerce").fillna(
            0.0
        )
    if Columns.P_CUSTO in df_filtered.columns:
        df_filtered[Columns.P_CUSTO] = (
            df_filtered[Columns.P_CUSTO]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df_filtered[Columns.P_CUSTO] = pd.to_numeric(
            df_filtered[Columns.P_CUSTO], errors="coerce"
        ).fillna(0.0)

    df_filtered = flag_price_anomalies(df_filtered)

    if "DUV" in df_filtered.columns:
        df_filtered = df_filtered.drop(columns=["DUV"])

    duv_max_str = data_max.strftime("%d-%m-%Y") if pd.notna(data_max) else ""

    entry = FileInventoryEntry(
        filename=filename,
        farmacia=localizacao_alvo,
        n_linhas=len(df_filtered),
        duv_max=duv_max_str,
        status="ok",
        error_message="",
    )

    if invalid_codes:
        entry.avisos = f"Códigos inválidos ignorados: {len(invalid_codes)}"

    return df_filtered, entry
