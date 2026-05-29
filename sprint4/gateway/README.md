# Gateway (Kong) — API Gateway / Orquestador

Punto único de entrada del experimento. Enruta hacia los 3 microservicios y, en
producción, valida el JWT de Auth0.

## Rutas
| Path | Microservicio | ASR |
|---|---|---|
| `GET /reportes?empresa&periodo` | ms-reportes (FastAPI+Mongo) | Latencia (lectura precalculada) |
| `GET /reporte-oncall?empresa&periodo` | ms-alertas (Django+Postgres) | Línea base (anti-patrón, agrega crudos) |
| `POST /consolidar` | ms-alertas | Precálculo del consolidado → Mongo |
| `GET/POST /empresas` | ms-autenticacion (Django+Postgres) | Registro/validación |

## Autenticación
- **Local/pruebas:** la autenticación y autorización se hacen en `ms-reportes/auth.py`
  (HS256), activables con `AUTH_ENABLED` para la prueba de trade-off.
- **Producción (Auth0):** habilitar el plugin `jwt` de Kong sobre la ruta `reportes`
  (RS256, clave pública de Auth0). Ver el bloque comentado en `kong.yaml`.

El cambio de proveedor de identidad (Auth0 → Keycloak) solo afecta a este gateway
+ `ms-reportes/auth.py` (`AUTH_PROVIDER`), evidenciando el ASR de mantenibilidad.
