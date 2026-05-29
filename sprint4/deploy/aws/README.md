# Despliegue en AWS — Guía paso a paso (una EC2 por microservicio)

Despliegue del experimento con **una EC2 por microservicio** + 1 EC2 de datos + 1 ALB.
Coincide con la vista de despliegue del Sprint 4. Pensado para seguirse de principio a fin.

> 💡 **Modo recomendado para el experimento:** usar **AUTH_PROVIDER=local** (HS256 con `gen_token.py`).
> Es reproducible en JMeter sin depender de Auth0. La arquitectura mantiene la abstracción del
> proveedor (sustenta el ASR de mantenibilidad). Auth0 queda como Paso 7 opcional para producción.

## Topología
```
Cliente/JMeter ──HTTP──> ALB ──> EC2 "kong" (:8000)
                                   ├─> EC2 "ms-reportes"     (:8080) ──> Mongo (EC2 datos :27017)
                                   ├─> EC2 "ms-alertas"      (:8080) ──> Postgres alertas (EC2 datos :5432) + Mongo
                                   └─> EC2 "ms-autenticacion"(:8080) ──> Postgres auth (EC2 datos :5433)
```
**5 EC2** (`kong`, `ms-reportes`, `ms-alertas`, `ms-autenticacion`, `datos`) + **1 ALB**.
**AMI:** Amazon Linux 2023 (`al2023-ami-*`, búscala en el asistente). **Tipo:** `t3.small` basta.
**Almacenamiento:** 8 GB (default). **Llave:** la misma `bite-key.pem` para todas.

> 💰 Detén o termina las instancias al terminar para no incurrir en costos.

---

## Paso 0 — Subir el código al repositorio
```bash
cd uniandes
git add sprint4 && git commit -m "Sprint 4: microservicios"
git push origin main
```
Repo: https://github.com/jorgeacaro08/uniandes (carpeta `sprint4/`).

## Paso 1 — Llave, Security Groups
1. **Key pair:** EC2 → Network & Security → Key Pairs → Create → `bite-key` (formato `.pem`). Guárdala.
2. **Security Groups** (VPC por defecto):

| SG | Regla de entrada | Puerto | Origen |
|---|---|---|---|
| `sg-alb` | HTTP | 80 | 0.0.0.0/0 |
| `sg-kong` | Custom TCP | 8000 | `sg-alb` |
| `sg-kong` | SSH | 22 | tu IP |
| `sg-svc` | Custom TCP | 8080 | `sg-kong` |
| `sg-svc` | SSH | 22 | tu IP |
| `sg-datos` | PostgreSQL | 5432-5433 | `sg-svc` |
| `sg-datos` | Custom TCP (Mongo) | 27017 | `sg-svc` |
| `sg-datos` | SSH | 22 | tu IP |

> En *Source* selecciona el SG (no una IP) para autorizar de un SG a otro.

## Paso 2 — Lanzar las 5 EC2
Por cada instancia: AMI = Amazon Linux 2023, tipo = `t3.small`, almacenamiento 8 GB, key = `bite-key`, SG según rol:

| Nombre (Tag Name) | Security Group | Rol |
|---|---|---|
| `datos` | `sg-datos` | PostgreSQL x2 + MongoDB (contenedores) |
| `ms-reportes` | `sg-svc` | FastAPI + Mongo |
| `ms-alertas` | `sg-svc` | Django + Postgres → Mongo |
| `ms-autenticacion` | `sg-svc` | Django + Postgres |
| `kong` | `sg-kong` | Gateway |

Cuando estén corriendo, anota para cada una:
- **Public IPv4** (para SSH): EC2 → Instances → click instancia → pestaña *Details*.
- **Private IPv4** (para conexión interna): misma pestaña.

**Conectarse por SSH:**
```bash
chmod 400 bite-key.pem       # solo la primera vez (en Linux/macOS/WSL)
ssh -i bite-key.pem ec2-user@<PUBLIC_IPv4>
```
> En Windows con PowerShell: `ssh -i .\bite-key.pem ec2-user@<PUBLIC_IPv4>`.

**En cada EC2**, una vez dentro, instala Docker + git:
```bash
sudo dnf update -y && sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user && newgrp docker
git clone https://github.com/jorgeacaro08/uniandes.git && cd uniandes/sprint4
```

## Paso 3 — EC2 "datos" (las 2 BD)
```bash
# PostgreSQL alertas (ms-alertas, datos crudos)
docker run -d --name pg-alertas -e POSTGRES_DB=alertas_db \
  -e POSTGRES_USER=monitoring_user -e POSTGRES_PASSWORD=isis2503 -p 5432:5432 postgres:16
# PostgreSQL auth (ms-autenticacion)
docker run -d --name pg-auth -e POSTGRES_DB=auth_db \
  -e POSTGRES_USER=monitoring_user -e POSTGRES_PASSWORD=isis2503 -p 5433:5432 postgres:16
# MongoDB (ms-alertas escribe, ms-reportes lee)
docker run -d --name mongo -e MONGO_INITDB_ROOT_USERNAME=monitoring_user \
  -e MONGO_INITDB_ROOT_PASSWORD=isis2503 -p 27017:27017 mongo:7
```
Anota la **Private IP** de esta instancia como `DATOS_IP`.

## Paso 4 — EC2 "ms-autenticacion"
```bash
cd uniandes/sprint4/ms-autenticacion && docker build -t ms-autenticacion .
docker run -d --name ms-autenticacion -p 8080:8080 \
  -e AUTH_DB_HOST=172.31.2.238 -e AUTH_DB_PORT=5433 -e AUTH_DB_NAME=auth_db \
  -e AUTH_DB_USER=monitoring_user -e AUTH_DB_PASSWORD=isis2503 ms-autenticacion
docker exec ms-autenticacion python manage.py seed_empresas --empresas 500
```

## Paso 5 — EC2 "ms-alertas"
```bash
cd uniandes/sprint4/ms-alertas && docker build -t ms-alertas .
docker run -d --name ms-alertas -p 8080:8080 \
  -e ALERTAS_DB_HOST=<DATOS_IP> -e ALERTAS_DB_PORT=5432 -e ALERTAS_DB_NAME=alertas_db \
  -e ALERTAS_DB_USER=monitoring_user -e ALERTAS_DB_PASSWORD=isis2503 \
  -e MONGO_URI="mongodb://monitoring_user:isis2503@172.31.2.238:27017/?authSource=admin" \
  -e MONGO_DB=reportes_db -e MONGO_COLLECTION=reportes_consolidados ms-alertas
docker exec ms-alertas python manage.py seed_crudos --empresas 50 --meses 24
docker exec ms-alertas python manage.py consolidar
```

## Paso 6 — EC2 "ms-reportes"
```bash
cd uniandes/sprint4/ms-reportes && docker build -t ms-reportes .
docker run -d --name ms-reportes -p 8080:8080 \
  -e MONGO_URI="mongodb://monitoring_user:isis2503@172.31.2.238:27017/?authSource=admin" \
  -e MONGO_DB=reportes_db -e MONGO_COLLECTION=reportes_consolidados \
  -e AUTH_ENABLED=true -e AUTH_PROVIDER=local -e AUTH_SECRET=dev-secret ms-reportes
```
> Para producción con Auth0 (Paso 7): `AUTH_PROVIDER=auth0`, `AUTH0_DOMAIN=...`, `AUTH0_AUDIENCE=...`.

## Paso 7 — Auth0 (OPCIONAL, producción)
1. Auth0 → **Applications → APIs → Create API**. Identifier (audience): `https://api.bite.co/reportes`. Algoritmo **RS256**.
2. **Roles:** crea `finanzas` y `admin` (User Management → Roles).
3. **Claim de empresa** vía Action *Login / Post Login*:
   ```js
   exports.onExecutePostLogin = async (event, api) => {
     api.accessToken.setCustomClaim('empresa', event.user.app_metadata?.empresa || '');
     api.accessToken.setCustomClaim('roles', event.authorization?.roles || []);
   };
   ```
4. Asigna `empresa` (en *app_metadata*) y rol a cada usuario.
5. Cambia `ms-reportes` a `AUTH_PROVIDER=auth0` con `AUTH0_DOMAIN` y `AUTH0_AUDIENCE`.

**Mantenibilidad:** swap Auth0 → Keycloak = solo `AUTH_PROVIDER` + adaptador en `auth.py` (1 componente).

## Paso 8 — EC2 "kong" (gateway)
Edita `gateway/kong.yaml` reemplazando los hosts por las IP privadas:
```yaml
services:
  - name: reportes-service
    url: http://172.31.6.74:8080
    routes: [{ name: reportes, paths: ["/reportes"], strip_path: false }, { name: health, paths: ["/health"], strip_path: false }]
  - name: autenticacion-service
    url: http://172.31.6.52:8080
    routes: [{ name: empresas, paths: ["/empresas"], strip_path: false }]
  - name: alertas-service
    url: http://172.31.5.114:8080
    routes: [{ name: oncall, paths: ["/reporte-oncall"], strip_path: false }, { name: consolidar, paths: ["/consolidar"], strip_path: false }]
```
Arranca Kong:
```bash
cd uniandes/sprint4
docker run -d --name kong -p 8000:8000 -p 8001:8001 \
  -e KONG_DATABASE=off -e KONG_DECLARATIVE_CONFIG=/kong/kong.yaml \
  -v $PWD/gateway/kong.yaml:/kong/kong.yaml:ro kong:3.7
curl http://localhost:8000/health   # verificar
```

## Paso 9 — ALB
1. EC2 → Load Balancers → **Create** → Application Load Balancer (internet-facing), SG `sg-alb`.
2. **Target group** (Instances, puerto 8000, health check path `/health`) → registra la EC2 `kong`.
3. Listener HTTP :80 → reenvía al target group.
4. Anota el **DNS del ALB** (p. ej. `bite-alb-123.us-east-1.elb.amazonaws.com`).

## Paso 10 — Pruebas con JMeter
Desde tu máquina con `apache-jmeter-5.6.3`:

1. **Instala PyJWT** y **genera tokens** (modo local, igual que en local):
   ```bat
   pip install pyjwt
   cd sprint4\load-tests
   set AUTH_SECRET=dev-secret
   python gen_token.py NIT900000000 finanzas        REM TOKEN_VALIDO
   python gen_token.py NIT999999999 finanzas        REM TOKEN_OTRA_EMPRESA
   ```
2. **Latencia, seguridad y trade-off:** sigue `../load-tests/README.md` usando `-Jhost=<DNS_ALB> -Jport=80`.
3. **Pega los resultados** (Average ms, Error %, capturas del Summary Report) en `wiki/Sprint-4/Experimento-de-{Latencia|seguridad}/Implementación.md`.

## Checklist
- [ ] `curl http://<DNS_ALB>/health` responde `ok`.
- [ ] `GET /reportes` con token válido → 200 y < 1 s.
- [ ] `GET /reportes` sin token → 401; otra empresa → 403.
- [ ] `GET /reporte-oncall` responde (más lento) → comparación.
- [ ] Mongo tiene consolidados (entrar a la EC2 datos: `docker exec -it mongo mongosh -u monitoring_user -p isis2503 --authenticationDatabase admin`).

## Teardown
Termina las 5 EC2 y elimina el ALB y los SGs.
