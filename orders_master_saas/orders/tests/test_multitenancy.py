import datetime

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from accounts.middleware import TenantMiddleware
from accounts.models import Cliente, Subscricao, UserProfile


@pytest.mark.django_db
def test_tenant_middleware_sets_request_tenant():
    cliente = Cliente.objects.create(nome="Teste", email="t@t.com")
    user = User.objects.create_user("testuser", password="pass")
    UserProfile.objects.create(user=user, cliente=cliente)
    Subscricao.objects.create(
        cliente=cliente,
        plano=Subscricao.Plano.BASICO,
        data_inicio=datetime.date(2025, 1, 1),
    )
    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = user
    middleware = TenantMiddleware(lambda r: None)
    middleware(request)
    assert request.tenant == cliente


@pytest.mark.django_db
def test_tenant_middleware_anonymous_no_tenant():
    from django.contrib.auth.models import AnonymousUser

    factory = RequestFactory()
    request = factory.get("/orders/")
    request.user = AnonymousUser()
    middleware = TenantMiddleware(lambda r: None)
    middleware(request)
    assert not hasattr(request, "tenant") or request.tenant is None