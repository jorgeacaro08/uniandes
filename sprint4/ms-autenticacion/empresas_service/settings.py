"""Configuracion del microservicio de autenticacion (Manejador de Autenticacion).

La base de datos se toma de variables de entorno (PostgreSQL en despliegue).
Si AUTH_DB_HOST no esta definido, usa SQLite local para poder ejecutar
`manage.py check`/`migrate` sin un servidor Postgres (validacion local).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-auth-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "empresas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "empresas_service.urls"
TEMPLATES = []
WSGI_APPLICATION = "empresas_service.wsgi.application"

_db_host = os.getenv("AUTH_DB_HOST")
if _db_host:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("AUTH_DB_NAME", "auth_db"),
            "USER": os.getenv("AUTH_DB_USER", "monitoring_user"),
            "PASSWORD": os.getenv("AUTH_DB_PASSWORD", "isis2503"),
            "HOST": _db_host,
            "PORT": os.getenv("AUTH_DB_PORT", "5432"),
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
