import sys
from pathlib import Path

from orders_master.config.labs_loader import get_file_mtime as get_labs_mtime
from orders_master.config.labs_loader import load_labs
from orders_master.config.locations_loader import get_file_mtime as get_locs_mtime
from orders_master.config.locations_loader import load_locations
from orders_master.exceptions import ConfigError


def validate_config(file_path: str) -> None:
    """
    Validates a configuration file using the appropriate loader.

    Args:
        file_path (str): Path to the configuration file.
    """
    path = Path(file_path)
    if not path.exists():
        sys.stdout.write(f"✗ Erro: Ficheiro não encontrado: {file_path}\n")
        sys.exit(1)

    try:
        if path.name == "laboratorios.json":
            load_labs(get_labs_mtime(path), path)
            sys.stdout.write(f"✓ Ficheiro {file_path} é válido.\n")
        elif path.name == "localizacoes.json":
            load_locations(get_locs_mtime(path), path)
            sys.stdout.write(f"✓ Ficheiro {file_path} é válido.\n")
        else:
            sys.stdout.write(f"! Aviso: Nenhum validador específico para {file_path}.\n")

        sys.exit(0)
    except ConfigError as e:
        sys.stdout.write(f"✗ Falha na validação de {file_path}: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stdout.write(f"✗ Erro inesperado ao validar {file_path}: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stdout.write("Uso: python -m orders_master.config.validate <ficheiro.json>\n")
        sys.exit(1)
    validate_config(sys.argv[1])
