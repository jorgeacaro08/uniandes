"""Acceso a MongoDB (destino del reporte consolidado).

pymongo se importa de forma perezosa para que `manage.py check`/`seed_crudos`
funcionen aunque pymongo no este instalado (solo se necesita al consolidar).
"""
import os


def get_collection():
    import pymongo

    uri = os.getenv(
        "MONGO_URI",
        "mongodb://monitoring_user:isis2503@localhost:27017/?retryWrites=true&w=majority",
    )
    db_name = os.getenv("MONGO_DB", "reportes_db")
    coll_name = os.getenv("MONGO_COLLECTION", "reportes_consolidados")
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    coll = client[db_name][coll_name]
    # Indice que hace O(log n) la lectura por (empresa, periodo): clave de la latencia.
    coll.create_index([("empresa", 1), ("periodo", 1)], unique=True)
    return coll
