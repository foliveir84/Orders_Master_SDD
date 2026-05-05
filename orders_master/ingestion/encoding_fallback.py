from typing import Any, Callable, List, Optional, Union
import pandas as pd
import io
from orders_master.exceptions import InfoprexEncodingError

def try_read_with_fallback_encodings(
    file_like: Union[io.BytesIO, io.StringIO, Any],
    sep: str = "\t",
    usecols: Optional[Union[List[str], Callable[[str], bool]]] = None,
) -> pd.DataFrame:
    """
    Tenta ler um ficheiro CSV/TXT usando uma sequência de codificações (utf-16 -> utf-8 -> latin1).
    Faz seek(0) antes de cada tentativa para garantir que o ponteiro está no início.

    Args:
        file_like: Objecto tipo ficheiro (deve suportar read() e seek()).
        sep: Separador de colunas (default é tabulação).
        usecols: Lista de colunas ou função de filtragem de colunas.

    Returns:
        pd.DataFrame: O conteúdo do ficheiro lido.

    Raises:
        InfoprexEncodingError: Se nenhuma das codificações funcionar.
    """
    encodings = ["utf-16", "utf-8", "latin1"]
    
    filename = getattr(file_like, "name", "ficheiro desconhecido")

    for enc in encodings:
        try:
            if hasattr(file_like, "seek"):
                file_like.seek(0)
            
            # Usamos pd.read_csv que é robusto para ler de buffers de bytes ou strings
            df = pd.read_csv(
                file_like,
                sep=sep,
                encoding=enc,
                usecols=usecols,
                on_bad_lines="error",  # Levanta erro se houver linhas mal formadas
            )
            return df
        except Exception:
            continue
    
    raise InfoprexEncodingError(f"Codificação não suportada para o ficheiro: {filename}")
