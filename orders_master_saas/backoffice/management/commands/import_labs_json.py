import json
from pathlib import Path

from django.core.management.base import BaseCommand

from orders.models import ConfigLaboratorio


class Command(BaseCommand):
    help = "Importa laboratorios a partir de um ficheiro JSON para ConfigLaboratorio"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Caminho para o ficheiro laboratorios.json",
        )

    def handle(self, *args, **options):
        json_path = Path(options["json_path"])
        if not json_path.exists():
            self.stderr.write(self.style.ERROR(f"Ficheiro nao encontrado: {json_path}"))
            return

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        created_count = 0
        updated_count = 0

        for nome, codigos in data.items():
            lab, created = ConfigLaboratorio.objects.update_or_create(
                nome=nome,
                defaults={"codigos_cla": codigos},
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