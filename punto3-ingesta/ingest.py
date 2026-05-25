"""
Proyecto 2 - Big Data ST0263
Script: punto3-ingesta/ingest.py

Pipeline de ingesta automática: lee de las 3 fuentes y sube a S3 raw/

Fuentes:
  1. RDS MariaDB   → s3://proyecto2-bigdata/raw/rds/places.csv
  2. EC2 archivos  → s3://proyecto2-bigdata/raw/files/place_hours.csv
                  → s3://proyecto2-bigdata/raw/files/place_types.csv
  3. URL pública   → s3://proyecto2-bigdata/raw/url/encuesta_cultura_2019.csv

Uso:
  pip install pandas pymysql boto3 requests paramiko python-dotenv
  python ingest.py

Variables de entorno (.env):
  # RDS
  RDS_HOST=tu-endpoint.rds.amazonaws.com
  RDS_PORT=3306
  RDS_USER=admin
  RDS_PASSWORD=Proyecto2024*
  RDS_DB=medellin_places

  # EC2
  EC2_HOST=ec2-XX-XX-XX-XX.compute-1.amazonaws.com
  EC2_USER=ec2-user
  EC2_KEY_PATH=ruta/a/tu-keypair.pem
  EC2_REMOTE_DIR=/home/ec2-user/data

  # S3
  S3_BUCKET=proyecto2-bigdata
  AWS_REGION=us-east-1
"""

import os
import io
import boto3
import pymysql
import requests
import paramiko
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ── Configuración ──────────────────────────────────────────
RDS_HOST       = os.getenv("RDS_HOST")
RDS_PORT       = int(os.getenv("RDS_PORT", 3306))
RDS_USER       = os.getenv("RDS_USER", "admin")
RDS_PASSWORD   = os.getenv("RDS_PASSWORD")
RDS_DB         = os.getenv("RDS_DB", "medellin_places")

EC2_HOST       = os.getenv("EC2_HOST")
EC2_USER       = os.getenv("EC2_USER", "ec2-user")
EC2_KEY_PATH   = os.getenv("EC2_KEY_PATH")
EC2_REMOTE_DIR = os.getenv("EC2_REMOTE_DIR", "/home/ec2-user/data")

S3_BUCKET      = os.getenv("S3_BUCKET", "proyecto2-bigdata")
AWS_REGION     = os.getenv("AWS_REGION", "us-east-1")

MEDATA_URL     = "https://medata.gov.co/sites/default/files/distribution/1-009-05-000270/encuesta_cultura_2019.csv"

# Rutas en S3
S3_RAW_RDS     = "raw/rds/"
S3_RAW_FILES   = "raw/files/"
S3_RAW_URL     = "raw/url/"
# ───────────────────────────────────────────────────────────


def get_s3_client():
    return boto3.client("s3", region_name=AWS_REGION)


def upload_df_to_s3(s3, df: pd.DataFrame, bucket: str, key: str):
    """Sube un DataFrame como CSV a S3 sin escribir archivo local."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    buffer.seek(0)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )
    print(f"    ✅ s3://{bucket}/{key}  ({len(df):,} filas)")


def upload_bytes_to_s3(s3, data: bytes, bucket: str, key: str):
    """Sube bytes crudos a S3."""
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType="text/csv")
    size_kb = len(data) / 1024
    print(f"    ✅ s3://{bucket}/{key}  ({size_kb:.1f} KB)")


# ── Fuente 1: RDS MariaDB ──────────────────────────────────
def ingest_from_rds(s3):
    print("\n📦 Fuente 1 — RDS MariaDB")

    conn = pymysql.connect(
        host=RDS_HOST, port=RDS_PORT,
        user=RDS_USER, password=RDS_PASSWORD,
        database=RDS_DB, charset="utf8mb4",
    )

    tables = {
        "places": f"{S3_RAW_RDS}places.csv",
    }

    for table, s3_key in tables.items():
        print(f"  Leyendo tabla '{table}'...")
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        upload_df_to_s3(s3, df, S3_BUCKET, s3_key)

    conn.close()
    print("  RDS ✅")


# ── Fuente 2: EC2 Archivos ─────────────────────────────────
def ingest_from_ec2(s3):
    print("\n📦 Fuente 2 — EC2 Archivos")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=EC2_HOST,
        username=EC2_USER,
        key_filename=EC2_KEY_PATH,
    )
    sftp = ssh.open_sftp()

    files = {
        "place_hours.csv": f"{S3_RAW_FILES}place_hours.csv",
        "place_types.csv": f"{S3_RAW_FILES}place_types.csv",
    }

    for filename, s3_key in files.items():
        remote_path = f"{EC2_REMOTE_DIR}/{filename}"
        print(f"  Leyendo {remote_path}...")

        with sftp.open(remote_path, "r") as remote_file:
            content = remote_file.read()

        # Parsear para mostrar info y re-subir a S3
        df = pd.read_csv(io.BytesIO(content))
        upload_df_to_s3(s3, df, S3_BUCKET, s3_key)

    sftp.close()
    ssh.close()
    print("  EC2 ✅")


# ── Fuente 3: URL Pública ──────────────────────────────────
def ingest_from_url(s3):
    print("\n📦 Fuente 3 — URL Pública (MeData)")
    print(f"  Descargando desde {MEDATA_URL}...")

    response = requests.get(MEDATA_URL, timeout=60)
    response.raise_for_status()

    content = response.content
    s3_key = f"{S3_RAW_URL}encuesta_cultura_2019.csv"
    upload_bytes_to_s3(s3, content, S3_BUCKET, s3_key)
    print("  URL ✅")


# ── Crear estructura de S3 si no existe ───────────────────
def ensure_s3_structure(s3):
    """Crea los prefijos base en S3 (raw, trusted, refined)."""
    prefixes = [
        "raw/rds/",
        "raw/files/",
        "raw/url/",
        "trusted/",
        "refined/",
    ]
    for prefix in prefixes:
        s3.put_object(Bucket=S3_BUCKET, Key=prefix, Body=b"")
    print(f"  Estructura de S3 verificada en s3://{S3_BUCKET}/")


# ── Main ───────────────────────────────────────────────────
def main():
    start = datetime.now()

    print("=" * 55)
    print("  Punto 3 — Ingesta automática a S3 Data Lake")
    print(f"  Bucket: s3://{S3_BUCKET}")
    print(f"  Inicio: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # Validar variables de entorno
    missing = []
    for var in ["RDS_HOST", "RDS_PASSWORD", "EC2_HOST", "EC2_KEY_PATH"]:
        if not os.getenv(var):
            missing.append(var)
    if missing:
        print(f"❌ Faltan variables de entorno: {', '.join(missing)}")
        print("   Crea el archivo .env con esas variables y vuelve a correr.")
        return

    s3 = get_s3_client()

    # Verificar que el bucket existe
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        print(f"\n✅ Bucket s3://{S3_BUCKET} encontrado")
    except Exception:
        print(f"\n❌ No se encontró el bucket s3://{S3_BUCKET}")
        print("   Créalo en la consola AWS → S3 → Create bucket")
        return

    ensure_s3_structure(s3)

    # Ingestar desde cada fuente
    errors = []

    try:
        ingest_from_rds(s3)
    except Exception as e:
        print(f"  ❌ Error en RDS: {e}")
        errors.append("RDS")

    try:
        ingest_from_ec2(s3)
    except Exception as e:
        print(f"  ❌ Error en EC2: {e}")
        errors.append("EC2")

    try:
        ingest_from_url(s3)
    except Exception as e:
        print(f"  ❌ Error en URL: {e}")
        errors.append("URL")

    # Resumen final
    elapsed = (datetime.now() - start).seconds
    print("\n" + "=" * 55)
    if not errors:
        print(f"  ✅ Ingesta completada en {elapsed}s — 0 errores")
    else:
        print(f"  ⚠️  Ingesta completada con errores en: {', '.join(errors)}")
    print(f"\n  Datos disponibles en:")
    print(f"    s3://{S3_BUCKET}/raw/rds/places.csv")
    print(f"    s3://{S3_BUCKET}/raw/files/place_hours.csv")
    print(f"    s3://{S3_BUCKET}/raw/files/place_types.csv")
    print(f"    s3://{S3_BUCKET}/raw/url/encuesta_cultura_2019.csv")
    print("=" * 55)


if __name__ == "__main__":
    main()
