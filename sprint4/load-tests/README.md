# Pruebas de carga (JMeter 5.6.3)

Planes parametrizables por `-J`. Apuntan al **gateway Kong** (puerto 8000), no a los servicios directamente.

> Atajo: `set JMETER=...\apache-jmeter-5.6.3\bin\jmeter.bat` (Windows).

## 0. Prerrequisitos
1. Servicios arriba (`docker compose up -d --build`) y datos sembrados (ver `../seed/README.md`).
2. PyJWT instalado: `pip install pyjwt`.
3. Generar tokens (modo local HS256; el secreto debe coincidir con `AUTH_SECRET`):
   ```bat
   set AUTH_SECRET=dev-secret
   python gen_token.py NIT900000000 finanzas   REM TOKEN VALIDO de la empresa
   python gen_token.py NIT999999999 finanzas   REM TOKEN de OTRA empresa
   ```

## 1. Latencia (ASR ≤ 1000 ms)
Escenario normal (150 hilos, ramp-up 10 s) contra la lectura precalculada `/reportes`:
```bat
%JMETER% -n -t latencia.jmx -Jhost=localhost -Jport=8000 -Jthreads=150 -Jrampup=10 -Jloops=10 ^
  -Jempresa=NIT900000000 -Jperiodo=2025-01 -Jtoken=<TOKEN_VALIDO> ^
  -l results\lat_normal.jtl -e -o results\lat_normal_report
```
Sobrecarga (300 hilos): repetir con `-Jthreads=300`.

**Comparación con el anti-patrón** (agrega crudos en caliente, como Sprint 3):
```bat
%JMETER% -n -t latencia.jmx -Jpath=/reporte-oncall -Jthreads=150 -Jrampup=10 -Jloops=10 ^
  -Jempresa=NIT900000000 -Jperiodo=2025-01 -Jtoken=<TOKEN_VALIDO> ^
  -l results\lat_oncall.jtl -e -o results\lat_oncall_report
```
Métricas (Summary Report): **Average** (ms) y **Error %**. Se espera Average ≤ 1000 ms y Error 0% en `/reportes`, y un Average mayor en `/reporte-oncall`.

## 2. Seguridad (5 min: 100% no autorizadas bloqueadas, ≥99% válidas OK)
```bat
%JMETER% -n -t seguridad.jmx -Jhost=localhost -Jport=8000 -Jduration=300 -Jsecthreads=10 ^
  -Jempresa=NIT900000000 -Jperiodo=2025-01 ^
  -Jtoken_valid=<TOKEN_VALIDO> -Jtoken_other=<TOKEN_OTRA_EMPRESA> ^
  -l results\seg.jtl -e -o results\seg_report
```
Cada grupo asevera su código esperado (401 / 401 / 403 / 200). En el Summary, **Error % ≈ 0** en los 4 grupos = ASR cumplido.

## 3. Trade-off latencia con/sin seguridad
1. **CON seguridad** (`AUTH_ENABLED=true` por defecto): correr el test de latencia (sección 1) con `-Jtoken=<VALIDO>`. Guardar Average.
2. **SIN seguridad**: editar `docker-compose.yml` → `AUTH_ENABLED: "false"` en `ms-reportes`; luego:
   ```bash
   docker compose up -d --build ms-reportes
   ```
   Correr el mismo test sin token (`-Jtoken=`). Guardar Average.
3. Comparar el sobrecosto (Δ ms) que introduce la validación del JWT y documentarlo en la wiki.
