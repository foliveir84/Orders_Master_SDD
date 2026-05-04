import sys
from pathlib import Path
from orders_master.config.labs_loader import load_labs, get_file_mtime
from orders_master.exceptions import ConfigError


def validate_config(file_path: str) -> None:
    """
    Validates a configuration file using the appropriate loader.
    
    Args:
        file_path (str): Path to the configuration file.
    """
    path = Path(file_path)
    if not path.exists():
        print(f"✗ Erro: Ficheiro não encontrado: {file_path}")
        sys.exit(1)

    try:
        if path.name == "laboratorios.json":
            # Using get_file_mtime for the mtime argument
            # st.cache_data usually works fine outside streamlit by simply executing the function.
            load_labs(get_file_mtime(path), path)
            print(f"✓ Ficheiro {file_path} é válido.")
        elif path.name == "localizacoes.json":
            # Placeholder for TASK-07
            print(f"! Aviso: Validador para {path.name} ainda não implementado (será feito na TASK-07).")
            # For now, let's just exit 0 to not break CI if it's just a placeholder
            sys.exit(0)
        else:
            print(f"! Aviso: Nenhum validador específico para {file_path}.")
            sys.exit(0)

        sys.exit(0)
    except ConfigError as e:
        print(f"✗ Falha na validação de {file_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Erro inesperado ao validar {file_path}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m orders_master.config.validate <ficheiro.json>")
        sys.exit(1)
    validate_config(sys.argv[1])
