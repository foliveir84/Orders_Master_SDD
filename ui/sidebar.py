"""
ui/sidebar.py — Bloco de controlo lateral (§6.1.2).

Implementa ``render_sidebar()`` que devolve uma ``SidebarSelection`` tipada
com todos os inputs do utilizador (ficheiros, labs, botão de processar).
"""
from dataclasses import dataclass, field
from typing import Any

import streamlit as st


@dataclass
class SidebarSelection:
    """Captura todos os inputs da sidebar num objecto tipado."""

    labs_selected: list[str] = field(default_factory=list)
    codes_file: Any = None  # UploadedFile | None
    infoprex_files: list[Any] = field(default_factory=list)  # list[UploadedFile]
    brands_files: list[Any] = field(default_factory=list)  # list[UploadedFile]
    processar_clicked: bool = False


def render_sidebar(labs_options: list[str]) -> SidebarSelection:
    """
    Renderiza a barra lateral com os 4 blocos de input conforme PRD §6.1.2.

    Args:
        labs_options: Lista ordenada de laboratórios disponíveis.

    Returns:
        SidebarSelection com todos os inputs capturados.
    """
    with st.sidebar:
        st.markdown("## ⚙️ Configuração")
        st.markdown("---")

        # Bloco 1 — Filtrar por Laboratório
        st.markdown("### 🏭 Laboratórios")
        labs_selected: list[str] = st.multiselect(
            "Filtrar por Laboratório",
            options=sorted(labs_options),
            help="Filtra os produtos pelos laboratórios seleccionados.",
        )
        st.markdown("---")

        # Bloco 2 — Ficheiro de Códigos CNP
        st.markdown("### 🔢 Filtrar por Códigos")
        codes_file = st.file_uploader(
            "Filtrar por Códigos",
            type=["txt"],
            help="Lista de CNPs, um por linha. Tem prioridade sobre Laboratórios.",
        )
        st.caption("Tem prioridade sobre Laboratórios")
        st.markdown("---")

        # Bloco 3 — Dados Base Infoprex
        st.markdown("### 📂 Dados Infoprex")
        infoprex_files = st.file_uploader(
            "Dados Base Infoprex",
            type=["txt"],
            accept_multiple_files=True,
            help="Exportações do módulo Infoprex (UTF-16, separador Tab).",
        )
        st.markdown("---")

        # Bloco 4 — Base de Marcas
        st.markdown("### 🏷️ Base de Marcas")
        brands_files = st.file_uploader(
            "Base de Marcas",
            type=["csv"],
            accept_multiple_files=True,
            help="CSVs com colunas COD e MARCA (separador ;).",
        )
        st.markdown("---")

        # Botão de Processar
        processar_clicked: bool = st.button(
            "🚀 Processar Dados",
            type="primary",
            use_container_width=True,
        )

    return SidebarSelection(
        labs_selected=labs_selected,
        codes_file=codes_file,
        infoprex_files=list(infoprex_files) if infoprex_files else [],
        brands_files=list(brands_files) if brands_files else [],
        processar_clicked=processar_clicked,
    )
