import json
import os
import tempfile

from django.core.management import call_command
from django.test import TestCase

from orders.models import ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset


class ImportLabsJsonCommandTest(TestCase):
    def test_import_creates_labs(self):
        data = {"Mylan": ["137", "2651"], "Teva": ["2326", "2618"]}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp_path = f.name

        try:
            call_command("import_labs_json", tmp_path)
            self.assertEqual(ConfigLaboratorio.objects.count(), 2)
            mylan = ConfigLaboratorio.objects.get(nome="Mylan")
            self.assertEqual(mylan.codigos_cla, ["137", "2651"])
        finally:
            os.unlink(tmp_path)

    def test_import_idempotent_update_or_create(self):
        ConfigLaboratorio.objects.create(nome="Mylan", codigos_cla=["137"])
        data = {"Mylan": ["137", "2651", "2953"]}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp_path = f.name

        try:
            call_command("import_labs_json", tmp_path)
            self.assertEqual(ConfigLaboratorio.objects.count(), 1)
            mylan = ConfigLaboratorio.objects.get(nome="Mylan")
            self.assertEqual(mylan.codigos_cla, ["137", "2651", "2953"])
        finally:
            os.unlink(tmp_path)

    def test_import_nonexistent_file(self):
        from io import StringIO

        stderr = StringIO()
        call_command("import_labs_json", "/nonexistent/path.json", stderr=stderr)
        self.assertIn("nao encontrado", stderr.getvalue())


class ImportLocationsJsonCommandTest(TestCase):
    def test_import_creates_global_locations(self):
        data = {"NOVA da vila": "Guia", "ilha": "Ilha"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp_path = f.name

        try:
            call_command("import_locations_json", tmp_path)
            self.assertEqual(ConfigLocalizacao.objects.count(), 2)
            loc = ConfigLocalizacao.objects.get(search_term="NOVA da vila")
            self.assertEqual(loc.alias, "Guia")
            self.assertIsNone(loc.cliente)
        finally:
            os.unlink(tmp_path)

    def test_import_idempotent_update_or_create(self):
        ConfigLocalizacao.objects.create(search_term="ilha", alias="Ilha")
        data = {"ilha": "Ilha Updated"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp_path = f.name

        try:
            call_command("import_locations_json", tmp_path)
            self.assertEqual(ConfigLocalizacao.objects.count(), 1)
            loc = ConfigLocalizacao.objects.get(search_term="ilha")
            self.assertEqual(loc.alias, "Ilha Updated")
        finally:
            os.unlink(tmp_path)

    def test_import_nonexistent_file(self):
        from io import StringIO

        stderr = StringIO()
        call_command("import_locations_json", "/nonexistent/path.json", stderr=stderr)
        self.assertIn("nao encontrado", stderr.getvalue())


class ImportPresetsYamlCommandTest(TestCase):
    def test_import_creates_presets(self):
        yaml_content = "presets:\n  Padrao: [0.4, 0.3, 0.2, 0.1]\n  Conservador: [0.5, 0.3, 0.15, 0.05]\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = f.name

        try:
            call_command("import_presets_yaml", tmp_path)
            self.assertEqual(ConfigPesoPreset.objects.count(), 2)
            padrao = ConfigPesoPreset.objects.get(nome="Padrao")
            self.assertEqual(padrao.pesos, [0.4, 0.3, 0.2, 0.1])
        finally:
            os.unlink(tmp_path)

    def test_import_idempotent_update_or_create(self):
        ConfigPesoPreset.objects.create(nome="Padrao", pesos=[0.4, 0.3, 0.2, 0.1])
        yaml_content = "presets:\n  Padrao: [0.5, 0.25, 0.15, 0.1]\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = f.name

        try:
            call_command("import_presets_yaml", tmp_path)
            self.assertEqual(ConfigPesoPreset.objects.count(), 1)
            padrao = ConfigPesoPreset.objects.get(nome="Padrao")
            self.assertEqual(padrao.pesos, [0.5, 0.25, 0.15, 0.1])
        finally:
            os.unlink(tmp_path)

    def test_import_nonexistent_file(self):
        from io import StringIO

        stderr = StringIO()
        call_command("import_presets_yaml", "/nonexistent/path.yaml", stderr=stderr)
        self.assertIn("nao encontrado", stderr.getvalue())