import pytest
from django.contrib.auth.models import User

from accounts.models import Cliente, Farmacia
from orders.services.license import validate_localizacao


@pytest.fixture
def cliente_with_farmacias(db):
    cliente = Cliente.objects.create(nome="Test Labs", email="test@example.com")
    Farmacia.objects.create(
        cliente=cliente,
        nome="Farmacia Guia",
        localizacao_key="FARMACIA GUIA",
        alias="Guia",
        ativa=True,
    )
    Farmacia.objects.create(
        cliente=cliente,
        nome="Farmacia Lisboa",
        localizacao_key="FARMACIA LISBOA",
        alias="Lisboa",
        ativa=True,
    )
    Farmacia.objects.create(
        cliente=cliente,
        nome="Farmacia Inactive",
        localizacao_key="FARMACIA INACTIVE",
        alias="Inactive",
        ativa=False,
    )
    return cliente


@pytest.mark.django_db
def test_exact_match(cliente_with_farmacias):
    result = validate_localizacao("FARMACIA GUIA", cliente_with_farmacias)
    assert result is not None
    assert result.alias == "Guia"


@pytest.mark.django_db
def test_case_insensitive_match(cliente_with_farmacias):
    result = validate_localizacao("farmacia guia", cliente_with_farmacias)
    assert result is not None
    assert result.alias == "Guia"


@pytest.mark.django_db
def test_partial_match_localizacao_in_key(cliente_with_farmacias):
    """LOCALIZACAO 'LISBOA' is a substring of the key 'FARMACIA LISBOA'."""
    result = validate_localizacao("LISBOA", cliente_with_farmacias)
    assert result is not None
    assert result.alias == "Lisboa"


@pytest.mark.django_db
def test_no_match(cliente_with_farmacias):
    result = validate_localizacao("FARMACIA PORTO", cliente_with_farmacias)
    assert result is None


@pytest.mark.django_db
def test_inactive_farmacia_excluded(cliente_with_farmacias):
    result = validate_localizacao("FARMACIA INACTIVE", cliente_with_farmacias)
    assert result is None