"""Pobla MongoDB directamente con reportes consolidados (rapido, a escala).

Alternativa al flujo realista (seed_crudos en Postgres + `manage.py consolidar`).
Util para la prueba de latencia cuando solo se necesita el modelo de lectura.

Uso:  python seed_mongo.py --empresas 500 --meses 24
Requiere MONGO_URI (o usa localhost por defecto). Volumen consecuente con el
crecimiento: 500 empresas x 24 meses = 12.000 documentos consolidados.
"""
import argparse
import hashlib
import os
import random
from datetime import datetime, timezone

import pymongo


def periodos(inicio, meses):
    y, m = (int(x) for x in inicio.split("-"))
    out = []
    for _ in range(meses):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def doc(empresa, periodo):
    costo_aws = round(random.uniform(1000, 50000), 2)
    costo_gcp = round(random.uniform(1000, 50000), 2)
    total = round(costo_aws + costo_gcp, 2)
    h = hashlib.sha256(f"{empresa}|{total:.2f}|{periodo}".encode()).hexdigest()
    return {
        "empresa": empresa,
        "periodo": periodo,
        "cpu_avg_aws": round(random.uniform(5, 95), 2),
        "netout_gb_aws": round(random.uniform(10, 5000), 2),
        "cpu_avg_gcp": round(random.uniform(5, 95), 2),
        "netout_gb_gcp": round(random.uniform(10, 5000), 2),
        "costo_aws": costo_aws,
        "costo_gcp": costo_gcp,
        "costo_total": total,
        "hash": h,
        "generado_en": datetime.now(timezone.utc).isoformat(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--empresas", type=int, default=500)
    ap.add_argument("--meses", type=int, default=24)
    ap.add_argument("--inicio", default="2024-01")
    a = ap.parse_args()

    uri = os.getenv(
        "MONGO_URI", "mongodb://monitoring_user:isis2503@localhost:27017/?authSource=admin"
    )
    coll = pymongo.MongoClient(uri)[os.getenv("MONGO_DB", "reportes_db")][
        os.getenv("MONGO_COLLECTION", "reportes_consolidados")
    ]
    coll.create_index([("empresa", 1), ("periodo", 1)], unique=True)

    pers = periodos(a.inicio, a.meses)
    batch, n = [], 0
    for i in range(a.empresas):
        emp = f"NIT{900000000 + i}"
        for per in pers:
            d = doc(emp, per)
            batch.append(
                pymongo.ReplaceOne({"empresa": emp, "periodo": per}, d, upsert=True)
            )
            if len(batch) >= 2000:
                coll.bulk_write(batch)
                n += len(batch)
                batch = []
    if batch:
        coll.bulk_write(batch)
        n += len(batch)
    print(f"Insertados/actualizados {n} consolidados en Mongo")


if __name__ == "__main__":
    main()
