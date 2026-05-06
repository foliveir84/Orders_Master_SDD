"""
ui/main_area.py — Área principal do dashboard (§6.1.3).

Implementa ``render_main(state)`` que apresenta a área de dados principal:
métricas, tabela agregada/detalhada, erros e inventário de ficheiros.
"""

import streamlit as st

from orders_master.app_services.session_state import SessionState
from ui.scope_bar import render_scope_summary
from ui.sidebar import SidebarSelection


def render_main(state: SessionState, selection: SidebarSelection | None = None) -> None:
    """
    Renderiza a área principal do dashboard conforme PRD §6.1.3.

    Args:
        state: Estado actual da sessão com os DataFrames processados.
        selection: Selecção actual da sidebar para detecção de filtros obsoletos.
    """
    st.title("📦 Orders Master Infoprex")

    # ------------------------------------------------------------------
    # TASK-32: Banner e Documentação
    # ------------------------------------------------------------------
    render_top_banner(state)
    render_documentation_expander()

    # ------------------------------------------------------------------
    # TASK-33: Scope Summary Bar (US-14, §8.7)
    # ------------------------------------------------------------------
    if not state.df_raw.empty:
        render_scope_summary(state)

    # ------------------------------------------------------------------
    # TASK-28: Detecção de filtros obsoletos
    # ------------------------------------------------------------------
    if selection and not state.df_aggregated.empty:
        labs_changed = (state.last_labs_selection or []) != selection.labs_selected

        current_codes_name = (
            getattr(selection.codes_file, "name", None) if selection.codes_file else None
        )
        codes_changed = state.last_codes_file_name != current_codes_name

        if labs_changed or codes_changed:
            st.warning(
                "⚠️ **Filtros Modificados!** Os filtros de Laboratórios ou Códigos foram alterados. "
                "Clique em **🚀 Processar Dados** para actualizar os resultados.",
                icon="⚠️",
            )

    # Sem dados ainda
    if state.df_aggregated.empty and state.df_detailed.empty:
        st.info(
            "Configure os filtros na barra lateral e clique em **🚀 Processar Dados** "
            "para gerar as propostas de encomenda.",
            icon="ℹ️",
        )
        return

    # Erros de ficheiros
    if state.file_errors:
        with st.expander(f"⚠️ {len(state.file_errors)} erro(s) durante a ingestão", expanded=False):
            for err in state.file_errors:
                st.error(f"**{err.filename}** [{err.type}]: {err.message}")

    # Métricas sumárias
    if not state.df_aggregated.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Produtos", len(state.df_aggregated))
        col2.metric(
            "Ficheiros OK",
            sum(1 for e in state.file_inventory if e.status == "ok"),
        )
        col3.metric(
            "Erros",
            len(state.file_errors),
        )
        st.markdown("---")

    # Tabela principal (agrupada)
    if not state.df_aggregated.empty:
        st.subheader("📊 Vista Agrupada")
        st.dataframe(state.df_aggregated, use_container_width=True)

    # Tabela detalhada
    if not state.df_detailed.empty:
        st.subheader("🏪 Vista Detalhada (por Farmácia)")
        st.dataframe(state.df_detailed, use_container_width=True)

    # Inventário de ficheiros
    if state.file_inventory:
        with st.expander("📋 Inventário de Ficheiros", expanded=False):
            for entry in state.file_inventory:
                icon = "✅" if entry.status == "ok" else "❌"
                st.markdown(
                    f"{icon} **{entry.filename}** — {entry.farmacia} "
                    f"| {entry.n_linhas} linhas | DUV: {entry.duv_max}"
                    + (f" | ⚠️ {entry.avisos}" if entry.avisos else "")
                )


def render_top_banner(state: SessionState) -> None:
    """Renderiza o banner com a data de consulta da BD Rupturas."""
    data = state.shortages_data_consulta or "Não foi possível carregar a INFO"

    # Estilização conforme PRD §6.2.3
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, #e0f7fa 0%, #f1f8e9 100%);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 20px;
            border: 1px solid #c8e6c9;
        ">
            <span style="color: #555; font-size: 16px;">🗓️ Data Consulta BD Rupturas — </span>
            <span style="color: #0078D7; font-size: 24px; font-weight: bold;">{data}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_documentation_expander() -> None:
    """Renderiza o expander com a documentação básica."""
    with st.expander("ℹ️ Documentação e Workflow", expanded=False):
        st.markdown(
            """
        ### Como utilizar o Orders Master
        1. **Configurar Sidebar**: Seleccione os laboratórios ou carregue uma lista de CNPs (.txt).
        2. **Dados Base**: Carregue os ficheiros exportados do Infoprex (UTF-16, Tab separated).
        3. **Processar**: Clique em **🚀 Processar Dados**.
        4. **Ajustar**: Use os controlos na área principal para ajustar meses de previsão e pesos.
        5. **Exportar**: Clique em **📥 Download Excel Encomendas** para obter o ficheiro final.

        ---
        *Dica: O sistema detecta automaticamente rupturas oficiais e sinaliza produtos 'Não Comprar'.*
        """
        )
