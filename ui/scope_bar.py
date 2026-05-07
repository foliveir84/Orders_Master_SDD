"""
ui/scope_bar.py — Barra de resumo métrico horizontal (§6.1.4).

Implementa ``render_scope_summary(state)`` que apresenta o contexto
actual do filtro e parâmetros de cálculo.
"""

import streamlit as st

from orders_master.app_services.session_state import SessionState


def render_scope_summary(state: SessionState) -> None:
    """
    Renderiza a barra de resumo métrico horizontal conforme PRD §8.7 e US-14.
    """
    ctx = state.scope_context

    # Se não houver produtos, não faz sentido mostrar a barra
    if not ctx.n_produtos and state.df_raw.empty:
        return

    # Formatação do conteúdo (TASK-33)
    # Janela: Mês Inicial – Mês Final
    janela = f"{ctx.primeiro_mes}–{ctx.ultimo_mes}" if ctx.primeiro_mes else "N/A"

    # Preset ainda é fixo por agora (Padrão), virá da TASK-29
    preset = "Padrão"

    # Obter valores actuais dos widgets via session_state para sincronização (TASK-33)
    months_val = st.session_state.get("months_input", ctx.meses)
    is_detailed = st.session_state.get("detailed_view_toggle", (ctx.modo == "Detalhada"))
    modo_val = "Detalhada" if is_detailed else "Agrupada"

    # Construção da string de métricas
    metrics = [
        f"📊 **{ctx.n_produtos}** produtos",
        f"🏪 **{ctx.n_farmacias}** farmácias",
        f"🎯 {ctx.descricao_filtro}",
        f"📅 Janela: {janela}",
        f"⚖️ Pesos: {preset}",
        f"🔮 Previsão: **{months_val:.1f}** m",
        f"👁️ Modo: **{modo_val}**",
    ]

    content = " | ".join(metrics)

    # Estilização Gradiente Subtil conforme PRD §6.1.4
    # Fundo gradiente subtil (#f5f7fa → #c3cfe2), padding 12px.
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 12px 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            border-left: 5px solid #0078D7;
            font-size: 14px;
            color: #333;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            {content}
        </div>
        """,
        unsafe_allow_html=True,
    )
