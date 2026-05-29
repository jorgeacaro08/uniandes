# Seed de datos (volumen consecuente con el crecimiento del negocio)

Dos bases de datos pobladas:

## 1. Empresas (PostgreSQL — ms-autenticacion)
```bash
cd ms-autenticacion
python manage.py seed_empresas --empresas 500
```

## 2a. Flujo realista: crudos en Postgres → consolidado en Mongo (ms-alertas)
Refleja la arquitectura real (CQRS: escritura cruda + precálculo materializado).
```bash
cd ms-alertas
python manage.py seed_crudos --empresas 50 --meses 24   # ~324k filas crudas (suba --empresas para ~1-2M)
python manage.py consolidar                              # materializa ~empresas x meses docs en Mongo
```

## 2b. Flujo rápido: consolidados directos en Mongo (solo lectura)
Para la prueba de latencia cuando no se necesita el detalle crudo.
```bash
cd seed
python seed_mongo.py --empresas 500 --meses 24           # 12.000 documentos consolidados
```

**Dimensionamiento:** el negocio espera 5.000–12.000 usuarios concurrentes y
+15% de empresas/año. Por defecto: 500 empresas × 24 meses = 12.000 reportes
consolidados (lectura) y cientos de miles–millones de registros crudos (fuente).
