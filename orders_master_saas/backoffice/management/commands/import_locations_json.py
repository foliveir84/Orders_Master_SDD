import json
from pathlib import Path

from django.core.management.base import BaseCommand

from orders.models import ConfigLocalizacao


class Command(BaseCommand):
    help = "Importa localizacoes globais a partir de um ficheiro JSON para ConfigLocalizacao"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Caminho para o ficheiro localizacoes.json",
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

        for search_term, alias in data.items():
            loc, created = ConfigLocalizacao.objects.update_or_create(
                cliente=None,
                search_term=search_term,
                defaults={"alias": alias},
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