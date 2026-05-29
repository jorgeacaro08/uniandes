"""Puebla la BD de empresas con un numero de clientes consecuente con el negocio.

Uso: python manage.py seed_empresas --empresas 500
Los NIT coinciden con los usados por el extractor (NIT9000000xx) para que el
flujo de validacion y consolidacion sea coherente.
"""
import random

from django.core.management.base import BaseCommand

from empresas.models import Empresa

SECTORES = ["Tecnologia", "Retail", "Finanzas", "Salud", "Manufactura", "Logistica"]


class Command(BaseCommand):
    help = "Puebla la BD de empresas clientes."

    def add_arguments(self, parser):
        parser.add_argument("--empresas", type=int, default=500)

    def handle(self, *args, **o):
        objs = [
            Empresa(
                nit=f"NIT{900000000 + i}",
                nombre=f"Empresa Cliente {i}",
                sector=random.choice(SECTORES),
                activa=True,
            )
            for i in range(o["empresas"])
        ]
        Empresa.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f"Insertadas {len(objs)} empresas"))
