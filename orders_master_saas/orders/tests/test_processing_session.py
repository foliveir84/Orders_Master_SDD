import pandas as pd
import pytest
from django.core.cache import cache

from orders.services.processing_session import ProcessingSession


@pytest.fixture
def session():
    """Return a fresh ProcessingSession with a unique key, cleaning up after."""
    s = ProcessingSession("test-session-001")
    s.clear()
    yield s
    s.clear()


@pytest.mark.django_db
def test_store_and_retrieve_dataframe(session):
    df = pd.DataFrame({"CÓDIGO": [100, 200], "PVP": [5.0, 10.5]})
    session.store("df_test", df)

    result = session.get("df_test")
    assert result is not None
    assert list(result.columns) == ["CÓDIGO", "PVP"]
    assert len(result) == 2
    assert result["PVP"].iloc[1] == pytest.approx(10.5)


@pytest.mark.django_db
def test_get_missing_returns_none(session):
    assert session.get("nonexistent") is None


@pytest.mark.django_db
def test_store_and_retrieve_scalar(session):
    session.store_value("scope", {"n_produtos": 42, "n_farmacias": 3})
    result = session.get_value("scope")
    assert result["n_produtos"] == 42

    assert session.get_value("missing_key") is None


@pytest.mark.django_db
def test_clear_removes_all_keys(session):
    session.store("df_a", pd.DataFrame({"x": [1]}))
    session.store_value("val_b", "hello")

    session.clear()

    assert session.get("df_a") is None
    assert session.get_value("val_b") is None