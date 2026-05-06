from dataclasses import dataclass, field

import pandas as pd

from orders_master.exceptions import FileError


@dataclass(slots=True)
class ScopeContext:
    """Contexto do âmbito actual para exibição na UI."""

    n_produtos: int = 0
    n_farmacias: int = 0
    descricao_filtro: str = ""
    primeiro_mes: str = ""
    ultimo_mes: str = ""
    ano_range: str = ""
    meses: float = 0.0
    modo: str = ""


@dataclass(slots=True)
class FileInventoryEntry:
    """Entrada no inventário de ficheiros processados."""

    filename: str
    farmacia: str = ""
    n_linhas: int = 0
    duv_max: str = ""
    avisos: str = ""
    status: str = "ok"  # "ok" | "error"
    error_message: str = ""


@dataclass(slots=True)
class SessionState:
    """
    Estado da sessão da aplicação.
    Esta é uma dataclass pura que pode ser usada fora do Streamlit.
    """

    df_raw: pd.DataFrame = field(default_factory=pd.DataFrame)
    df_aggregated: pd.DataFrame = field(default_factory=pd.DataFrame)
    df_detailed: pd.DataFrame = field(default_factory=pd.DataFrame)
    master_products: pd.DataFrame = field(default_factory=pd.DataFrame)
    last_labs_selection: list[str] | None = None
    last_brands_selection: list[str] = field(default_factory=list)
    last_codes_file_name: str | None = None
    file_errors: list[FileError] = field(default_factory=list)
    invalid_codes: list[str] = field(default_factory=list)
    file_inventory: list[FileInventoryEntry] = field(default_factory=list)
    scope_context: ScopeContext = field(default_factory=ScopeContext)


def get_state() -> SessionState:
    """
    Obtém o estado da sessão actual.
    Faz lazy-init em st.session_state se o Streamlit estiver disponível.
    Caso contrário, devolve uma nova instância de SessionState (útil para testes).
    """
    try:
        import streamlit as st  # noqa: PLC0415

        if "orders_master_state" not in st.session_state:
            st.session_state["orders_master_state"] = SessionState()

        # Garantir que o retorno é do tipo SessionState (ajuda o mypy)
        state: SessionState = st.session_state["orders_master_state"]
        return state
    except ImportError:
        # Fallback para ambiente sem Streamlit (testes unitários)
        return SessionState()


def reset_state() -> None:
    """Limpa o estado da sessão actual no Streamlit."""
    try:
        import streamlit as st  # noqa: PLC0415

        if "orders_master_state" in st.session_state:
            del st.session_state["orders_master_state"]
    except ImportError:
        pass
