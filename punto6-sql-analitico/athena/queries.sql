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