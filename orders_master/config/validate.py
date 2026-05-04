import sys
from pathlib import Path
from orders_master.config.labs_loader import load_labs, get_file_mtime as get_labs_mtime
from orders_master.config.locations_loader import load_locations, get_file_mtime as get_locs_mtime


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
            load_labs(get_labs_mtime(path), path)
            print(f"✓ Ficheiro {file_path} é válido.")
        elif path.name == "localizacoes.json":
            load_locations(get_locs_mtime(path), path)
            print(f"✓ Ficheiro {file_path} é válido.")
        else:
            print(f"! Aviso: Nenhum validador específico para {file_path}.")

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
