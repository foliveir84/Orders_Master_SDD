import datetime

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from accounts.middleware import TenantMiddleware
from accounts.models import Cliente, Subscricao, UserProfile


@pytest.mark.django_db
def test_subscription_expired_when_past_end_date():
    """Middleware sets subscription_expired=True when data_fim is in the past."""
    cliente = Cliente.objects.create(nome="Expirado Lda", email="exp@test.pt")
    user = User.objects.create_user("expired_user", password="pass")
    UserProfile.objects.create(user=user, cliente=cliente)
    Subscricao.objects.create(
        cliente=cliente,
        plano=Subscricao.Plano.BASICO,
        data_inicio=datetime.date(2024, 1, 1),
        data_fim=datetime.date(2024, 12, 31),
        ativa=True,
    )
    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = user
    middleware = TenantMiddleware(lambda r: None)
    middleware(request)
    assert request.tenant == cliente
    assert request.subscription_expired is True


@pytest.mark.django_db
def test_subscription_not_expired_when_future_end_date():
    """Middleware sets subscription_expired=False when data_fim is in the future."""
    cliente = Cliente.objects.create(nome="Activo Lda", email="act@test.pt")
    user = User.objects.create_user("active_user", password="pass")
    UserProfile.objects.create(user=user, cliente=cliente)
    Subscricao.objects.create(
        cliente=cliente,
        plano=Subscricao.Plano.PROFISSIONAL,
        data_inicio=datetime.date(2025, 1, 1),
        data_fim=datetime.date(2030, 12, 31),
        ativa=True,
    )
    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = user
    middleware = TenantMiddleware(lambda r: None)
    middleware(request)
    assert request.tenant == cliente
    assert request.subscription_expired is False


@pytest.mark.django_db
def test_subscription_not_expired_when_no_end_date():
    """Middleware sets subscription_expired=False when data_fim is None."""
    cliente = Cliente.objects.create(nome="Sem Fim Lda", email="nofim@test.pt")
    user = User.objects.create_user("nofim_user", password="pass")
    UserProfile.objects.create(user=user, cliente=cliente)
    Subscricao.objects.create(
        cliente=cliente,
        plano=Subscricao.Plano.ENTERPRISE,
        data_inicio=datetime.date(2025, 1, 1),
        data_fim=None,
        ativa=True,
    )
    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = user
    middleware = TenantMiddleware(lambda r: None)
    middleware(request)
    assert request.tenant == cliente
    assert request.subscription_expired is False


@pytest.mark.django_db
def test_subscription_not_expired_when_inactive():
    """Middleware sets subscription_expired=False when subscription is inactive (already cancelled)."""
    cliente = Cliente.objects.create(nome="Inactivo Lda", email="inact@test.pt")
    user = User.objects.create_user("inact_user", password="pass")
    UserProfile.objects.create(user=user, cliente=cliente)
    Subscricao.objects.create(
        cliente=cliente,
        plano=Subscricao.Plano.BASICO,
        data_inicio=datetime.date(2024, 1, 1),
        data_fim=datetime.date(2024, 6, 1),
        ativa=False,
    )
    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = user
    middleware = TenantMiddleware(lambda r: None)
    middleware(request)
    assert request.tenant == cliente
    assert request.subscription_expired is False


@pytest.mark.django_db
def test_subscription_not_expired_when_no_subscription():
    """Middleware sets subscription_expired=False when tenant has no subscription record."""
    cliente = Cliente.objects.create(nome="Sem Sub Lda", email="nosub@test.pt")
    user = User.objects.create_user("nosub_user", password="pass")
    UserProfile.objects.create(user=user, cliente=cliente)
    # No Subscricao created for this cliente
    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = user
    middleware = TenantMiddleware(lambda r: None)
    middleware(request)
    assert request.tenant is None
    assert request.subscription_expired is False


@pytest.mark.django_db
def test_subscription_expired_anonymous_user():
    """Middleware does not set subscription_expired for anonymous users."""
    from django.contrib.auth.models import AnonymousUser

    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = AnonymousUser()
    middleware = TenantMiddleware(lambda r: None)
    middleware(request)
    assert not hasattr(request, "subscription_expired") or request.subscription_expired is False