from django.db import models


class RegistroCostoCrudo(models.Model):
    """Registro granular de costo cloud (dato crudo). Fuente de verdad relacional.

    Es la tabla grande (millones de filas) cuya agregacion en caliente genera
    latencia; el extractor la consolida fuera del request hacia MongoDB.
    """
    empresa = models.CharField(max_length=20)       # NIT de la empresa
    proveedor = models.CharField(max_length=10)      # AWS | GCP
    servicio = models.CharField(max_length=50)       # EC2, S3, ComputeEngine, ...
    fecha = models.DateField()
    periodo = models.CharField(max_length=7)         # YYYY-MM (denormalizado)
    cpu_avg = models.FloatField(default=0.0)
    netout_gb = models.FloatField(default=0.0)
    costo = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    class Meta:
        indexes = [
            models.Index(fields=["empresa", "periodo"]),
            models.Index(fields=["periodo"]),
        ]

    def __str__(self):
        return f"{self.empresa} {self.proveedor} {self.fecha} ${self.costo}"
