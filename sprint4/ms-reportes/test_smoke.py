"""Smoke test local de ms-reportes sin servidor Mongo (usa mongomock).

Valida: lectura precalculada, 401 sin token, 403 cross-empresa, 200 con token valido.
Ejecutar dentro del venv:  python test_smoke.py   (o: pytest test_smoke.py)
"""
import os

os.environ.setdefault("AUTH_ENABLED", "true")
os.environ.setdefault("AUTH_PROVIDER", "local")
os.environ.setdefault("AUTH_SECRET", "test-secret")

import jwt
import mongomock
from fastapi.testclient import TestClient

import db
from main import app

# Inyecta una coleccion mongomock con un reporte de ejemplo.
_coll = mongomock.MongoClient().reportes_db.reportes_consolidados
_coll.create_index([("empresa", 1), ("periodo", 1)], unique=True)
_coll.insert_one(
    {
        "empresa": "NIT900000000",
        "periodo": "2025-01",
        "costo_aws": 10.0,
        "costo_gcp": 5.0,
        "costo_total": 15.0,
        "hash": "x",
        "generado_en": "2025-02-01T00:00:00Z",
    }
)
db.set_collection(_coll)

client = TestClient(app)


def _token(empresa, roles=None):
    payload = {"sub": "u1", "empresa": empresa, "roles": roles or ["finanzas"]}
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def run():
    # Sin token -> 401
    r = client.get("/reportes", params={"empresa": "NIT900000000", "periodo": "2025-01"})
    assert r.status_code == 401, r.status_code

    # Token de otra empresa -> 403
    r = client.get(
        "/reportes",
        params={"empresa": "NIT900000000", "periodo": "2025-01"},
        headers={"Authorization": "Bearer " + _token("NIT999999999")},
    )
    assert r.status_code == 403, r.status_code

    # Token valido de la empresa -> 200 con el reporte
    r = client.get(
        "/reportes",
        params={"empresa": "NIT900000000", "periodo": "2025-01"},
        headers={"Authorization": "Bearer " + _token("NIT900000000")},
    )
    assert r.status_code == 200, r.status_code
    assert r.json()["costo_total"] == 15.0
    assert "_id" not in r.json()

    # Periodo inexistente -> 404
    r = client.get(
        "/reportes",
        params={"empresa": "NIT900000000", "periodo": "1999-01"},
        headers={"Authorization": "Bearer " + _token("NIT900000000")},
    )
    assert r.status_code == 404, r.status_code

    print("OK: 401 sin token, 403 cross-empresa, 200 valido, 404 inexistente")


def test_smoke():
    run()


if __name__ == "__main__":
    run()
