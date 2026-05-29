"""Acceso a MongoDB para el modelo de lectura (reporte consolidado precalculado).

Se usa pymongo (sincrono) para facilitar las pruebas con mongomock. La lectura es
un unico find_one indexado por (empresa, periodo): O(log n), clave del ASR de latencia.
"""
import os

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        import pymongo

        uri = os.getenv(
            "MONGO_URI",
            "mongodb://monitoring_user:isis2503@localhost:27017/?retryWrites=true&w=majority",
        )
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        _collection = client[os.getenv("MONGO_DB", "reportes_db")][
            os.getenv("MONGO_COLLECTION", "reportes_consolidados")
        ]
        _collection.create_index([("empresa", 1), ("periodo", 1)], unique=True)
    return _collection


def set_collection(collection):
    """Inyeccion para pruebas (p.ej. mongomock)."""
    global _collection
    _collection = collection
