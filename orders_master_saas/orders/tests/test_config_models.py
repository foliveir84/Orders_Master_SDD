from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Cliente
from orders.models import ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset, SessaoProcessamento


class ConfigLaboratorioModelTest(TestCase):
    def test_create_laboratorio(self):
        lab = ConfigLaboratorio.objects.create(
            nome="Mylan", codigos_cla=["137", "2651"]
        )
        self.assertEqual(lab.nome, "Mylan")
        self.assertEqual(lab.codigos_cla, ["137", "2651"])
        self.assertTrue(lab.ativo)

    def test_laboratorio_unique_name(self):
        ConfigLaboratorio.objects.create(nome="Mylan", codigos_cla=["137"])
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ConfigLaboratorio.objects.create(nome="Mylan", codigos_cla=["999"])

    def test_laboratorio_str(self):
        lab = ConfigLaboratorio.objects.create(nome="Teva", codigos_cla=["2326"])
        self.assertEqual(str(lab), "Teva")

    def test_laboratorio_ordering(self):
        ConfigLaboratorio.objects.create(nome="Zambon", codigos_cla=["834"])
        ConfigLaboratorio.objects.create(nome="Abboca", codigos_cla=["2066"])
        names = list(ConfigLaboratorio.objects.values_list("nome", flat=True))
        self.assertEqual(names, ["Abboca", "Zambon"])


class ConfigLocalizacaoModelTest(TestCase):
    def test_create_global_localizacao(self):
        loc = ConfigLocalizacao.objects.create(
            search_term="NOVA da vila", alias="Guia"
        )
        self.assertIsNone(loc.cliente)
        self.assertEqual(loc.search_term, "NOVA da vila")
        self.assertEqual(loc.alias, "Guia")

    def test_create_cliente_localizacao(self):
        cliente = Cliente.objects.create(nome="Farm X", email="x@test.pt")
        loc = ConfigLocalizacao.objects.create(
            cliente=cliente, search_term="ilha", alias="Ilha"
        )
        self.assertEqual(loc.cliente, cliente)

    def test_localizacao_str_global(self):
        loc = ConfigLocalizacao.objects.create(
            search_term="Colmeias", alias="Colmeias"
        )
        self.assertEqual(str(loc), "[Global] Colmeias -> Colmeias")

    def test_localizacao_str_cliente(self):
        cliente = Cliente.objects.create(nome="Farm X", email="x@test.pt")
        loc = ConfigLocalizacao.objects.create(
            cliente=cliente, search_term="ilha", alias="Ilha"
        )
        self.assertEqual(str(loc), "[Farm X] ilha -> Ilha")

    def test_localizacao_unique_together(self):
        cliente = Cliente.objects.create(nome="Farm X", email="x@test.pt")
        ConfigLocalizacao.objects.create(
            cliente=cliente, search_term="ilha", alias="Ilha"
        )
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ConfigLocalizacao.objects.create(
                cliente=cliente, search_term="ilha", alias="Ilha 2"
            )

    def test_global_and_cliente_same_search_term_allowed(self):
        """Global and client-specific configs with the same search_term are allowed."""
        ConfigLocalizacao.objects.create(search_term="ilha", alias="Ilha Global")
        cliente = Cliente.objects.create(nome="Farm X", email="x@test.pt")
        loc = ConfigLocalizacao.objects.create(
            cliente=cliente, search_term="ilha", alias="Ilha Farm X"
        )
        self.assertIsNotNone(loc.pk)


class ConfigPesoPresetModelTest(TestCase):
    def test_create_preset(self):
        preset = ConfigPesoPreset.objects.create(
            nome="Padrao", pesos=[0.4, 0.3, 0.2, 0.1]
        )
        self.assertEqual(preset.nome, "Padrao")
        self.assertEqual(preset.pesos, [0.4, 0.3, 0.2, 0.1])

    def test_preset_unique_name(self):
        ConfigPesoPreset.objects.create(nome="Conservador", pesos=[0.5, 0.3, 0.15, 0.05])
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ConfigPesoPreset.objects.create(nome="Conservador", pesos=[0.25, 0.25, 0.25, 0.25])

    def test_preset_str(self):
        preset = ConfigPesoPreset.objects.create(
            nome="Agressivo", pesos=[0.25, 0.25, 0.25, 0.25]
        )
        self.assertEqual(str(preset), "Agressivo")


class SessaoProcessamentoModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nome="Cliente Teste", email="t@test.pt")
        self.user = User.objects.create_user("maria", password="pass")

    def test_create_sessao(self):
        sessao = SessaoProcessamento.objects.create(
            cliente=self.cliente,
            utilizador=self.user,
            num_ficheiros=3,
            num_produtos=150,
            num_farmacias=4,
        )
        self.assertEqual(sessao.cliente, self.cliente)
        self.assertEqual(sessao.utilizador, self.user)
        self.assertEqual(sessao.num_ficheiros, 3)
        self.assertEqual(sessao.lab_selecionados, [])
        self.assertFalse(sessao.modo_detalhado)
        self.assertAlmostEqual(sessao.meses_previsao, 1.0)

    def test_sessao_str(self):
        sessao = SessaoProcessamento.objects.create(
            cliente=self.cliente,
            utilizador=self.user,
            num_ficheiros=1,
            num_produtos=10,
            num_farmacias=1,
        )
        self.assertIn("Cliente Teste", str(sessao))

    def test_sessao_ordering_newest_first(self):
        SessaoProcessamento.objects.create(
            cliente=self.cliente,
            utilizador=self.user,
            num_ficheiros=1,
            num_produtos=10,
            num_farmacias=1,
        )
        import time

        time.sleep(0.01)
        SessaoProcessamento.objects.create(
            cliente=self.cliente,
            utilizador=self.user,
            num_ficheiros=2,
            num_produtos=20,
            num_farmacias=2,
        )
        sessoes = list(SessaoProcessamento.objects.values_list("num_ficheiros", flat=True))
        self.assertEqual(sessoes, [2, 1])