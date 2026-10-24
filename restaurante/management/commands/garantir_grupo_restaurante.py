from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Garante que o grupo Restaurante existe."

    def handle(self, *args, **options):
        grupo, criado = Group.objects.get_or_create(
            name="Restaurante"
        )

        if criado:
            self.stdout.write(
                self.style.SUCCESS(
                    "Grupo Restaurante criado com sucesso."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "O grupo Restaurante já existia."
                )
            )
