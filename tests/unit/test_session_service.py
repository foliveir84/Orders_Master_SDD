import io
from typing import Any

import pytest

from orders_master.app_services.session_service import load_infoprex_files
from orders_master.app_services.session_state import SessionState


class DummyFile:
    def __init__(self, content: bytes, name: str) -> None:
        self._buffer = io.BytesIO(content)
        self.name = name

    def read(self, *args: Any, **kwargs: Any) -> bytes:
        return self._buffer.read(*args, **kwargs)

    def seek(self, *args: Any, **kwargs: Any) -> int:
        return self._buffer.seek(*args, **kwargs)


def test_load_infoprex_files_success_and_errors() -> None:
    state = SessionState()

    valid_content = "CPR\tDUV\tLOCALIZACAO\n1234567\t01/01/2026\tFARMACIA A\n"
    schema_error_content = "WRONG\tCOLUMNS\n123\tABC\n"
    # A random byte string that will definitely fail encoding
    encoding_error_content = b"\x00\x01\x02\xFF\xFE\xFD\xFC"

    file1 = DummyFile(valid_content.encode("utf-8"), "file1.txt")
    file2 = DummyFile(schema_error_content.encode("utf-8"), "file2.txt")
    file3 = DummyFile(encoding_error_content, "file3.txt")
    file4 = DummyFile(valid_content.encode("utf-8"), "file4.txt")

    files = [file1, file2, file3, file4]

    from unittest.mock import patch
    from orders_master.exceptions import InfoprexEncodingError

    with patch("orders_master.app_services.session_service.parse_infoprex_file") as mock_parse:
        def side_effect(file_like, *args, **kwargs):
            if getattr(file_like, "name", "") == "file3.txt":
                raise InfoprexEncodingError("Encoding falhou")
            from orders_master.ingestion.infoprex_parser import parse_infoprex_file
            return parse_infoprex_file(file_like, *args, **kwargs)
        
        mock_parse.side_effect = side_effect

        dfs = load_infoprex_files(
            files=files,  # type: ignore
            state=state,
            lista_cla=[],
            lista_codigos=[],
            locations_aliases={},
        )

    # 4 files total. 2 valid, 1 schema error, 1 encoding error
    assert len(dfs) == 2
    assert len(state.file_inventory) == 4
    assert len(state.file_errors) == 2

    # Check errors
    error_types = [e.type for e in state.file_errors]
    assert "schema" in error_types
    assert "encoding" in error_types

    # Check inventory
    ok_entries = [e for e in state.file_inventory if e.status == "ok"]
    assert len(ok_entries) == 2
    assert ok_entries[0].filename == "file1.txt"

    err_entries = [e for e in state.file_inventory if e.status == "error"]
    assert len(err_entries) == 2
    assert err_entries[0].error_message != ""
    assert err_entries[1].error_message != ""
