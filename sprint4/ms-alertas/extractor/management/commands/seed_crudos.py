"""Puebla PostgreSQL con registros de costo crudos a escala de negocio.

Ejemplo: python manage.py seed_crudos --empresas 50 --meses 24
Por defecto genera ~50 empresas x 24 meses x ~30 dias x 9 servicios = ~324k filas.
Para acercarse a 1-2M, suba --empresas (p.ej. 200) o --meses.
"""
import calendar
import random
from datetime import date

from django.core.management.base import BaseCommand

from extractor.models import RegistroCostoCrudo

SERVICIOS = {
    "AWS": ["EC2", "S3", "RDS", "Lambda", "CloudWatch"],
    "GCP": ["ComputeEngine", "CloudStorage", "BigQuery", "CloudFunctions"],
}


def iter_periodos(inicio, meses):
    y, m = (int(x) for x in inicio.split("-"))
    for _ in range(meses):
        yield f"{y:04d}-{m:02d}", y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


class Command(BaseCommand):
    help = "Puebla la BD relacional con registros de costo crudos."

    def add_arguments(self, parser):
        parser.add_argument("--empresas", type=int, default=50)
        parser.add_argument("--meses", type=int, default=24)
        parser.add_argument("--inicio", type=str, default="2024-01")
        parser.add_argument("--batch", type=int, default=5000)

    def handle(self, *args, **o):
        empresas = [f"NIT{900000000 + i}" for i in range(o["empresas"])]
        buf, total = [], 0
        for emp in empresas:
            for periodo, y, m in iter_periodos(o["inicio"], o["meses"]):
                dias = calendar.monthrange(y, m)[1]
                for d in range(1, dias + 1):
                    fecha = date(y, m, d)
                    for prov, servicios in SERVICIOS.items():
                        for serv in servicios:
                            buf.append(
                                RegistroCostoCrudo(
                                    empresa=emp,
                                    proveedor=prov,
                                    servicio=serv,
                                    fecha=fecha,
                                    periodo=periodo,
                                    cpu_avg=round(random.uniform(5, 95), 2),
                                    netout_gb=round(random.uniform(0.1, 50), 3),
                                    costo=round(random.uniform(0.5, 200), 4),
                                )
                            )
                            if len(buf) >= o["batch"]:
                                RegistroCostoCrudo.objects.bulk_create(
                                    buf, ignore_conflicts=True
                                )
                                total += len(buf)
                                buf = []
        if buf:
            RegistroCostoCrudo.objects.bulk_create(buf, ignore_conflicts=True)
            total += len(buf)
        self.stdout.write(self.style.SUCCESS(f"Insertados {total} registros crudos"))
