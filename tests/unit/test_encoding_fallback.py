import io

import pytest

from orders_master.exceptions import InfoprexEncodingError
from orders_master.ingestion.encoding_fallback import try_read_with_fallback_encodings


def test_utf16_le_with_bom():
    """Verifica se lê UTF-16 LE com BOM (padrão Sifarma)."""
    data = "CPR\tNOM\n123\tTeste UTF-16"
    # UTF-16 com BOM
    file_content = data.encode("utf-16")
    file_like = io.BytesIO(file_content)
    file_like.name = "utf16_bom.txt"

    df = try_read_with_fallback_encodings(file_like)
    assert df.shape == (1, 2)
    assert df.iloc[0]["NOM"] == "Teste UTF-16"


def test_utf8():
    """Verifica se lê UTF-8."""
    data = "CPR\tNOM\n456\tTeste UTF-8"
    file_content = data.encode("utf-8")
    file_like = io.BytesIO(file_content)
    file_like.name = "utf8.txt"

    df = try_read_with_fallback_encodings(file_like)
    assert df.shape == (1, 2)
    assert df.iloc[0]["NOM"] == "Teste UTF-8"


def test_latin1():
    """Verifica se lê Latin-1 (ISO-8859-1) para caracteres acentuados."""
    # 'ç' em latin1 é 0xE7, em utf8 é 0xC3 0xA7
    data = "CPR\tNOM\n789\tAçúcar"
    file_content = data.encode("latin1")
    file_like = io.BytesIO(file_content)
    file_like.name = "latin1.txt"

    df = try_read_with_fallback_encodings(file_like)
    assert df.shape == (1, 2)
    assert df.iloc[0]["NOM"] == "Açúcar"


def test_usecols_list():
    """Verifica se respeita usecols como lista."""
    data = "CPR\tNOM\tEXTRA\n1\tA\tB"
    file_like = io.BytesIO(data.encode("utf-8"))

    df = try_read_with_fallback_encodings(file_like, usecols=["CPR", "NOM"])
    assert list(df.columns) == ["CPR", "NOM"]


def test_usecols_callable():
    """Verifica se respeita usecols como callable."""
    data = "CPR\tNOM\tEXTRA\n1\tA\tB"
    file_like = io.BytesIO(data.encode("utf-8"))

    df = try_read_with_fallback_encodings(file_like, usecols=lambda c: c in ["CPR", "EXTRA"])
    assert list(df.columns) == ["CPR", "EXTRA"]


def test_invalid_encoding_raises_error():
    """Verifica se levanta InfoprexEncodingError para ficheiros binários aleatórios."""
    # 100 bytes aleatórios que provavelmente não são texto válido em nenhum destes encodings
    # Ou pelo menos não são CSVs válidos.
    # Na verdade, latin1 aceita quase tudo, mas o pandas pode falhar se houver inconsistência de colunas.
    # Mas se o ficheiro for binário e pedirmos utf-16, ele falha.
    # Vamos tentar algo que quebre todos.
    file_content = bytes([0, 1, 2, 3, 4, 5, 255, 254, 0, 0, 10, 20])
    file_like = io.BytesIO(file_content)
    file_like.name = "corrupted.bin"

    with pytest.raises(InfoprexEncodingError) as excinfo:
        # Usamos usecols para forçar falha se o conteúdo não tiver as colunas
        try_read_with_fallback_encodings(file_like, usecols=["CPR"])

    assert "Codificação não suportada" in str(excinfo.value)


def test_seek_is_called():
    """Verifica se seek(0) é chamado em cada tentativa."""

    # Para testar isso, precisamos de um mock que registe as chamadas a seek
    class SeekRecorder:
        def __init__(self, data):
            self.data = data
            self.seeks = 0
            self.name = "mock"

        def seek(self, pos):
            self.seeks += 1

        def read(self, size=-1):
            # Devolve algo que quebra o primeiro encoding mas talvez passe no seguinte?
            # Ou apenas que falhe sempre para contar os seeks.
            return self.data

        def readline(self):
            return b"CPR\tNOM\n"  # Apenas para o pandas não crashar logo de início se ler linha a linha

    # Na verdade o pandas read_csv interage de forma complexa com o stream.
    # Vamos usar um BytesIO real e monkeypatch o seek
    file_like = io.BytesIO(b"garbage")
    original_seek = file_like.seek
    seek_count = 0

    def mock_seek(pos):
        nonlocal seek_count
        seek_count += 1
        return original_seek(pos)

    file_like.seek = mock_seek

    try:
        try_read_with_fallback_encodings(file_like, usecols=["CPR"])
    except InfoprexEncodingError:
        pass

    # 3 encodings = 3 tentativas de seek(0)
    assert seek_count >= 3
