from typing import NamedTuple


class OrdersMasterError(Exception):
    """Base para todas as excepções do domínio."""


class InfoprexEncodingError(OrdersMasterError):
    """Erro lançado quando a codificação do ficheiro Infoprex não é reconhecida."""


class InfoprexSchemaError(OrdersMasterError):
    """Erro lançado quando o ficheiro Infoprex não contém as colunas estruturais esperadas."""


class ConfigError(OrdersMasterError):
    """Erro lançado por falhas na validação de ficheiros de configuração (JSON/YAML)."""


class IntegrationError(OrdersMasterError):
    """Erro lançado por falhas na integração com fontes externas (Google Sheets, etc.)."""


class PriceAnomalyWarning(UserWarning):
    """Aviso emitido quando são detectadas anomalias de preço (PVP <= 0, P.CUSTO <= 0, etc.)."""


class FileError(NamedTuple):
    """
    Representação imutável de um erro num ficheiro específico.

    Attributes:
        filename (str): Nome do ficheiro problemático.
        type (str): Categoria do erro ("encoding", "schema" ou "unknown").
        message (str): Descrição detalhada do erro.
    """

    filename: str
    type: str  # "encoding" | "schema" | "unknown"
    message: str
