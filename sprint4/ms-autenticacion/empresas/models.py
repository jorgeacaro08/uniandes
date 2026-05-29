from django.db import models


class Empresa(models.Model):
    """Empresa cliente de BITE.co. Usado para validar el alcance de los reportes."""
    nit = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True, default="")
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["nit"])]

    def to_dict(self):
        return {
            "nit": self.nit,
            "nombre": self.nombre,
            "sector": self.sector,
            "activa": self.activa,
        }

    def __str__(self):
        return f"{self.nombre} ({self.nit})"
