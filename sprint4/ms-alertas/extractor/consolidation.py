"""Logica de consolidacion (Computed Pattern).

Agrega los registros crudos de PostgreSQL por (empresa, periodo) y produce el
documento consolidado que se materializa en MongoDB. Reutiliza el esquema y el
hash de integridad del Sprint 3 (Facturacion_Consolidada).
"""
import hashlib
from datetime import datetime, timezone

from django.db.models import Sum, Avg

from .models import RegistroCostoCrudo


def _agg(empresa, periodo, proveedor):
    r = RegistroCostoCrudo.objects.filter(
        empresa=empresa, periodo=periodo, proveedor=proveedor
    ).aggregate(cpu=Avg("cpu_avg"), net=Sum("netout_gb"), costo=Sum("costo"))
    return (
        float(r["cpu"] or 0.0),
        float(r["net"] or 0.0),
        float(r["costo"] or 0.0),
    )


def generar_hash(empresa, periodo, costo_total):
    data = f"{empresa}|{costo_total:.2f}|{periodo}"
    return hashlib.sha256(data.encode()).hexdigest()


def calcular_consolidado(empresa, periodo):
    """Calcula el consolidado agregando los crudos (operacion costosa)."""
    cpu_aws, net_aws, costo_aws = _agg(empresa, periodo, "AWS")
    cpu_gcp, net_gcp, costo_gcp = _agg(empresa, periodo, "GCP")
    costo_total = round(costo_aws + costo_gcp, 2)
    return {
        "empresa": empresa,
        "periodo": periodo,
        "cpu_avg_aws": round(cpu_aws, 2),
        "netout_gb_aws": round(net_aws, 2),
        "cpu_avg_gcp": round(cpu_gcp, 2),
        "netout_gb_gcp": round(net_gcp, 2),
        "costo_aws": round(costo_aws, 2),
        "costo_gcp": round(costo_gcp, 2),
        "costo_total": costo_total,
        "hash": generar_hash(empresa, periodo, costo_total),
        "generado_en": datetime.now(timezone.utc).isoformat(),
    }


def consolidar_a_mongo(empresa, periodo):
    """Precalcula y materializa el consolidado en MongoDB (modelo de lectura)."""
    doc = calcular_consolidado(empresa, periodo)
    from .mongo import get_collection

    coll = get_collection()
    coll.replace_one({"empresa": empresa, "periodo": periodo}, doc, upsert=True)
    return doc
