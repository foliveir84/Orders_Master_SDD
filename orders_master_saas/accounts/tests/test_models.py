import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Cliente, Farmacia, Subscricao, UserProfile


class ClienteModelTest(TestCase):
    def test_create_cliente(self):
        c = Cliente.objects.create(nome="Farmacia Central", email="info@central.pt")
        self.assertEqual(c.nome, "Farmacia Central")
        self.assertEqual(c.email, "info@central.pt")
        self.assertTrue(c.ativo)
        self.assertIsNotNone(c.criado_em)
        self.assertIsNotNone(c.actualizado_em)

    def test_cliente_str(self):
        c = Cliente.objects.create(nome="Farmacia Central", email="info@central.pt")
        self.assertEqual(str(c), "Farmacia Central")

    def test_cliente_ordering(self):
        Cliente.objects.create(nome="Zebra", email="z@test.pt")
        Cliente.objects.create(nome="Alpha", email="a@test.pt")
        names = list(Cliente.objects.values_list("nome", flat=True))
        self.assertEqual(names, ["Alpha", "Zebra"])

    def test_cliente_optional_fields_blank(self):
        c = Cliente.objects.create(nome="Minimal", email="m@test.pt")
        self.assertEqual(c.nif, "")
        self.assertEqual(c.telefone, "")


class FarmaciaModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nome="Cliente Teste", email="t@test.pt")

    def test_farmacia_belongs_to_cliente(self):
        f = Farmacia.objects.create(
            cliente=self.cliente,
            nome="Farmacia Guia",
            localizacao_key="NOVA da vila",
            alias="Guia",
        )
        self.assertEqual(f.cliente, self.cliente)
        self.assertIn(f, self.cliente.farmacias.all())

    def test_farmacia_str(self):
        f = Farmacia.objects.create(
            cliente=self.cliente,
            nome="Farmacia Guia",
            localizacao_key="NOVA da vila",
            alias="Guia",
        )
        self.assertEqual(str(f), "Guia (Cliente Teste)")

    def test_farmacia_unique_together(self):
        Farmacia.objects.create(
            cliente=self.cliente,
            nome="Farmacia Guia",
            localizacao_key="NOVA da vila",
            alias="Guia",
        )
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Farmacia.objects.create(
                cliente=self.cliente,
                nome="Farmacia Guia 2",
                localizacao_key="NOVA da vila",
                alias="Guia 2",
            )


class SubscricaoModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nome="Cliente Teste", email="t@test.pt")

    def test_subscricao_bd_rupturas_flag_default(self):
        s = Subscricao.objects.create(
            cliente=self.cliente,
            plano=Subscricao.Plano.BASICO,
            data_inicio=datetime.date(2025, 1, 1),
        )
        self.assertFalse(s.bd_rupturas_ativa)

    def test_subscricao_bd_rupturas_flag_enabled(self):
        s = Subscricao.objects.create(
            cliente=self.cliente,
            plano=Subscricao.Plano.PROFISSIONAL,
            data_inicio=datetime.date(2025, 1, 1),
            bd_rupturas_ativa=True,
        )
        self.assertTrue(s.bd_rupturas_ativa)

    def test_subscricao_str(self):
        s = Subscricao.objects.create(
            cliente=self.cliente,
            plano=Subscricao.Plano.BASICO,
            data_inicio=datetime.date(2025, 1, 1),
        )
        self.assertEqual(str(s), "Cliente Teste - Basico")

    def test_subscricao_plano_choices(self):
        s = Subscricao.objects.create(
            cliente=self.cliente,
            plano=Subscricao.Plano.ENTERPRISE,
            data_inicio=datetime.date(2025, 1, 1),
        )
        self.assertEqual(s.get_plano_display(), "Enterprise")


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nome="Cliente Teste", email="t@test.pt")
        self.user = User.objects.create_user("joao", password="pass")

    def test_userprofile_links_user_to_cliente(self):
        up = UserProfile.objects.create(
            user=self.user,
            cliente=self.cliente,
            role=UserProfile.Role.COMPRAS,
        )
        self.assertEqual(up.user, self.user)
        self.assertEqual(up.cliente, self.cliente)
        self.assertEqual(up.role, UserProfile.Role.COMPRAS)

    def test_userprofile_str(self):
        up = UserProfile.objects.create(
            user=self.user,
            cliente=self.cliente,
            role=UserProfile.Role.ADMIN,
        )
        self.assertEqual(str(up), "joao (Cliente Teste)")

    def test_userprofile_one_to_one(self):
        UserProfile.objects.create(
            user=self.user,
            cliente=self.cliente,
            role=UserProfile.Role.FARMACIA,
        )
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(
                user=self.user,
                cliente=self.cliente,
                role=UserProfile.Role.COMPRAS,
            )

    def test_user_backwards_relation(self):
        UserProfile.objects.create(
            user=self.user,
            cliente=self.cliente,
            role=UserProfile.Role.ADMIN,
        )
        self.assertEqual(self.user.profile.cliente, self.cliente)