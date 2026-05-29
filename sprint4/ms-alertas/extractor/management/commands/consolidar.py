"""Precalcula los reportes consolidados y los materializa en MongoDB.

Recorre los pares (empresa, periodo) presentes en los crudos y escribe un
documento por cada uno (Computed Pattern). Ejecutar tras seed_crudos y de forma
periodica en produccion (cron / AWS Lambda + CloudWatch Events).

Ejemplo: python manage.py consolidar            # todos los periodos
         python manage.py consolidar --periodo 2025-01
"""
from django.core.management.base import BaseCommand

from extractor.models import RegistroCostoCrudo
from extractor.consolidation import consolidar_a_mongo


class Command(BaseCommand):
    help = "Materializa los reportes consolidados (empresa, periodo) en MongoDB."

    def add_arguments(self, parser):
        parser.add_argument("--periodo", type=str, default=None)

    def handle(self, *args, **o):
        pares = RegistroCostoCrudo.objects.values_list("empresa", "periodo").distinct()
        if o["periodo"]:
            pares = pares.filter(periodo=o["periodo"])
        n = 0
        for empresa, periodo in pares:
            consolidar_a_mongo(empresa, periodo)
            n += 1
            if n % 100 == 0:
                self.stdout.write(f"  ...{n} consolidados")
        self.stdout.write(self.style.SUCCESS(f"Consolidados {n} reportes en Mongo"))
