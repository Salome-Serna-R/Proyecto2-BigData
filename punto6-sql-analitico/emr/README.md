# Punto 6 - Consultas analíticas descriptivas con SQL usando EMR/Hive y SparkSQL

## Objetivo

Realizar consultas y procesamiento analítico descriptivo con SQL utilizando Amazon EMR, Hive y SparkSQL sobre datos almacenados en Amazon S3.

Para este punto se utilizó una estructura de datos en formato Parquet ubicada en S3, equivalente a una zona `trusted/` generada por el procesamiento previo del proyecto. Las consultas no copian los datos al clúster; Hive y SparkSQL leen directamente los archivos Parquet desde S3.

## Datos utilizados

Los datos consultados se encuentran en:

```txt
s3://proyecto2-bigdata-punto8/trusted_mock_parquet/
```

Estructura de datos:

```txt
trusted_mock_parquet/
  places/
    barrio=.../
      part-00000.parquet

  place_hours/
    day_es=.../
      part-00000.parquet

  place_types/
    part-00000.parquet

  encuesta_cultura_ciudadana/
    part-00000.parquet
```

Distribución de tablas:

| Tabla | Ubicación en S3 | Partición |
|---|---|---|
| `places` | `trusted_mock_parquet/places/` | `barrio` |
| `place_hours` | `trusted_mock_parquet/place_hours/` | `day_es` |
| `place_types` | `trusted_mock_parquet/place_types/` | Sin partición |
| `encuesta_cultura_ciudadana` | `trusted_mock_parquet/encuesta_cultura_ciudadana/` | Sin partición |

Las tablas `places` y `place_hours` se encuentran particionadas para representar una salida típica de Spark/Glue en la zona trusted.

## Configuración del clúster EMR

Se creó un clúster Amazon EMR en EC2 siguiendo la guía trabajada en clase.

Configuración usada:

| Campo | Valor |
|---|---|
| Nombre del clúster | `proyecto2-punto6-emr-sql` |
| Versión de Amazon EMR | `emr-7.13.0` |
| Tipo de instancia | `m5.xlarge` |
| Nodo principal | 1 instancia |
| Nodos centrales | 2 instancias |
| Nodo de tarea | 1 instancia |

## Aplicaciones instaladas

Durante la creación del clúster se seleccionaron las siguientes aplicaciones:

- Hadoop 3.4.2
- Hive 3.1.3
- Spark 3.5.6
- Hue 4.11.0
- HCatalog 3.1.3

También se habilitó el uso del catálogo para metadatos de tablas de Hive y Spark.

## Seguridad, roles y acceso

Configuración usada:

| Configuración | Valor |
|---|---|
| Par de claves EC2 | `vockey` |
| Rol de servicio de Amazon EMR | `EMR_DefaultRole` |
| Perfil de instancia EC2 para Amazon EMR | `EMR_EC2_DefaultRole` |

Durante la configuración del clúster se usaron roles propios de EMR, ya que el perfil `LabRole` no era válido como instance profile para este flujo.

## Terminación del clúster

La opción configurada fue:

```txt
Terminar manualmente el clúster
```

También quedó activado el reemplazo de nodos en mal estado.

Al finalizar las pruebas se terminó manualmente el clúster desde la consola de EMR para evitar consumo adicional del presupuesto de AWS Academy.

## Configuración de red

Después de crear el clúster se configuraron excepciones de puertos en la sección de bloqueo de acceso público de EMR.

Puertos utilizados:

| Puerto | Uso |
|---|---|
| 22 | Acceso SSH al nodo principal |
| 8888 | Acceso a Hue |
| 9443 | Acceso a JupyterHub según la guía de clase |

Luego se ingresó al grupo de seguridad administrado por EMR para el nodo principal y se agregaron reglas de entrada TCP para los puertos anteriores.

## Acceso a Hue

Desde la pestaña `Aplicaciones` del clúster EMR se identificó la URL de Hue en el puerto `8888`.

Ejemplo:

```txt
http://ec2-3-92-185-47.compute-1.amazonaws.com:8888/
```

En el primer ingreso a Hue se creó una cuenta de administrador. Posteriormente se usó el editor de Hive para ejecutar consultas SQL.

Para usar Hive en Hue se accedió al editor correspondiente:

```txt
/hue/editor/?type=hive
```

## Consultas con EMR/Hive

Las tablas fueron creadas como tablas externas. Esto significa que Hive registra el esquema y la ubicación de los datos, pero los archivos permanecen en S3.

### Creación de base de datos y tablas externas

```sql
CREATE DATABASE IF NOT EXISTS medellin_trusted_demo;

USE medellin_trusted_demo;

CREATE EXTERNAL TABLE IF NOT EXISTS places (
    place_id        STRING,
    name            STRING,
    rating          DOUBLE,
    total_ratings   INT,
    price_level     INT,
    latitude        DOUBLE,
    longitude       DOUBLE,
    ingestion_date  TIMESTAMP
)
PARTITIONED BY (barrio STRING)
STORED AS PARQUET
LOCATION 's3://proyecto2-bigdata-punto8/trusted_mock_parquet/places/';

MSCK REPAIR TABLE places;

CREATE EXTERNAL TABLE IF NOT EXISTS place_hours (
    place_id        STRING,
    open_time       STRING,
    close_time      STRING,
    is_open         BOOLEAN,
    is_closed       BOOLEAN,
    ingestion_date  TIMESTAMP
)
PARTITIONED BY (day_es STRING)
STORED AS PARQUET
LOCATION 's3://proyecto2-bigdata-punto8/trusted_mock_parquet/place_hours/';

MSCK REPAIR TABLE place_hours;

CREATE EXTERNAL TABLE IF NOT EXISTS place_types (
    place_id        STRING,
    type            STRING,
    ingestion_date  TIMESTAMP
)
STORED AS PARQUET
LOCATION 's3://proyecto2-bigdata-punto8/trusted_mock_parquet/place_types/';

CREATE EXTERNAL TABLE IF NOT EXISTS encuesta_cultura_ciudadana (
    idm             INT,
    ciudad          STRING,
    fecha           STRING,
    sexo            STRING,
    annos           INT,
    p_seg_cal       STRING,
    p_seg_es        STRING,
    conf_per_gral   STRING,
    ingestion_date  TIMESTAMP
)
STORED AS PARQUET
LOCATION 's3://proyecto2-bigdata-punto8/trusted_mock_parquet/encuesta_cultura_ciudadana/';

SELECT current_database();

SHOW TABLES;
```

`MSCK REPAIR TABLE` se ejecutó sobre las tablas particionadas para que Hive detectara las particiones físicas presentes en S3, como `barrio=...` y `day_es=...`.

### Consulta Hive 1 - Barrios con más lugares

```sql
USE medellin_trusted_demo;

SELECT
    barrio,
    COUNT(*) AS n_lugares,
    ROUND(AVG(rating), 2) AS rating_promedio,
    SUM(total_ratings) AS total_resenas
FROM places
WHERE rating > 0
GROUP BY barrio
ORDER BY n_lugares DESC
LIMIT 10;
```

Esta consulta obtiene los barrios con mayor cantidad de lugares registrados, su rating promedio y el total de reseñas.

### Consulta Hive 2 - Lugares mejor calificados abiertos el domingo

```sql
USE medellin_trusted_demo;

SELECT
    p.name,
    p.barrio,
    p.rating,
    p.total_ratings
FROM places p
JOIN place_hours h
  ON p.place_id = h.place_id
WHERE h.day_es = 'domingo'
  AND h.is_open = true
  AND p.rating > 0
ORDER BY p.rating DESC, p.total_ratings DESC
LIMIT 10;
```

Esta consulta realiza un `JOIN` entre lugares y horarios para identificar lugares abiertos el domingo, ordenados por calificación y número de reseñas.

## Consultas con SparkSQL

Para ejecutar SparkSQL se accedió al nodo principal del clúster mediante SSH y se inició PySpark:

```bash
pyspark
```

Luego se leyeron los mismos archivos Parquet desde S3 y se crearon vistas temporales.

```python
places = spark.read.parquet("s3://proyecto2-bigdata-punto8/trusted_mock_parquet/places/")
place_hours = spark.read.parquet("s3://proyecto2-bigdata-punto8/trusted_mock_parquet/place_hours/")
place_types = spark.read.parquet("s3://proyecto2-bigdata-punto8/trusted_mock_parquet/place_types/")
encuesta = spark.read.parquet("s3://proyecto2-bigdata-punto8/trusted_mock_parquet/encuesta_cultura_ciudadana/")

places.createOrReplaceTempView("places")
place_hours.createOrReplaceTempView("place_hours")
place_types.createOrReplaceTempView("place_types")
encuesta.createOrReplaceTempView("encuesta_cultura_ciudadana")
```

### Consulta SparkSQL 1 - Barrios con más lugares

```python
spark.sql("""
SELECT
    barrio,
    COUNT(*) AS n_lugares,
    ROUND(AVG(rating), 2) AS rating_promedio,
    SUM(total_ratings) AS total_resenas
FROM places
WHERE rating > 0
GROUP BY barrio
ORDER BY n_lugares DESC
LIMIT 10
""").show(truncate=False)
```

### Consulta SparkSQL 2 - Tipos de lugar más frecuentes

```python
spark.sql("""
SELECT
    t.type,
    COUNT(*) AS n_lugares,
    ROUND(AVG(p.rating), 2) AS rating_promedio,
    SUM(p.total_ratings) AS total_resenas
FROM places p
JOIN place_types t
  ON p.place_id = t.place_id
WHERE p.rating > 0
GROUP BY t.type
ORDER BY n_lugares DESC
LIMIT 10
""").show(truncate=False)
```

## Resultado

El punto permitió validar consultas SQL descriptivas sobre datos Parquet almacenados en S3 usando dos mecanismos dentro del ecosistema EMR:

1. **Hive desde Hue**, mediante tablas externas sobre S3.
2. **SparkSQL desde PySpark**, leyendo directamente los Parquet desde S3 y consultando vistas temporales.

Con esto se cumple el uso de EMR/Hive y SparkSQL para procesamiento analítico descriptivo sobre la zona trusted del Data Lake.

## Consideraciones finales

- Las tablas creadas en Hive son externas; por lo tanto, eliminarlas no borra los datos en S3.
- Las particiones de `places` y `place_hours` se cargan con `MSCK REPAIR TABLE`.
- SparkSQL consulta los mismos datos usando `spark.read.parquet()` y vistas temporales.
- El clúster EMR debe terminarse manualmente al finalizar las pruebas para evitar consumo adicional.