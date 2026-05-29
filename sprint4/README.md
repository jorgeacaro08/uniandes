# BITE.co — Sprint 4: Microservicios (Latencia + Seguridad + Mantenibilidad)

Experimento de microservicios sobre la funcionalidad de consultar el reporte
consolidado de gasto mensual por empresa. Tres ASR:

- **Latencia** — visualizar el reporte consolidado en ≤ 1 s.
- **Seguridad** — solo usuarios autenticados/autorizados; 100% de no autorizadas rechazadas, ≥99% de válidas procesadas (5 min).
- **Mantenibilidad** — reemplazar Auth0 por Keycloak tocando solo el Manejador de Autenticación (≤ 4 h, ≤ 1 componente).

## Arquitectura
API Gateway **Kong** → 3 microservicios, cada uno con su BD (Database-per-Service):

| Microservicio (carpeta) | Componente del wiki | Tecnología | BD | ASR |
|---|---|---|---|---|
| **ms-reportes** | Manejador de Reportes | FastAPI | **MongoDB** | Latencia (lee 1 documento precalculado) |
| **ms-autenticacion** | Manejador de Autenticación | Django | PostgreSQL | Seguridad + Mantenibilidad (encapsula Auth0/Keycloak) |
| **ms-alertas** | Gestor de Alertas | Django | PostgreSQL → **MongoDB** | Negocio (ingesta + precálculo Computed + anti-patrón) |

**Patrones (≠ descomposición):** API Gateway, Database-per-Service, Computed Pattern, CQRS.
**2 tecnologías:** Django + FastAPI. **2 BD:** PostgreSQL + MongoDB (NoSQL).
**Táctica de latencia:** Computed Pattern + índice `(empresa, periodo)` en Mongo → lectura O(log n).
**Táctica de seguridad:** autenticar + autorizar actores (Auth0/JWT, alcance por empresa) en `ms-reportes/auth.py`.
**Mantenibilidad:** proveedor encapsulado (`AUTH_PROVIDER=auth0|keycloak`); cambiarlo solo toca `auth.py`.

## Estructura
```
gateway/            Kong declarativo (kong.yaml)
ms-reportes/        FastAPI + Mongo  (latencia + auth)
ms-autenticacion/   Django + Postgres (registro empresas/usuarios)
ms-alertas/         Django + Postgres + escribe a Mongo (ingesta + precálculo + anti-patrón)
seed/               poblado de datos a escala de negocio
load-tests/         planes JMeter + gen_token.py
deploy/aws/         runbook de despliegue en AWS (paso a paso)
docker-compose.yml  orquestación local
```

## Ejecutar localmente (Docker)
```bash
cp .env.example .env
docker compose up -d --build
# Sembrar datos
docker compose exec ms-autenticacion python manage.py seed_empresas --empresas 500
docker compose exec ms-alertas python manage.py seed_crudos --empresas 50 --meses 24
docker compose exec ms-alertas python manage.py consolidar
# Token y prueba (a través del gateway, puerto 8000)
pip install pyjwt
TOKEN=$(cd load-tests && AUTH_SECRET=dev-secret python gen_token.py NIT900000000 finanzas)
curl "http://localhost:8000/reportes?empresa=NIT900000000&periodo=2025-01" -H "Authorization: Bearer $TOKEN"
```

## Pruebas de carga
Ver [load-tests/README.md](load-tests/README.md): latencia (normal/sobrecarga + anti-patrón), seguridad (5 min) y trade-off con/sin seguridad.

## Despliegue en AWS
Ver [deploy/aws/README.md](deploy/aws/README.md) (paso a paso, 1 EC2 por servicio).
