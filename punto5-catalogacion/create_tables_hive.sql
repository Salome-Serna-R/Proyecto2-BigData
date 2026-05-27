-- 0. BASE DE DATOS
CREATE DATABASE IF NOT EXISTS medellin_trusted
  COMMENT 'Tablas catalogadas de la zona trusted del Data Lake'
  LOCATION 's3://proyecto2-bigdata-2026/trusted/';

USE medellin_trusted;

-- 1. places  (particionada por barrio)
CREATE EXTERNAL TABLE IF NOT EXISTS medellin_trusted.places (
    place_id        STRING      COMMENT 'Identificador único del lugar (Google Places)',
    name            STRING      COMMENT 'Nombre del lugar (UTF-8 corregido)',
    rating          DOUBLE      COMMENT 'Calificación promedio (0-5). -1 si no disponible',
    total_ratings   INT         COMMENT 'Número total de reseñas. 0 si no disponible',
    price_level     INT         COMMENT 'Nivel de precio (1-4)',
    latitude        DOUBLE      COMMENT 'Latitud WGS-84 (filtrado: 6.1-6.4)',
    longitude       DOUBLE      COMMENT 'Longitud WGS-84 (filtrado: -75.7 a -75.4)',
    ingestion_date  TIMESTAMP   COMMENT 'Timestamp de carga a trusted'
)
PARTITIONED BY (barrio STRING COMMENT 'Barrio de Medellín (initcap, "Desconocido" si nulo)')
STORED AS PARQUET
LOCATION 's3://proyecto2-bigdata-2026/trusted/places/'
TBLPROPERTIES (
    'parquet.compress'           = 'SNAPPY',
    'has_encrypted_data'         = 'false',
    'classification'             = 'parquet'
);

MSCK REPAIR TABLE medellin_trusted.places;

-- 2. place_hours  (particionada por day_es)
CREATE EXTERNAL TABLE IF NOT EXISTS medellin_trusted.place_hours (
    place_id        STRING      COMMENT 'FK → places.place_id',
    open_time       STRING      COMMENT 'Hora de apertura (HH:mm)',
    close_time      STRING      COMMENT 'Hora de cierre (HH:mm)',
    is_open         BOOLEAN     COMMENT 'true si el lugar abre ese día',
    is_closed       BOOLEAN     COMMENT 'true si el lugar cierra ese día (inverso de is_open)',
    ingestion_date  TIMESTAMP   COMMENT 'Timestamp de carga a trusted'
)
PARTITIONED BY (day_es STRING COMMENT 'Día en español minúsculas: lunes…domingo')
STORED AS PARQUET
LOCATION 's3://proyecto2-bigdata-2026/trusted/place_hours/'
TBLPROPERTIES (
    'parquet.compress'   = 'SNAPPY',
    'has_encrypted_data' = 'false',
    'classification'     = 'parquet'
);

MSCK REPAIR TABLE medellin_trusted.place_hours;

-- 3. place_types  (sin partición)
CREATE EXTERNAL TABLE IF NOT EXISTS medellin_trusted.place_types (
    place_id        STRING      COMMENT 'FK → places.place_id',
    type            STRING      COMMENT 'Categoría Google Places (restaurant, cafe, bar, etc.)',
    ingestion_date  TIMESTAMP   COMMENT 'Timestamp de carga a trusted'
)
STORED AS PARQUET
LOCATION 's3://proyecto2-bigdata-2026/trusted/place_types/'
TBLPROPERTIES (
    'parquet.compress'   = 'SNAPPY',
    'has_encrypted_data' = 'false',
    'classification'     = 'parquet'
);

-- 4. encuesta_cultura_ciudadana  (sin partición)
CREATE EXTERNAL TABLE IF NOT EXISTS medellin_trusted.encuesta_cultura_ciudadana (
    idm             INT         COMMENT 'Código de barrio/sector de la encuesta',
    ciudad          STRING      COMMENT 'Ciudad (filtrado: solo Medellín)',
    fecha           STRING      COMMENT 'Fecha de la encuesta (YYYY-MM-DD)',
    sexo            STRING      COMMENT 'Sexo del encuestado',
    annos           INT         COMMENT 'Edad del encuestado',
    p_seg_cal       STRING      COMMENT 'Percepción de seguridad en barrio: Más/Menos/Igual segura',
    p_seg_es        STRING      COMMENT 'Sensación de seguridad personal',
    conf_per_gral   STRING      COMMENT 'Confianza general en las personas',
    ingestion_date  TIMESTAMP   COMMENT 'Timestamp de carga a trusted'
)
STORED AS PARQUET
LOCATION 's3://proyecto2-bigdata-2026/trusted/encuesta_cultura_ciudadana/'
TBLPROPERTIES (
    'parquet.compress'   = 'SNAPPY',
    'has_encrypted_data' = 'false',
    'classification'     = 'parquet'
);

-- VERIFICACIÓN
-- 1. Listar base de datos y tablas
SHOW DATABASES LIKE 'medellin_trusted';
USE medellin_trusted;
SHOW TABLES;

-- 2. Inspeccionar esquemas (confirmar columnas y tipos)
DESCRIBE FORMATTED medellin_trusted.places;
DESCRIBE FORMATTED medellin_trusted.place_hours;
DESCRIBE FORMATTED medellin_trusted.place_types;
DESCRIBE FORMATTED medellin_trusted.encuesta_cultura_ciudadana;

-- 3. Verificar particiones detectadas
SHOW PARTITIONS medellin_trusted.places;
SHOW PARTITIONS medellin_trusted.place_hours;

-- 4. Conteo de registros por tabla
SELECT 'places'                     AS tabla, COUNT(*) AS total FROM medellin_trusted.places
UNION ALL
SELECT 'place_hours',                          COUNT(*) FROM medellin_trusted.place_hours
UNION ALL
SELECT 'place_types',                          COUNT(*) FROM medellin_trusted.place_types
UNION ALL
SELECT 'encuesta_cultura_ciudadana',           COUNT(*) FROM medellin_trusted.encuesta_cultura_ciudadana;

-- QUERIES ANALÍTICAS
-- Q1: Top 10 barrios con más lugares y su rating promedio
SELECT
    barrio,
    COUNT(*)                    AS n_lugares,
    ROUND(AVG(rating), 2)       AS rating_promedio,
    SUM(total_ratings)          AS total_resenas
FROM medellin_trusted.places
WHERE rating > 0
GROUP BY barrio
ORDER BY n_lugares DESC
LIMIT 10;

-- Q2: Categorías más frecuentes
SELECT
    type,
    COUNT(*) AS n_lugares
FROM medellin_trusted.place_types
GROUP BY type
ORDER BY n_lugares DESC
LIMIT 10;

-- Q3: Lugares abiertos los fines de semana (sábado o domingo)
SELECT COUNT(DISTINCT place_id) AS lugares_abiertos_finde
FROM medellin_trusted.place_hours
WHERE day_es IN ('sábado', 'domingo')
  AND is_open = true;

-- Q4: Top 10 lugares mejor calificados que abren el domingo
SELECT
    p.name,
    p.barrio,
    p.rating,
    p.total_ratings
FROM medellin_trusted.places  p
JOIN medellin_trusted.place_hours h
  ON p.place_id = h.place_id
WHERE h.day_es = 'domingo'
  AND h.is_open = true
  AND p.rating > 0
ORDER BY p.rating DESC, p.total_ratings DESC
LIMIT 10;

-- Q5: Barrios con mejor rating por categoría (TOP 1 por tipo)
SELECT type, barrio, avg_rating, n_lugares
FROM (
    SELECT
        t.type,
        p.barrio,
        ROUND(AVG(p.rating), 2)  AS avg_rating,
        COUNT(*)                 AS n_lugares,
        ROW_NUMBER() OVER (PARTITION BY t.type ORDER BY AVG(p.rating) DESC) AS rn
    FROM medellin_trusted.places     p
    JOIN medellin_trusted.place_types t ON p.place_id = t.place_id
    WHERE p.rating > 0
    GROUP BY t.type, p.barrio
    HAVING COUNT(*) >= 3
) ranked
WHERE rn = 1
ORDER BY type;

-- Q6: Distribución de sensación de seguridad en Medellín
SELECT
    p_seg_es,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
FROM medellin_trusted.encuesta_cultura_ciudadana
WHERE p_seg_es IS NOT NULL
GROUP BY p_seg_es
ORDER BY total DESC;

-- Q7: Pregunta central — rating y oferta de lugares vs percepción de seguridad por barrio
SELECT
    p.barrio,
    COUNT(DISTINCT p.place_id)          AS n_lugares,
    ROUND(AVG(p.rating), 2)             AS rating_promedio,
    e.p_seg_es                          AS sensacion_seguridad_mayoritaria,
    COUNT(e.idm)                        AS n_encuestados
FROM medellin_trusted.places          p
JOIN medellin_trusted.encuesta_cultura_ciudadana e
  ON LOWER(p.barrio) = LOWER(e.ciudad)   -- placeholder: ajustar con tabla de mapeo idm→barrio
WHERE p.rating > 0
GROUP BY p.barrio, e.p_seg_es
ORDER BY n_lugares DESC
LIMIT 20;