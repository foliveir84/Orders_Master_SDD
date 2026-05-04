import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from orders_master.app_services.session_state import get_state, reset_state, SessionState, ScopeContext, FileInventoryEntry
from orders_master.exceptions import FileError

def test_session_state_dataclass_init():
    """Verifica se as dataclasses podem ser inicializadas correctamente sem Streamlit."""
    state = SessionState()
    assert isinstance(state.df_aggregated, pd.DataFrame)
    assert state.last_labs_selection is None
    assert isinstance(state.file_errors, list)
    assert isinstance(state.scope_context, ScopeContext)

def test_get_state_no_streamlit():
    """Verifica se get_state funciona sem Streamlit (fallback)."""
    with patch.dict("sys.modules", {"streamlit": None}):
        state = get_state()
        assert isinstance(state, SessionState)

def test_get_state_with_mock_streamlit():
    """Verifica se get_state interage correctamente com st.session_state."""
    mock_st = MagicMock()
    mock_st.session_state = {}
    
    with patch.dict("sys.modules", {"streamlit": mock_st}):
        # Primeira chamada - deve inicializar
        state1 = get_state()
        assert "orders_master_state" in mock_st.session_state
        assert isinstance(state1, SessionState)
        
        # Modificar o estado
        state1.last_labs_selection = ["Lab1"]
        
        # Segunda chamada - deve devolver a mesma instância
        state2 = get_state()
        assert state2.last_labs_selection == ["Lab1"]
        assert state1 is state2

def test_reset_state_with_mock_streamlit():
    """Verifica se reset_state limpa o st.session_state."""
    mock_st = MagicMock()
    state = SessionState()
    mock_st.session_state = {"orders_master_state": state}
    
    with patch.dict("sys.modules", {"streamlit": mock_st}):
        reset_state()
        assert "orders_master_state" not in mock_st.session_state

def test_file_inventory_entry_defaults():
    """Verifica valores default de FileInventoryEntry."""
    entry = FileInventoryEntry(filename="test.txt")
    assert entry.filename == "test.txt"
    assert entry.status == "ok"
    assert entry.farmacia == ""

def test_scope_context_defaults():
    """Verifica valores default de ScopeContext."""
    ctx = ScopeContext()
    assert ctx.n_produtos == 0
    assert ctx.meses == 0.0
