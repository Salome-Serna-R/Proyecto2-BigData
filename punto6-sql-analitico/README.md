# Punto 6 - Consultas analíticas descriptivas con SQL

## Objetivo

Realizar consultas y procesamiento analítico descriptivo con SQL utilizando AWS Athena, EMR/Hive y SparkSQL.

Este punto consulta archivos limpios provenientes de la zona `trusted/` del proyecto para responder preguntas descriptivas sobre lugares de interés en Medellín.

## Herramientas

- AWS Athena
- EMR/Hive
- SparkSQL
- Amazon S3

## Estructura del directorio

```txt
punto6-sql-analitico/
  README.md
  athena/
    queries.sql
  emr-hive/
    hive_queries.sql
  sparksql/
    sparksql_queries.py
```

## Datos utilizados

Los datos base provienen de archivos CSV limpios:

```txt
places_clean.csv
place_types_clean.csv
place_hours_clean.csv
```

Para Athena se utiliza una copia de estos archivos en prefijos separados, porque cada tabla externa debe leer archivos con el mismo esquema desde una ubicación independiente.

Ubicaciones usadas en S3:

```txt
s3://proyecto2-bigdata-punto8/athena/places_clean/
s3://proyecto2-bigdata-punto8/athena/place_types_clean/
s3://proyecto2-bigdata-punto8/athena/place_hours_clean/
```

La ubicación de resultados de Athena se configuró en:

```txt
s3://proyecto2-bigdata-punto8/athena/results/
```

## Athena

El archivo:

```txt
athena/queries.sql
```

contiene:

1. Creación de la base de datos `proyecto2_bigdata`.
2. Creación de tablas externas sobre archivos CSV en S3.
3. Consultas descriptivas sobre barrios, tipos de lugar, horarios y niveles de precio.

Consultas realizadas:

- Barrios con mayor cantidad de lugares.
- Barrios con mejor rating promedio.
- Tipos de lugar más frecuentes.
- Tipos con mayor volumen de reseñas.
- Cobertura de apertura en fin de semana.
- Relación entre nivel de precio y rating promedio.

## EMR/Hive

La sección de EMR/Hive utiliza consultas SQL equivalentes sobre tablas externas disponibles desde el entorno Hive del cluster EMR.

El archivo esperado es:

```txt
emr-hive/hive_queries.sql
```

## SparkSQL

La sección de SparkSQL ejecuta consultas SQL usando una sesión Spark.

El archivo esperado es:

```txt
sparksql/sparksql_queries.py
```

## Evidencias sugeridas

Las evidencias del punto deben mostrar:

1. Datos en S3 organizados por tabla.
2. Configuración de ubicación de resultados en Athena.
3. Base de datos creada en Athena.
4. Tablas externas creadas.
5. Consulta de validación sobre `places_clean`.
6. Consultas analíticas ejecutadas en Athena.
7. Consultas equivalentes en EMR/Hive.
8. Consultas equivalentes en SparkSQL.

## Nota sobre datos definitivos

Si los archivos definitivos del pipeline conservan la misma estructura de columnas, basta con reemplazar los archivos en S3 y ejecutar nuevamente las consultas. Si cambian los nombres de columnas, se deben ajustar las definiciones de tabla y consultas SQL.