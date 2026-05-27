# Punto 5 — Catalogación de Tablas SQL
## AWS Glue Data Catalog + Athena

Objetivo: Registrar las tablas Parquet de la zona trusted/ en el Glue Data Catalog para que sean consultables por nombre desde Athena y PySpark, sin necesidad de referenciar rutas S3 directamente.

## ¿Qué es el Glue Data Catalog?

Es un metastore centralizado compatible con Hive Metastore que almacena el esquema de cada tabla (nombres de columnas, tipos de datos), la ubicación de los datos en S3 y las particiones de cada tabla. Una vez registradas, las tablas son accesibles desde Athena, Glue Studio y PySpark con spark.table("medellin_trusted.places").

## Tablas catalogadas

| Tabla | Ubicación S3 | Partición | Filas |
|---|---|---|---|
| medellin_trusted.places | trusted/places/ | barrio | 969 |
| medellin_trusted.place_hours | trusted/place_hours/ | day_es | 5,885 |
| medellin_trusted.place_types | trusted/place_types/ | — | 1,457 |
| medellin_trusted.encuesta_cultura_ciudadana | trusted/encuesta_cultura_ciudadana/ | — | 1,029 |

## Prerrequisitos

- Punto 4 ejecutado: las carpetas trusted/ deben existir con archivos Parquet
- Acceso a AWS Glue
- Rol IAM: LabRole

## Paso 1 — Crear la base de datos en Glue Data Catalog

1. Ir a AWS Console -> AWS Glue -> Databases -> Add database
2. Configurar:

| Campo | Valor |
| Database name | medellin_trusted |
| Description | Tablas catalogadas de la zona trusted del Data Lake |
| Location | s3://proyecto2-bigdata-2026/trusted/ |

3. Click Create database

## Paso 2 — Crear el Crawler

1. Ir a AWS Glue -> Crawlers -> Create crawler

Pantalla 1 — Name:

| Campo | Valor |
| Crawler name | trusted-crawler |

Pantalla 2 — Data sources:

| Campo | Valor |
| Data source | S3 |
| Network connection | No connection required |
| S3 path | s3://proyecto2-bigdata-2026/trusted/ |
| Subsequent crawler runs | Crawl all sub-folders |

Click Add an S3 data source -> Click Next

Pantalla 3 — IAM Role:

| Campo | Valor |
| IAM role | Choose an existing IAM role |
| Role name | LabRole |

Click Next

Pantalla 4 — Output:

| Campo | Valor |
| Target database | medellin_trusted |
| Table name prefix | dejar vacío |
| Crawler schedule | On demand |

Click Next -> Create crawler

## Paso 3 — Ejecutar el Crawler

1. Seleccionar trusted-crawler -> Click Run
2. Esperar ~1–2 minutos hasta que el estado pase de Running a Ready
3. En la columna "Tables added" debe decir 4

## Paso 4 — Verificar las tablas en el Catálogo

1. Ir a AWS Glue -> Tables (panel izquierdo)
2. Filtrar por database: medellin_trusted
3. Deben aparecer exactamente estas 4 tablas:

| Tabla | Formato | Partición |
| places | Parquet | barrio |
| place_hours | Parquet | day_es |
| place_types | Parquet | — |
| encuesta_cultura_ciudadana | Parquet | — |

4. Entrar a cada tabla y verificar que el schema se detectó correctamente (columnas con tipos double, int, string, boolean)

## Paso 5 — Consultar con Athena

1. Ir a AWS Console -> Amazon Athena -> Iniciar editor de consultas
2. Configurar bucket de resultados: s3://proyecto2-bigdata-2026/athena-results/
3. Seleccionar Data source: AwsDataCatalog - Database: medellin_trusted

-- Conteo de registros por tabla
SELECT 'places'                     AS tabla, COUNT(*) AS total FROM places
UNION ALL
SELECT 'place_hours',                          COUNT(*) FROM place_hours
UNION ALL
SELECT 'place_types',                          COUNT(*) FROM place_types
UNION ALL
SELECT 'encuesta_cultura_ciudadana',           COUNT(*) FROM encuesta_cultura_ciudadana;
-- Resultados: 969 / 5885 / 1457 / 1029

-- Top 10 barrios con más lugares
SELECT barrio, COUNT(*) AS total
FROM places
WHERE rating > 0
GROUP BY barrio
ORDER BY total DESC
LIMIT 10;

-- Top 10 lugares mejor calificados abiertos el domingo
SELECT p.name, p.barrio, p.rating
FROM places p
JOIN place_hours h ON p.place_id = h.place_id
WHERE h.day_es = 'domingo' AND h.is_open = true
ORDER BY p.rating DESC
LIMIT 10;

-- Distribución de sensación de seguridad en Medellín
SELECT p_seg_es, COUNT(*) AS total
FROM encuesta_cultura_ciudadana
WHERE p_seg_es IS NOT NULL
GROUP BY p_seg_es
ORDER BY total DESC;
-- Permanece igual: 469 / Menos segura: 323 / Más segura: 237

## Estructura final del Glue Data Catalog

Glue Data Catalog
└── Database: medellin_trusted
    ├── Table: places
    │   ├── Columns: place_id, name, rating, total_ratings, price_level,
    │   │            latitude, longitude, ingestion_date
    │   └── Partition key: barrio
    ├── Table: place_hours
    │   ├── Columns: place_id, open_time, close_time, is_open, is_closed,
    │   │            ingestion_date
    │   └── Partition key: day_es
    ├── Table: place_types
    │   └── Columns: place_id, type, ingestion_date
    └── Table: encuesta_cultura_ciudadana
        └── Columns: idm, ciudad, fecha, sexo, annos, p_seg_cal,
                     p_seg_es, conf_per_gral, ingestion_date

## Posibles errores y soluciones

| Error | Causa | Solución |
| Crawler no encuentra datos | trusted/ está vacío | Ejecutar Punto 4 primero |
| Tables added: 0 | Ruta S3 incorrecta | Verificar que la ruta termina en trusted/ |
| Table not found en Athena | Particiones no cargadas | Ejecutar MSCK REPAIR TABLE medellin_trusted.places |
| Botón Ejecutar gris en Athena | Bucket de resultados no configurado | Configurar s3://proyecto2-bigdata-2026/athena-results/ en Settings |
