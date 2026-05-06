import io
from pathlib import Path

import pytest

from orders_master.ingestion.infoprex_parser import parse_infoprex_file


@pytest.fixture(scope="session")
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_infoprex_df(fixtures_dir):
    """
    Retorna o DataFrame resultante do parse do infoprex_mini.txt.
    """
    file_path = fixtures_dir / "infoprex_mini.txt"

    with open(file_path, "rb") as f:
        file_content = f.read()

    file_like = io.BytesIO(file_content)
    file_like.name = "infoprex_mini.txt"

    aliases = {"ilha": "Farmácia da Ilha", "colmeias": "Farmácia Colmeias"}
    df, _ = parse_infoprex_file(file_like, [], [], aliases)
    return df


@pytest.fixture
def mock_session_state(monkeypatch):
    """
    Mocks st.session_state for testing without Streamlit runtime.
    """

    class MockSessionState(dict):
        def __getattr__(self, item):
            return self.get(item)

        def __setattr__(self, key, value):
            self[key] = value

    mock_state = MockSessionState()

    try:
        import streamlit as st

        monkeypatch.setattr(st, "session_state", mock_state)
    except ImportError:
        pass

    return mock_state
