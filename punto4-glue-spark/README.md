# Punto 4 — Preparación de Datos: RAW -> TRUSTED
## AWS Glue + Apache Spark (PySpark)

Objetivo: Limpiar, transformar y normalizar los datos crudos de la zona raw/ y escribirlos
en formato Parquet en la zona trusted/, listos para análisis.

## Arquitectura

S3: raw/rds/places.csv                ─┐
S3: raw/files/place_hours.csv          ├──► AWS Glue Job (PySpark) ──► S3: trusted/
S3: raw/files/place_types.csv          │
S3: raw/url/encuesta_cultura_2019.csv ─┘

## Tablas procesadas

| Tabla entrada (raw)             | Tabla salida (trusted)          | Partición  |
|---------------------------------|---------------------------------|------------|
| raw/rds/places.csv              | trusted/places/                 | barrio     |
| raw/files/place_hours.csv       | trusted/place_hours/            | day_es     |
| raw/files/place_types.csv       | trusted/place_types/            | —          |
| raw/url/encuesta_cultura_2019   | trusted/encuesta_cultura_ciudadana/ | —      |

## Transformaciones aplicadas

### places
- Renombrado: neighborhood -> barrio, lat -> latitude, lng -> longitude, review_count -> total_ratings
- Cast: rating y coordenadas a Double, total_ratings y price_level a Integer
- trim() en name, initcap() en barrio para normalizar mayúsculas
- Nulos en rating reemplazados por -1.0, nulos en barrio por "Desconocido"
- Filtro geográfico: solo coordenadas dentro del bounding box de Medellín
  (lat 6.15–6.40, lon -75.65–-75.50)
- Deduplicación por place_id

### place_hours
- Días normalizados a minúscula con lower()
- is_open casteado a Boolean real
- is_closed derivado: si is_open = False entonces is_closed = True
- Columnas day_en y raw descartadas por no aportar al análisis
- Deduplicación por (place_id, day_es)

### place_types
- type normalizado a minúscula con lower()
- Filtro: solo categorías conocidas del catálogo de Google Maps
- Deduplicación por (place_id, type)

### encuesta_cultura_ciudadana
- Solo se seleccionan 8 columnas relevantes de las ~250 del CSV original:
  idm, ciudad, fecha, sexo, annos, p_seg_cal, p_seg_es, conf_per_gral
- trim() en columnas de texto
- annos e idm casteados a Integer
- Filtro: solo registros de Medellín con idm válido
- Sin partición: dataset pequeño, no justifica overhead

## Pasos para reproducir

## Prerrequisitos

- Cuenta AWS Academy activa con acceso a S3, Glue, IAM
- Punto 3 ejecutado: los 4 archivos deben estar en raw/
- Rol IAM con permisos: LabRole + AmazonS3FullAccess

## Paso 1 — Subir el script a S3

aws s3 cp glue_job_raw_to_trusted.py s3://proyecto2-bigdata-2026/scripts/glue_job_raw_to_trusted.py

Verificar que subió:
aws s3 ls s3://proyecto2-bigdata-2026/scripts/

## Paso 2 — Crear el Glue Job

1. Ir a AWS Console -> AWS Glue -> ETL Jobs -> Create job
2. Seleccionar "Script editor" -> "Upload script"
3. Subir el archivo glue_job_raw_to_trusted.py
4. Configurar:

| Parámetro        | Valor                                                        |
|------------------|--------------------------------------------------------------|
| Job name         | raw-to-trusted-medellin                                      |
| IAM Role         | AWSGlueServiceRole                                           |
| Glue version     | Glue 4.0 (Spark 3.3)                                         |
| Worker type      | G.1X                                                         |
| Number of workers| 2                                                            |
| Job bookmark     | Disabled                                                     |
| Script path      | s3://proyecto2-bigdata-2026/scripts/glue_job_raw_to_trusted.py    |
| Temporary dir    | s3://proyecto2-bigdata-2026/tmp/                                  |

5. Click "Save" -> "Run"

## Paso 3 — Verificar la ejecución

En la consola Glue:
- Ir a Glue -> Jobs -> raw-to-trusted-medellin -> Runs
- El estado debe cambiar de Running -> Succeeded (tarda ~3–5 min)
- Si falla: ir a "Logs" -> CloudWatch para ver el error

Verificar archivos en S3:
aws s3 ls s3://proyecto2-bigdata-2026/trusted/
aws s3 ls s3://proyecto2-bigdata-2026/trusted/places/ --recursive

Deberías ver:
trusted/places/barrio=El Poblado/part-00000-xxxx.parquet
trusted/places/barrio=Laureles/part-00000-xxxx.parquet
trusted/place_hours/day_es=lunes/part-00000-xxxx.parquet
trusted/place_types/part-00000-xxxx.parquet
trusted/encuesta_cultura_ciudadana/part-00000-xxxx.parquet

## Paso 4 — Validación rápida en Athena

Una vez catalogadas las tablas en el Punto 5, validar con:

SELECT COUNT(*) FROM medellin_trusted.places;           
SELECT COUNT(*) FROM medellin_trusted.place_hours;      
SELECT COUNT(*) FROM medellin_trusted.place_types;      
SELECT COUNT(*) FROM medellin_trusted.encuesta_cultura_ciudadana; 

SELECT MIN(latitude), MAX(latitude), MIN(longitude), MAX(longitude)
FROM medellin_trusted.places;
-- Esperado: lat entre 6.15 y 6.40, lon entre -75.65 y -75.50

## Posibles errores y soluciones

| Error                              | Causa probable                        | Solución                                      |
|------------------------------------|---------------------------------------|-----------------------------------------------|
| Path does not exist                | CSV no ingestado                      | Ejecutar Punto 3 primero                      |
| Access Denied on S3                | Rol IAM sin permisos                  | Agregar AmazonS3FullAccess al rol de Glue     |
| Job en estado Failed sin logs      | Falta directorio tmp/                 | Crear s3://proyecto2-bigdata-2026/tmp/ manualmente |
| Columnas con todos nulls           | Nombre de columna incorrecto en el CSV| Verificar con df.printSchema() en los logs    |

## Evidencias a incluir en el informe

1. Glue Job creado — vista de la consola con el job listado
2. Ejecución exitosa — Run con estado Succeeded y tiempo de ejecución
3. Logs de CloudWatch — líneas [OK] para cada tabla
4. S3 trusted/ — carpetas creadas con archivos .parquet
5. Athena COUNT(*) — resultados de las consultas de validación