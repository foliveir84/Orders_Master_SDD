"""
ui/main_area.py — Área principal do dashboard (§6.1.3).

Implementa ``render_main(state)`` que apresenta a área de dados principal:
banner, expanders, toggles, tabela formatada e exportação.
"""

import streamlit as st
from typing import Any

from orders_master.app_services.recalc_service import recalculate_proposal
from orders_master.app_services.session_state import SessionState
from orders_master.business_logic.averages import load_presets
from orders_master.constants import Columns, GroupLabels
from orders_master.formatting.excel_formatter import build_excel, compute_scope_tag
from orders_master.formatting.web_styler import build_styler
from ui.file_inventory import render_file_inventory
from ui.scope_bar import render_scope_summary
from ui.sidebar import SidebarSelection


def render_main(
    state: SessionState,
    selection: SidebarSelection | None = None,
    labs_config: Any | None = None,
) -> None:
    """
    Renderiza a área principal do dashboard conforme PRD §6.1.3.
    Mantém a ordem vertical dos 14 componentes.
    """
    # 1. Banner "BD Rupturas" (Sempre visível)
    render_top_banner(state)

    # 2. Expander "Documentação" (Sempre visível)
    render_documentation_expander()

    # 5. Expander "Códigos CLA" (Sempre visível)
    render_cla_expander(state, labs_config)

    # Se não há dados, mostrar info e sair
    if state.df_raw.empty:
        st.info(
            "Configure os filtros na barra lateral e clique em **🚀 Processar Dados** "
            "para gerar as propostas de encomenda.",
            icon="ℹ️",
        )
        return

    # 3. Scope Summary Bar (Só após processamento)
    render_scope_summary(state)

    # 4. File Inventory (Só após processamento)
    render_file_inventory(state)

    # 6. Avisos de filtros obsoletos (TASK-28)
    if selection:
        _render_obsolete_filters_warning(state, selection)

    # 7. Erros e Warnings de Ingestão (TASK-03/TASK-23)
    if state.file_errors:
        with st.expander(f"⚠️ {len(state.file_errors)} erro(s) durante a ingestão", expanded=False):
            for err in state.file_errors:
                st.error(f"**{err.filename}** [{err.type}]: {err.message}")

    st.markdown("---")

    # --- CONTROLOS DE RECÁLCULO (8, 9, 10, 11, 12) ---
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        # 8. Toggle "Ver Detalhe de Sell Out?"
        detailed_view = st.toggle(
            "Ver Detalhe de Sell Out (por farmácia)?", 
            value=False,
            key="detailed_view_toggle"
        )
    with col_t2:
        # 9. Toggle "Média com base no mês ANTERIOR?"
        use_previous_month = st.toggle(
            "Ignorar mês corrente na média?", 
            value=True,
            key="use_prev_month_toggle"
        )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        # 10. Input "Meses a Prever"
        months = st.number_input(
            "📅 Meses a Prever",
            min_value=1.0,
            max_value=6.0,
            value=1.0,
            step=0.1,
            key="months_input",
            help="Número de meses de stock pretendido para a proposta.",
        )
    with col_m2:
        # TASK-29: Preset de Pesos
        weights = render_weights_selector()

    # 11. Feedback visual da previsão
    st.info(f"💡 **A preparar encomenda para {months:.1f} meses.**", icon="📦")

    # 12. Multiselect "Filtrar por Marca" (TASK-30)
    marcas_selected = render_brands_filter(state)

    # --- EXECUÇÃO DO RECÁLCULO (Pipeline Leve, <500ms) ---
    df_final = recalculate_proposal(
        df_detailed=state.df_raw,
        detailed_view=detailed_view,
        master_products=state.master_products,
        months=months,
        weights=weights,
        use_previous_month=use_previous_month,
        marcas=marcas_selected,
        scope_context=state.scope_context,
    )

    # 13. Tabela Formatada (TASK-41)
    if not df_final.empty:
        styler = build_styler(df_final)
        
        # Colunas a esconder (apenas técnicas puras)
        hide_cols = [
            Columns.TIME_DELTA, Columns.PRICE_ANOMALY, 
            Columns.SORT_KEY, Columns.CLA, "CÓDIGO_STR", Columns.MEDIA, Columns.MARCA
        ]
        column_config = {col: None for col in hide_cols if col in df_final.columns}

        # Configuração Streamlit para tabelas grandes
        st.dataframe(
            styler, 
            use_container_width=True, 
            height=600,
            column_config=column_config
        )

        # 14. Botão Download Excel (TASK-42)
        scope_tag = compute_scope_tag(
            labs=state.last_labs_selection or [],
            codes_file=state.last_codes_file_name,
            codes_count=len(df_final) if not detailed_view else state.scope_context.n_produtos,
        )
        excel_bytes, filename = build_excel(df_final, scope_tag)
        st.download_button(
            label="📥 Download Excel Encomendas",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
    else:
        st.warning("⚠️ Nenhum produto encontrado com os filtros actuais.")


def render_top_banner(state: SessionState) -> None:
    """Renderiza o banner com a data de consulta da BD Rupturas (§6.2.3)."""
    data = state.shortages_data_consulta or "Não disponível"
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, #e0f7fa 0%, #f1f8e9 100%);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
            border: 1px solid #c8e6c9;
        ">
            <span style="color: #555; font-size: 14px;">🗓️ Data Consulta BD Rupturas — </span>
            <span style="color: #0078D7; font-size: 20px; font-weight: bold;">{data}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_documentation_expander() -> None:
    """Checklist de workflow (§6.1.3)."""
    with st.expander("ℹ️ Documentação e Workflow", expanded=False):
        st.markdown(
            """
        1. **Configurar**: Escolha laboratórios ou carregue lista TXT.
        2. **Dados**: Carregue exportações Infoprex (UTF-16).
        3. **Processar**: Clique em **🚀 Processar Dados**.
        4. **Ajustar**: Altere meses, pesos ou filtros de marca abaixo.
        5. **Exportar**: Clique em **📥 Download Excel**.
        """
        )


def render_cla_expander(state: SessionState, labs_config: Any | None) -> None:
    """Mostra os códigos CLA activos (§6.1.3, componente 5)."""
    if not state.last_labs_selection:
        with st.expander("🔬 Códigos CLA dos Laboratórios Selecionados", expanded=False):
            st.info("Nenhum laboratório seleccionado.")
        return

    labs_str = ", ".join(state.last_labs_selection)
    with st.expander(f"🔬 Códigos CLA Ativos ({labs_str})", expanded=False):
        if not labs_config:
            st.error("Configuração de laboratórios não disponível.")
            return

        active_clas = []
        for lab in state.last_labs_selection:
            if lab in labs_config.root:
                active_clas.extend(labs_config.root[lab])

        if active_clas:
            st.write(f"**Total de {len(active_clas)} códigos CLA:**")
            st.caption(", ".join(active_clas))
        else:
            st.warning("Nenhum código CLA encontrado para a selecção actual.")


def render_weights_selector() -> tuple[float, ...]:
    """Widget de selecção de pesos (TASK-29)."""
    presets = load_presets("config/presets.yaml")
    options = list(presets.keys()) + ["Custom"]

    selected_preset = st.selectbox("⚖️ Preset de Pesos", options=options, index=1)  # Default: Padrão

    if selected_preset == "Custom":
        with st.expander("Pesos Customizados (Soma deve ser 1.0)", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            w1 = col1.number_input("Peso 1 (Mês n-1)", 0.0, 1.0, 0.4, 0.05)
            w2 = col2.number_input("Peso 2 (Mês n-2)", 0.0, 1.0, 0.3, 0.05)
            w3 = col3.number_input("Peso 3 (Mês n-3)", 0.0, 1.0, 0.2, 0.05)
            w4 = col4.number_input("Peso 4 (Mês n-4)", 0.0, 1.0, 0.1, 0.05)
            weights = (w1, w2, w3, w4)
            total = sum(weights)
            if abs(total - 1.0) > 1e-3:
                st.error(f"❌ A soma dos pesos é {total:.2f}. Deve ser exactamente 1.00.")
                st.warning("⚠️ Usando preset 'Padrão' até que a soma seja corrigida.")
                return presets.get("Padrão", (0.4, 0.3, 0.2, 0.1))
            return weights
    return presets[selected_preset]


def render_brands_filter(state: SessionState) -> list[str] | None:
    """Widget de filtro de marcas (TASK-30)."""
    # Só faz sentido se houver marcas disponíveis no dataset filtrado actual
    if state.df_raw.empty or Columns.MARCA not in state.df_raw.columns:
        return None

    # Extrair marcas únicas disponíveis (ignorando NaN)
    available_brands = (
        state.df_raw[state.df_raw[Columns.MARCA].notna()][Columns.MARCA]
        .unique()
        .tolist()
    )
    if not available_brands:
        return None

    # Key dinâmica para evitar state ghost (§5.5.3)
    dynamic_key = f"brands_ms_{'_'.join(state.last_labs_selection or [])}"

    selected = st.multiselect(
        "🏷️ Filtrar por Marca:",
        options=sorted(available_brands),
        default=sorted(available_brands),
        key=dynamic_key,
        help="A linha 'Grupo' é preservada mesmo ao filtrar marcas.",
    )
    return selected


def _render_obsolete_filters_warning(state: SessionState, selection: SidebarSelection) -> None:
    """Componente 6: Avisa se os filtros da sidebar mudaram sem re-processar."""
    labs_changed = (state.last_labs_selection or []) != selection.labs_selected
    current_codes_name = (
        getattr(selection.codes_file, "name", None) if selection.codes_file else None
    )
    codes_changed = state.last_codes_file_name != current_codes_name

    if labs_changed or codes_changed:
        st.warning(
            "⚠️ **Filtros Modificados!** Clique em **🚀 Processar Dados** para actualizar a base de dados.",
            icon="⚠️",
        )
