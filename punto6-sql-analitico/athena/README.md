# Punto 6 - Consultas analíticas con AWS Athena

## Objetivo

Realizar consultas analíticas descriptivas con SQL usando AWS Athena sobre archivos CSV almacenados en Amazon S3.

Esta parte del punto 6 permite consultar los datos preparados del proyecto mediante tablas externas en Athena. Las tablas no copian los datos: únicamente definen el esquema y la ubicación de los archivos en S3 para poder ejecutar consultas SQL sobre ellos.

## Datos utilizados

Los archivos utilizados se encuentran en el bucket:

```txt
s3://proyecto2-bigdata-punto8/
```

Para Athena se organizaron copias de los CSV en prefijos separados, de forma que cada tabla externa lea únicamente archivos con el mismo esquema.

Ubicaciones usadas:

```txt
s3://proyecto2-bigdata-punto8/athena/places_clean/
s3://proyecto2-bigdata-punto8/athena/place_types_clean/
s3://proyecto2-bigdata-punto8/athena/place_hours_clean/
```

La ubicación de resultados de Athena se configuró en:

```txt
s3://proyecto2-bigdata-punto8/athena/results/
```

## Base de datos

Se creó la base de datos:

```sql
CREATE DATABASE IF NOT EXISTS proyecto2_bigdata;
```

Nombre de la base de datos:

```txt
proyecto2_bigdata
```

## Tablas externas creadas

Se crearon tres tablas externas:

| Tabla | Fuente S3 | Descripción |
|---|---|---|
| `places_clean` | `s3://proyecto2-bigdata-punto8/athena/places_clean/` | Lugares de interés con barrio, coordenadas, rating, nivel de precio y cantidad de reseñas. |
| `place_types_clean` | `s3://proyecto2-bigdata-punto8/athena/place_types_clean/` | Tipos o categorías asociadas a cada lugar. |
| `place_hours_clean` | `s3://proyecto2-bigdata-punto8/athena/place_hours_clean/` | Horarios de atención por lugar y día. |

Las tablas fueron definidas sobre archivos CSV usando `OpenCSVSerde` y omitiendo la primera línea de encabezados mediante:

```sql
TBLPROPERTIES ("skip.header.line.count"="1");
```

## Script SQL usado

El archivo principal de consultas se encuentra en:

```txt
athena/queries.sql
```

Contenido:

```sql
-- Punto 6 - Consultas analíticas con AWS Athena
-- Base de datos: proyecto2_bigdata
-- Bucket: s3://proyecto2-bigdata-punto8/

CREATE DATABASE IF NOT EXISTS proyecto2_bigdata;

CREATE EXTERNAL TABLE IF NOT EXISTS proyecto2_bigdata.places_clean (
  place_id string,
  name string,
  address string,
  neighborhood string,
  lat string,
  lng string,
  rating string,
  price_level string,
  review_count string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  "separatorChar" = ",",
  "quoteChar" = "\""
)
STORED AS TEXTFILE
LOCATION 's3://proyecto2-bigdata-punto8/athena/places_clean/'
TBLPROPERTIES ("skip.header.line.count"="1");

CREATE EXTERNAL TABLE IF NOT EXISTS proyecto2_bigdata.place_types_clean (
  place_id string,
  type string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  "separatorChar" = ",",
  "quoteChar" = "\""
)
STORED AS TEXTFILE
LOCATION 's3://proyecto2-bigdata-punto8/athena/place_types_clean/'
TBLPROPERTIES ("skip.header.line.count"="1");

CREATE EXTERNAL TABLE IF NOT EXISTS proyecto2_bigdata.place_hours_clean (
  place_id string,
  day_es string,
  day_en string,
  is_open string,
  open_time string,
  close_time string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  "separatorChar" = ",",
  "quoteChar" = "\""
)
STORED AS TEXTFILE
LOCATION 's3://proyecto2-bigdata-punto8/athena/place_hours_clean/'
TBLPROPERTIES ("skip.header.line.count"="1");

-- Validación de lectura
SELECT *
FROM proyecto2_bigdata.places_clean
LIMIT 10;

-- Consulta 1: barrios con mayor cantidad de lugares
SELECT
  neighborhood,
  COUNT(*) AS places_count,
  ROUND(AVG(TRY_CAST(rating AS DOUBLE)), 2) AS average_rating,
  SUM(TRY_CAST(review_count AS INTEGER)) AS total_reviews
FROM proyecto2_bigdata.places_clean
GROUP BY neighborhood
ORDER BY places_count DESC
LIMIT 10;

-- Consulta 2: barrios con mejor rating promedio
SELECT
  neighborhood,
  COUNT(*) AS places_count,
  ROUND(AVG(TRY_CAST(rating AS DOUBLE)), 2) AS average_rating
FROM proyecto2_bigdata.places_clean
WHERE TRY_CAST(rating AS DOUBLE) IS NOT NULL
GROUP BY neighborhood
HAVING COUNT(*) >= 3
ORDER BY average_rating DESC
LIMIT 10;

-- Consulta 3: tipos de lugar más frecuentes
SELECT
  t.type,
  COUNT(*) AS places_count,
  ROUND(AVG(TRY_CAST(p.rating AS DOUBLE)), 2) AS average_rating,
  SUM(TRY_CAST(p.review_count AS INTEGER)) AS total_reviews
FROM proyecto2_bigdata.places_clean p
JOIN proyecto2_bigdata.place_types_clean t
  ON p.place_id = t.place_id
GROUP BY t.type
ORDER BY places_count DESC
LIMIT 10;

-- Consulta 4: tipos de lugar con mayor volumen de reseñas
SELECT
  t.type,
  COUNT(*) AS places_count,
  SUM(TRY_CAST(p.review_count AS INTEGER)) AS total_reviews,
  ROUND(AVG(TRY_CAST(p.rating AS DOUBLE)), 2) AS average_rating
FROM proyecto2_bigdata.places_clean p
JOIN proyecto2_bigdata.place_types_clean t
  ON p.place_id = t.place_id
GROUP BY t.type
ORDER BY total_reviews DESC
LIMIT 10;

-- Consulta 5: cobertura de apertura en fin de semana
SELECT
  day_en,
  COUNT(DISTINCT place_id) AS open_places
FROM proyecto2_bigdata.place_hours_clean
WHERE LOWER(is_open) = 'true'
  AND day_en IN ('Saturday', 'Sunday')
GROUP BY day_en
ORDER BY open_places DESC;

-- Consulta 6: relación entre nivel de precio y rating
SELECT
  TRY_CAST(price_level AS INTEGER) AS price_level,
  COUNT(*) AS places_count,
  ROUND(AVG(TRY_CAST(rating AS DOUBLE)), 2) AS average_rating,
  SUM(TRY_CAST(review_count AS INTEGER)) AS total_reviews
FROM proyecto2_bigdata.places_clean
WHERE TRY_CAST(price_level AS INTEGER) > 0
GROUP BY TRY_CAST(price_level AS INTEGER)
ORDER BY price_level;
```

## Consultas realizadas

### Validación de lectura

```sql
SELECT *
FROM proyecto2_bigdata.places_clean
LIMIT 10;
```

Esta consulta valida que Athena puede leer correctamente los archivos CSV almacenados en S3.

### Consulta 1 - Barrios con mayor cantidad de lugares

```sql
SELECT
  neighborhood,
  COUNT(*) AS places_count,
  ROUND(AVG(TRY_CAST(rating AS DOUBLE)), 2) AS average_rating,
  SUM(TRY_CAST(review_count AS INTEGER)) AS total_reviews
FROM proyecto2_bigdata.places_clean
GROUP BY neighborhood
ORDER BY places_count DESC
LIMIT 10;
```

Permite identificar los barrios con mayor cantidad de lugares registrados, junto con su rating promedio y número total de reseñas.

### Consulta 2 - Barrios con mejor rating promedio

```sql
SELECT
  neighborhood,
  COUNT(*) AS places_count,
  ROUND(AVG(TRY_CAST(rating AS DOUBLE)), 2) AS average_rating
FROM proyecto2_bigdata.places_clean
WHERE TRY_CAST(rating AS DOUBLE) IS NOT NULL
GROUP BY neighborhood
HAVING COUNT(*) >= 3
ORDER BY average_rating DESC
LIMIT 10;
```

Permite comparar barrios por calificación promedio, considerando únicamente barrios con al menos tres lugares registrados.

### Consulta 3 - Tipos de lugar más frecuentes

```sql
SELECT
  t.type,
  COUNT(*) AS places_count,
  ROUND(AVG(TRY_CAST(p.rating AS DOUBLE)), 2) AS average_rating,
  SUM(TRY_CAST(p.review_count AS INTEGER)) AS total_reviews
FROM proyecto2_bigdata.places_clean p
JOIN proyecto2_bigdata.place_types_clean t
  ON p.place_id = t.place_id
GROUP BY t.type
ORDER BY places_count DESC
LIMIT 10;
```

Esta consulta usa un `JOIN` entre lugares y tipos para identificar las categorías de lugar más frecuentes.

### Consulta 4 - Tipos con mayor volumen de reseñas

```sql
SELECT
  t.type,
  COUNT(*) AS places_count,
  SUM(TRY_CAST(p.review_count AS INTEGER)) AS total_reviews,
  ROUND(AVG(TRY_CAST(p.rating AS DOUBLE)), 2) AS average_rating
FROM proyecto2_bigdata.places_clean p
JOIN proyecto2_bigdata.place_types_clean t
  ON p.place_id = t.place_id
GROUP BY t.type
ORDER BY total_reviews DESC
LIMIT 10;
```

Permite identificar qué tipos de lugar concentran mayor volumen de reseñas.

### Consulta 5 - Cobertura de apertura en fin de semana

```sql
SELECT
  day_en,
  COUNT(DISTINCT place_id) AS open_places
FROM proyecto2_bigdata.place_hours_clean
WHERE LOWER(is_open) = 'true'
  AND day_en IN ('Saturday', 'Sunday')
GROUP BY day_en
ORDER BY open_places DESC;
```

Permite contar cuántos lugares abren los días del fin de semana.

### Consulta 6 - Relación entre nivel de precio y rating

```sql
SELECT
  TRY_CAST(price_level AS INTEGER) AS price_level,
  COUNT(*) AS places_count,
  ROUND(AVG(TRY_CAST(rating AS DOUBLE)), 2) AS average_rating,
  SUM(TRY_CAST(review_count AS INTEGER)) AS total_reviews
FROM proyecto2_bigdata.places_clean
WHERE TRY_CAST(price_level AS INTEGER) > 0
GROUP BY TRY_CAST(price_level AS INTEGER)
ORDER BY price_level;
```

Permite analizar la relación entre el nivel de precio, la cantidad de lugares, el rating promedio y el total de reseñas.

## Resultado

Con Athena se logró consultar directamente información almacenada en S3 mediante SQL, creando tablas externas sobre archivos CSV. Las consultas permitieron realizar análisis descriptivo por barrio, categoría, horario de apertura y nivel de precio.

Esta sección cubre el uso de AWS Athena como motor SQL serverless dentro del punto 6 del proyecto.