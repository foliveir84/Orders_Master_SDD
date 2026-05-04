from enum import StrEnum


class Columns(StrEnum):
    """Nomes de colunas usados no sistema."""

    # Colunas Base
    CODIGO = "CÓDIGO"
    DESIGNACAO = "DESIGNAÇÃO"
    LOCALIZACAO = "LOCALIZACAO"
    STOCK = "STOCK"
    PVP = "PVP"
    PVP_MEDIO = "PVP_Médio"
    P_CUSTO = "P.CUSTO"
    P_CUSTO_MEDIO = "P.CUSTO_Médio"
    T_UNI = "T Uni"
    DUC = "DUC"
    DTVAL = "DTVAL"
    CLA = "CLA"

    # Colunas de Integração
    DIR = "DIR"  # Data de Início de Rutura
    DPR = "DPR"  # Data Prevista de Reposição
    DATA_OBS = "DATA_OBS"  # Data de marcação em "Não Comprar"
    TIME_DELTA = "TimeDelta"  # Dias até à reposição

    # Colunas de Cálculo e Lógica
    PROPOSTA = "Proposta"
    MEDIA = "Media"
    PRICE_ANOMALY = "price_anomaly"
    MARCA = "MARCA"
    SORT_KEY = "_sort_key"


class GroupLabels(StrEnum):
    """Rótulos usados para agrupamento."""

    GROUP_ROW = "Grupo"


class Weights:
    """Pesos da média ponderada para os diferentes presets."""

    CONSERVADOR = (0.5, 0.3, 0.15, 0.05)
    PADRAO = (0.4, 0.3, 0.2, 0.1)
    AGRESSIVO = (0.25, 0.25, 0.25, 0.25)


class Highlight:
    """Cores hexadecimais para formatação condicional."""

    GRUPO_BG = "#000000"
    GRUPO_FG = "#FFFFFF"
    NAO_COMPRAR_BG = "#E6D5F5"
    RUTURA_BG = "#FF0000"
    RUTURA_FG = "#FFFFFF"
    VALIDADE_BG = "#FFA500"


class Limits:
    """Limites e valores de configuração do sistema."""

    MESES_PREVISAO_MIN = 1.0
    MESES_PREVISAO_MAX = 6.0
    MESES_PREVISAO_STEP = 0.1
    MESES_PREVISAO_DEFAULT = 1.0

    VALIDADE_ALERTA_MESES = 4

    # Número de meses usados no cálculo da média (janela base)
    MEDIA_WINDOW_SIZE = 4
