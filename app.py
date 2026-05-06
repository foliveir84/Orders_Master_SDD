"""
app.py — Entry-point fino do Orders Master Infoprex (TASK-25, PRD §6.1.1).

Responsabilidades (≤ 100 linhas):
  1. Configurar a página Streamlit.
  2. Inicializar o logging centralizado.
  3. Carregar configurações externas (labs, localizações).
  4. Delegar para ui.sidebar (render_sidebar) e ui.main_area (render_main).
  5. Orquestrar o fluxo de processamento via session_service.

Sem lógica de negócio aqui — todas as regras residem em orders_master/.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from orders_master.app_services.recalc_service import recalculate_proposal
from orders_master.app_services.session_service import process_orders_session
from orders_master.app_services.session_state import get_state, reset_state
from orders_master.business_logic.averages import load_presets
from orders_master.config.labs_loader import get_file_mtime as get_labs_mtime
from orders_master.config.labs_loader import load_labs
from orders_master.config.locations_loader import get_file_mtime as get_locs_mtime
from orders_master.config.locations_loader import load_locations
from orders_master.logger import configure_logging
from ui.main_area import render_main
from ui.sidebar import render_sidebar

# ---------------------------------------------------------------------------
# Configuração global (executado antes de qualquer render)
# ---------------------------------------------------------------------------
configure_logging(Path("logs"))
pd.set_option("styler.render.max_elements", 1_000_000)

_LABS_PATH = Path("config/laboratorios.json")
_LOCS_PATH = Path("config/localizacoes.json")


def main() -> None:
    st.set_page_config(
        page_title="Orders Master Infoprex",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ------------------------------------------------------------------
    # Carregar configurações externas (cache por mtime)
    # ------------------------------------------------------------------
    labs_config = load_labs(get_labs_mtime(_LABS_PATH), _LABS_PATH)
    locs_config = load_locations(get_locs_mtime(_LOCS_PATH), _LOCS_PATH)
    locations_aliases: dict[str, str] = dict(locs_config.root)

    # ------------------------------------------------------------------
    # Sidebar — captura inputs do utilizador
    # ------------------------------------------------------------------
    selection = render_sidebar(labs_options=list(labs_config.root.keys()))
    state = get_state()

    # ------------------------------------------------------------------
    # Processar Dados
    # ------------------------------------------------------------------
    if selection.processar_clicked:
        reset_state()
        state = get_state()

        progress_bar = st.progress(0, text="A iniciar processamento...")

        def update_progress(fraction: float, text: str) -> None:
            progress_bar.progress(fraction, text=text)

        process_orders_session(
            files=selection.infoprex_files,
            codes_file=selection.codes_file,
            brands_files=selection.brands_files,
            labs_selected=selection.labs_selected,
            locations_aliases=locations_aliases,
            state=state,
            progress_callback=update_progress,
        )
        progress_bar.empty()

    # ------------------------------------------------------------------
    # Recálculo Dinâmico (TASK-24, TASK-26, TASK-28, TASK-33)
    # ------------------------------------------------------------------
    if not state.df_raw.empty:
        # 1. Obter Presets/Pesos (Por agora fixos, TASK-28 virá depois)
        presets = load_presets("config/presets.yaml")
        weights = presets.get("Padrão", (0.4, 0.3, 0.2, 0.1))

        # 2. Recalcular Vista Detalhada
        state.df_detailed = recalculate_proposal(
            df_detailed=state.df_raw,
            detailed_view=True,
            master_products=state.master_products,
            months=1.0,  # TODO: TASK-28
            weights=weights,
        )

        # 3. Recalcular Vista Agrupada
        state.df_aggregated = recalculate_proposal(
            df_detailed=state.df_raw,
            detailed_view=False,
            master_products=state.master_products,
            months=1.0,  # TODO: TASK-28
            weights=weights,
        )

    # ------------------------------------------------------------------
    # Área principal — renderização dos resultados
    # ------------------------------------------------------------------
    render_main(state, selection)


if __name__ == "__main__":
    main()
