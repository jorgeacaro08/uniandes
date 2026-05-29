"""Configuracion del microservicio Gestor de Alertas (ingesta + precalculo).

PostgreSQL (datos crudos) via variables de entorno ALERTAS_DB_*; si no estan,
usa SQLite local para validacion. La conexion a MongoDB (destino del consolidado)
se configura con MONGO_URI / MONGO_DB / MONGO_COLLECTION y la usa extractor/mongo.py.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-alertas-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "extractor",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "extractor_service.urls"
TEMPLATES = []
WSGI_APPLICATION = "extractor_service.wsgi.application"

_db_host = os.getenv("ALERTAS_DB_HOST")
if _db_host:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("ALERTAS_DB_NAME", "alertas_db"),
            "USER": os.getenv("ALERTAS_DB_USER", "monitoring_user"),
            "PASSWORD": os.getenv("ALERTAS_DB_PASSWORD", "isis2503"),
            "HOST": _db_host,
            "PORT": os.getenv("ALERTAS_DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "local.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
