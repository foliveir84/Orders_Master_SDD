import streamlit as st
from pathlib import Path
from orders_master.logger import configure_logging

# Initialize Centralized Logging
configure_logging(Path("logs"))

def main() -> None:
    st.set_page_config(
        page_title="Orders Master Infoprex",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Orders Master Infoprex")
    st.write("Bem-vindo ao sistema de gestão de encomendas.")
    st.info("A aguardar configuração de dados na sidebar...")

if __name__ == "__main__":
    main()
