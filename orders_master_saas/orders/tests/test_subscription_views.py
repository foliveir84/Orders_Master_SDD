import pytest
from django.contrib.auth.models import User
from django.test import Client

from accounts.models import Cliente, Subscricao, UserProfile


@pytest.mark.django_db
def test_upload_view_blocked_when_subscription_expired():
    """upload_view returns 403 when subscription is expired."""
    cliente = Cliente.objects.create(nome="Expirado Lda", email="exp@test.pt")
    user = User.objects.create_user("exp_user", password="testpass123")
    UserProfile.objects.create(user=user, cliente=cliente)
    Subscricao.objects.create(
        cliente=cliente,
        plano=Subscricao.Plano.BASICO,
        data_inicio=__import__("datetime").date(2024, 1, 1),
        data_fim=__import__("datetime").date(2024, 12, 31),
        ativa=True,
    )
    c = Client()
    c.login(username="exp_user", password="testpass123")
    response = c.get("/orders/")
    assert response.status_code == 403
    assert "Subscricao Expirada" in response.content.decode()


@pytest.mark.django_db
def test_upload_view_allowed_when_subscription_active():
    """upload_view returns 200 when subscription is active."""
    cliente = Cliente.objects.create(nome="Activo Lda", email="act@test.pt")
    user = User.objects.create_user("act_user", password="testpass123")
    UserProfile.objects.create(user=user, cliente=cliente)
    Subscricao.objects.create(
        cliente=cliente,
        plano=Subscricao.Plano.PROFISSIONAL,
        data_inicio=__import__("datetime").date(2025, 1, 1),
        data_fim=__import__("datetime").date(2030, 12, 31),
        ativa=True,
    )
    c = Client()
    c.login(username="act_user", password="testpass123")
    response = c.get("/orders/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_results_view_blocked_when_subscription_expired():
    """results_view returns 403 when subscription is expired."""
    cliente = Cliente.objects.create(nome="Expirado Res Lda", email="expres@test.pt")
    user = User.objects.create_user("expres_user", password="testpass123")
    UserProfile.objects.create(user=user, cliente=cliente)
    Subscricao.objects.create(
        cliente=cliente,
        plano=Subscricao.Plano.BASICO,
        data_inicio=__import__("datetime").date(2024, 1, 1),
        data_fim=__import__("datetime").date(2024, 12, 31),
        ativa=True,
    )
    c = Client()
    c.login(username="expres_user", password="testpass123")
    response = c.get("/orders/results/")
    assert response.status_code == 403
    assert "Subscricao Expirada" in response.content.decode()