import sys
import csv as py_csv
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, IntegerType, BooleanType,
    StringType, StructType, StructField
)
import logging

# INICIALIZACIÓN
args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET    = "s3://proyecto2-bigdata-2026"
RAW_RDS   = f"{BUCKET}/raw/rds/"
RAW_FILES = f"{BUCKET}/raw/files/"
RAW_URL   = f"{BUCKET}/raw/url/"
TRUSTED   = f"{BUCKET}/trusted/"

# HELPERS 
def read_csv(path, sep=",", encoding="UTF-8"):
    logger.info(f"[READ] {path}")
    return (
        spark.read
             .option("header", "true")
             .option("inferSchema", "true")
             .option("sep", sep)
             .option("encoding", encoding)
             .csv(path)
    )

def write_trusted(df, table_name, partition_col=None):
    out_path = f"{TRUSTED}{table_name}/"
    logger.info(f"[WRITE] {out_path} filas={df.count()} cols={len(df.columns)}")
    writer = df.write.mode("overwrite").format("parquet")
    if partition_col:
        writer = writer.partitionBy(partition_col)
    writer.save(out_path)
    logger.info(f"[OK] {table_name} guardado en trusted.")

# UDF para reparar el doble-encoding, e.g. "MedellÃ­n" → "Medellín", "miÃ©rcoles" → "miércoles"
def _fix_enc(s):
    if s is None:
        return None
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s

fix_enc = F.udf(_fix_enc, StringType())

# TABLA 1: places — Lugares de interés
# Columnas desde RDS: place_id, name, neighborhood, lat, lng, rating, price_level, review_count
logger.info("=== PROCESANDO: places ===")

PLACES_SCHEMA = StructType([
    StructField("place_id",     StringType(),  True),
    StructField("name",         StringType(),  True),
    StructField("address",      StringType(),  True),
    StructField("neighborhood", StringType(),  True),
    StructField("lat",          StringType(),  True),  # se castea luego
    StructField("lng",          StringType(),  True),
    StructField("rating",       StringType(),  True),
    StructField("price_level",  StringType(),  True),
    StructField("review_count", StringType(),  True),
])

def parse_places_row(line):
    if not line:
        return None
    # Quitar comillas externas (el wrapping que genera el problema)
    if line.startswith('"') and line.endswith('"'):
        inner = line[1:-1]
    else:
        inner = line
    try:
        parts = next(py_csv.reader([inner]))
    except Exception:
        return None
    if len(parts) < 9:
        return None
    # Los últimos 5 campos son siempre numéricos/fijos: review_count, price_level, rating, lng, lat (en ese orden desde el final)
    review_count = parts[-1].strip()
    price_level  = parts[-2].strip()
    rating       = parts[-3].strip()
    lng          = parts[-4].strip()
    lat          = parts[-5].strip()
    neighborhood = parts[-6].strip()
    place_id     = parts[0].strip()
    name         = parts[1].strip()
    address      = ",".join(parts[2:-6]).strip()
    return (place_id, name, address, neighborhood, lat, lng, rating, price_level, review_count)

parse_places_udf = F.udf(
    parse_places_row,
    StructType([
        StructField("place_id",     StringType(), True),
        StructField("name",         StringType(), True),
        StructField("address",      StringType(), True),
        StructField("neighborhood", StringType(), True),
        StructField("lat",          StringType(), True),
        StructField("lng",          StringType(), True),
        StructField("rating",       StringType(), True),
        StructField("price_level",  StringType(), True),
        StructField("review_count", StringType(), True),
    ])
)

# Leer como texto (skip header)
df_places_raw = (
    spark.read
         .option("encoding", "UTF-8")
         .text(f"{RAW_RDS}places.csv")
         .filter(F.col("value").isNotNull() & (F.col("value") != ""))
         # quitar BOM si quedó en la primera línea
         .withColumn("value", F.regexp_replace(F.col("value"), "^\ufeff", ""))
         # filtrar la cabecera
         .filter(~F.col("value").startswith("place_id,"))
)

df_places_parsed = df_places_raw.withColumn("parsed", parse_places_udf(F.col("value")))

df_places = (
    df_places_parsed
    .filter(F.col("parsed").isNotNull())
    .select(
        F.col("parsed.place_id"),
        F.col("parsed.name"),
        F.col("parsed.address"),
        F.col("parsed.neighborhood").alias("barrio"),
        F.col("parsed.lat").alias("latitude"),
        F.col("parsed.lng").alias("longitude"),
        F.col("parsed.rating"),
        F.col("parsed.price_level"),
        F.col("parsed.review_count").alias("total_ratings"),
    )
    # Reparar doble-encoding en campos de texto
    .withColumn("name",   fix_enc(F.trim(F.col("name"))))
    .withColumn("barrio", fix_enc(F.trim(F.col("barrio"))))

    # Castear numéricos
    .withColumn("latitude",      F.col("latitude").cast(DoubleType()))
    .withColumn("longitude",     F.col("longitude").cast(DoubleType()))
    .withColumn("rating",        F.col("rating").cast(DoubleType()))
    .withColumn("price_level",   F.col("price_level").cast(IntegerType()))
    .withColumn("total_ratings", F.col("total_ratings").cast(IntegerType()))

    # Normalizar texto
    .withColumn("name",   F.trim(F.col("name")))
    .withColumn("barrio", F.initcap(F.trim(F.col("barrio"))))

    # Imputar nulls
    .withColumn("rating",
        F.when(F.col("rating").isNull(), -1.0).otherwise(F.col("rating")))
    .withColumn("total_ratings",
        F.when(F.col("total_ratings").isNull(), 0).otherwise(F.col("total_ratings")))
    .withColumn("barrio",
        F.when(F.col("barrio").isNull() | (F.col("barrio") == ""), "Desconocido")
         .otherwise(F.col("barrio")))

    # Filtro geográfico: ahora lat/lng sí tienen valores
    .filter(F.col("latitude").between(6.1, 6.4))
    .filter(F.col("longitude").between(-75.7, -75.4))

    .dropDuplicates(["place_id"])
    .withColumn("ingestion_date", F.current_timestamp())
    .select(
        "place_id", "name", "rating", "total_ratings",
        "price_level", "latitude", "longitude",
        "barrio", "ingestion_date"
    )
)

write_trusted(df_places, "places", partition_col="barrio")

# TABLA 2: place_hours — Horarios por lugar/día
# Columnas desde EC2: place_id, day_es, day_en, is_open, open_time, close_time, raw
logger.info("=== PROCESANDO: place_hours ===")
VALID_DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

df_hours = (
    read_csv(f"{RAW_FILES}place_hours.csv", encoding="UTF-8")  

    .withColumn("place_id",   F.trim(F.col("place_id")))
    .withColumn("day_es",     F.lower(F.trim(fix_enc(F.col("day_es")))))
    .withColumn("open_time",  F.trim(F.col("open_time")))
    .withColumn("close_time", F.trim(F.col("close_time")))

    .withColumn("is_open",    F.col("is_open").cast(BooleanType()))
    .withColumn("is_closed",
        F.when(F.col("is_open") == False, True).otherwise(False))

    .filter(F.col("day_es").isin(VALID_DAYS))
    .filter(F.col("place_id").isNotNull() & (F.col("place_id") != ""))
    .dropDuplicates(["place_id", "day_es"])
    .withColumn("ingestion_date", F.current_timestamp())

    .select(
        "place_id", "day_es",
        "open_time", "close_time",
        "is_open", "is_closed",
        "ingestion_date"
    )
)

write_trusted(df_hours, "place_hours", partition_col="day_es")

# TABLA 3: place_types — Categorías por lugar
# Columnas desde EC2: place_id, type
logger.info("=== PROCESANDO: place_types ===")

VALID_TYPES = [
    "restaurant", "cafe", "bar", "night_club", "bakery",
    "art_gallery", "museum", "park", "gym", "store",
    "lodging", "spa", "beauty_salon", "pharmacy", "hospital",
    "school", "library", "movie_theater", "shopping_mall", "food"
]

df_types = (
    read_csv(f"{RAW_FILES}place_types.csv")
    .withColumn("place_id", F.trim(F.col("place_id")))
    .withColumn("type",     F.trim(F.lower(F.col("type"))))
    .filter(F.col("type").isin(VALID_TYPES))
    .filter(F.col("place_id").isNotNull())
    .dropDuplicates(["place_id", "type"])
    .withColumn("ingestion_date", F.current_timestamp())
    .select("place_id", "type", "ingestion_date")
)

write_trusted(df_types, "place_types")

# TABLA 4: encuesta_cultura_2019
# Columnas relevantes para el proyecto:
#   idm            → código de barrio/sector
#   ciudad         → ciudad (todos Medellín)
#   p_seg_cal      → percepción de seguridad en el barrio (texto: Más segura/Menos segura/Igual)
#   p_seg_es       → sensación de seguridad personal (texto)
#   conf_per_gral  → confianza general en las personas (texto)
#   sexo, annos    → datos demográficos básicos
logger.info("=== PROCESANDO: encuesta_cultura_ciudadana ===")

df_encuesta = (
    read_csv(f"{RAW_URL}encuesta_cultura_2019.csv", encoding="UTF-8")  # FIX: era ISO-8859-1

    .select(
        "idm", "ciudad", "fecha",
        "sexo", "annos",
        "p_seg_cal",
        "p_seg_es",
        "conf_per_gral"
    )

    # FIX: reparar doble-encoding en columnas de texto ANTES de filtrar
    .withColumn("ciudad",        fix_enc(F.trim(F.col("ciudad"))))
    .withColumn("p_seg_cal",     fix_enc(F.trim(F.col("p_seg_cal"))))
    .withColumn("p_seg_es",      fix_enc(F.trim(F.col("p_seg_es"))))
    .withColumn("conf_per_gral", fix_enc(F.trim(F.col("conf_per_gral"))))
    .withColumn("sexo",          fix_enc(F.trim(F.col("sexo"))))

    .withColumn("annos", F.col("annos").cast(IntegerType()))
    .withColumn("idm",   F.col("idm").cast(IntegerType()))

    # Este filtro ahora sí matchea porque ciudad ya está bien decodificado
    .filter(F.col("ciudad") == "Medellín")
    .filter(F.col("idm").isNotNull())

    .dropDuplicates()
    .withColumn("ingestion_date", F.current_timestamp())
)

write_trusted(df_encuesta, "encuesta_cultura_ciudadana")


# COMMIT 
logger.info("=== JOB COMPLETADO EXITOSAMENTE ===")
job.commit()