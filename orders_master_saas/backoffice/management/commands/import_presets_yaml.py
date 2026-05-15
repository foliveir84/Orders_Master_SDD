from pathlib import Path

from django.core.management.base import BaseCommand

from orders.models import ConfigPesoPreset

try:
    import yaml
except ImportError:
    yaml = None


class Command(BaseCommand):
    help = "Importa presets de pesos a partir de um ficheiro YAML para ConfigPesoPreset"

    def add_arguments(self, parser):
        parser.add_argument(
            "yaml_path",
            type=str,
            help="Caminho para o ficheiro presets.yaml",
        )

    def handle(self, *args, **options):
        if yaml is None:
            self.stderr.write(self.style.ERROR("Biblioteca PyYAML nao instalada. Instale com: pip install pyyaml"))
            return

        yaml_path = Path(options["yaml_path"])
        if not yaml_path.exists():
            self.stderr.write(self.style.ERROR(f"Ficheiro nao encontrado: {yaml_path}"))
            return

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        presets_data = data.get("presets", {})
        created_count = 0
        updated_count = 0

        for nome, pesos in presets_data.items():
            preset, created = ConfigPesoPreset.objects.update_or_create(
                nome=nome,
                defaults={"pesos": pesos},
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importacao concluida: {created_count} criados, {updated_count} actualizados"
            )
        )