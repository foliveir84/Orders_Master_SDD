"""
ui/file_inventory.py — Inventário de ficheiros processados (§6.1.5).

Implementa ``render_file_inventory(state)`` que apresenta um resumo técnico
de todos os ficheiros Infoprex carregados.
"""

import pandas as pd
import streamlit as st

from orders_master.app_services.session_state import SessionState


def render_file_inventory(state: SessionState) -> None:
    """
    Renderiza o componente de inventário de ficheiros conforme PRD §8.8 e US-15.
    """
    if not state.file_inventory:
        return

    with st.expander("📋 Inventário de Ficheiros Processados", expanded=False):
        # Construir DataFrame para exibição tabular
        inventory_data = []
        for entry in state.file_inventory:
            status_icon = "✅" if entry.status == "ok" else "❌"
            inventory_data.append(
                {
                    "S": status_icon,
                    "Ficheiro": entry.filename,
                    "Farmácia": entry.farmacia,
                    "Linhas": entry.n_linhas,
                    "Última Venda": entry.duv_max,
                    "Avisos": entry.avisos,
                }
            )

        df_inventory = pd.DataFrame(inventory_data)

        # Aplicar estilo condicional para erros (TASK-34)
        def highlight_errors(row: pd.Series) -> list[str]:
            if row["S"] == "❌":
                return ["background-color: #ffebee; color: #b71c1c"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_inventory.style.apply(highlight_errors, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "S": st.column_config.TextColumn("S", width="small"),
                "Linhas": st.column_config.NumberColumn("Linhas", format="%d"),
                "Avisos": st.column_config.TextColumn("Avisos", width="large"),
            },
        )

        if any(e.status == "error" for e in state.file_inventory):
            st.caption("⚠️ Alguns ficheiros não puderam ser processados. Verifique os erros acima.")
