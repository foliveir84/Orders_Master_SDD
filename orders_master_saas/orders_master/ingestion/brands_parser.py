from typing import Any

import pandas as pd

from orders_master.schemas import BrandRecordSchema


def parse_brands_csv(files_like: list[Any]) -> pd.DataFrame:
    """
    Lê múltiplos ficheiros CSV de marcas (Infoprex_SIMPLES), consolida-os
    e deduplica por código de produto.

    Pipeline:
    1. Lê cada ficheiro com separador ';' e colunas COD, MARCA.
    2. Consolida todos num único DataFrame.
    3. Limpa e normaliza os dados (strings, NAs).
    4. Converte COD para inteiro, descartando não-numéricos.
    5. Deduplica por COD, mantendo a primeira ocorrência.

    Args:
        files_like (List[Any]): Lista de objectos tipo ficheiro (suportam read()).

    Returns:
        pd.DataFrame: DataFrame com colunas COD (int) e MARCA (str).
    """
    if not files_like:
        return pd.DataFrame(columns=["COD", "MARCA"])

    dfs = []
    for file_like in files_like:
        try:
            # Tenta ler o ficheiro - UploadedFile do Streamlit suporta seek(0) se necessário
            if hasattr(file_like, "seek"):
                file_like.seek(0)

            df = pd.read_csv(
                file_like,
                sep=";",
                usecols=["COD", "MARCA"],
                dtype=str,
                on_bad_lines="skip",
                encoding="utf-8",
            )
            dfs.append(df)
        except Exception:
            # Defesa contra ficheiros corrompidos ou schemas inválidos
            continue

    if not dfs:
        return pd.DataFrame(columns=["COD", "MARCA"])

    # 2. Concat
    df_brands = pd.concat(dfs, ignore_index=True)

    # 3. Limpeza de strings e NAs
    df_brands["MARCA"] = df_brands["MARCA"].str.strip()

    # Substituir strings vazias ou nulas por pd.NA
    df_brands.loc[df_brands["MARCA"].isin(["", "nan", "None", "None"]), "MARCA"] = pd.NA

    # Drop NAs na marca
    df_brands = df_brands.dropna(subset=["MARCA"])

    # 4. Converter COD para numérico, drop não-convertíveis
    df_brands["COD"] = pd.to_numeric(df_brands["COD"], errors="coerce")
    df_brands = df_brands.dropna(subset=["COD"])

    # 5. Converter COD para int
    df_brands["COD"] = df_brands["COD"].astype(int)

    # 6. Deduplicar mantendo a primeira MARCA vista
    df_brands = df_brands.drop_duplicates(subset=["COD"], keep="first")

    # Validar schema na fronteira de saída
    BrandRecordSchema.validate_df(df_brands)

    return df_brands
