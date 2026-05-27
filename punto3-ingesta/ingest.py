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

Variables de entorno (.env en la raiz del proyecto):
  RDS_HOST=tu-endpoint.rds.amazonaws.com
  RDS_PORT=3306
  RDS_USER=admin
  RDS_PASSWORD=tu-password
  RDS_DB=medellin_places
  EC2_HOST=ec2-XX-XX-XX-XX.compute-1.amazonaws.com
  EC2_USER=ec2-user
  EC2_KEY_PATH=ruta/absoluta/a/keypair.pem
  EC2_REMOTE_DIR=/home/ec2-user/data
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
from pathlib import Path

# Cargar .env desde la raiz del proyecto (2 niveles arriba de este script)
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# ── Configuracion ──────────────────────────────────────────
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
    print(f"    OK s3://{bucket}/{key}  ({len(df):,} filas)")


def upload_bytes_to_s3(s3, data: bytes, bucket: str, key: str):
    """Sube bytes crudos a S3."""
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType="text/csv")
    size_kb = len(data) / 1024
    print(f"    OK s3://{bucket}/{key}  ({size_kb:.1f} KB)")


# ── Fuente 1: RDS MariaDB ──────────────────────────────────
def ingest_from_rds(s3):
    print("\nFuente 1 - RDS MariaDB")

    conn = pymysql.connect(
        host=RDS_HOST, port=RDS_PORT,
        user=RDS_USER, password=RDS_PASSWORD,
        database=RDS_DB, charset="utf8mb4",
    )

    print("  Leyendo tabla places...")
    df = pd.read_sql("SELECT * FROM places", conn)
    conn.close()

    upload_df_to_s3(s3, df, S3_BUCKET, f"{S3_RAW_RDS}places.csv")
    print("  RDS OK")


# ── Fuente 2: EC2 Archivos ─────────────────────────────────
def ingest_from_ec2(s3):
    print("\nFuente 2 - EC2 Archivos")

    # Normalizar ruta del keypair (fix para Windows con barras invertidas)
    key_path = str(EC2_KEY_PATH).replace("\\", "/")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=EC2_HOST,
        username=EC2_USER,
        key_filename=key_path,
        timeout=30,
    )
    sftp = ssh.open_sftp()

    files = [
        ("place_hours.csv", f"{S3_RAW_FILES}place_hours.csv"),
        ("place_types.csv", f"{S3_RAW_FILES}place_types.csv"),
    ]

    for filename, s3_key in files:
        remote_path = f"{EC2_REMOTE_DIR}/{filename}"
        print(f"  Leyendo {remote_path}...")

        # FIX: leer en modo binario para evitar problemas de encoding
        with sftp.open(remote_path, "rb") as remote_file:
            content = remote_file.read()

        df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
        upload_df_to_s3(s3, df, S3_BUCKET, s3_key)

    sftp.close()
    ssh.close()
    print("  EC2 OK")


# ── Fuente 3: URL Publica ──────────────────────────────────
def ingest_from_url(s3):
    print("\nFuente 3 - URL Publica (MeData)")
    print(f"  Descargando desde medata.gov.co...")

    # FIX: headers para evitar bloqueo por user-agent
    headers = {"User-Agent": "Mozilla/5.0 (compatible; proyecto2-bigdata/1.0)"}
    response = requests.get(MEDATA_URL, timeout=60, headers=headers)
    response.raise_for_status()

    content = response.content
    s3_key = f"{S3_RAW_URL}encuesta_cultura_2019.csv"
    upload_bytes_to_s3(s3, content, S3_BUCKET, s3_key)
    print("  URL OK")


# ── Crear estructura de S3 ─────────────────────────────────
def ensure_s3_structure(s3):
    prefixes = ["raw/rds/", "raw/files/", "raw/url/", "trusted/", "refined/"]
    for prefix in prefixes:
        s3.put_object(Bucket=S3_BUCKET, Key=prefix, Body=b"")
    print(f"  Estructura de S3 verificada en s3://{S3_BUCKET}/")


# ── Main ───────────────────────────────────────────────────
def main():
    start = datetime.now()

    print("=" * 55)
    print("  Punto 3 - Ingesta automatica a S3 Data Lake")
    print(f"  Bucket: s3://{S3_BUCKET}")
    print(f"  Inicio: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # Validar variables de entorno
    missing = [v for v in ["RDS_HOST", "RDS_PASSWORD", "EC2_HOST", "EC2_KEY_PATH"] if not os.getenv(v)]
    if missing:
        print(f"ERROR: Faltan variables en el .env: {', '.join(missing)}")
        print(f"       Buscando .env en: {dotenv_path}")
        return

    # Validar que el keypair existe
    if not Path(EC2_KEY_PATH).exists():
        print(f"ERROR: No se encontro el keypair en: {EC2_KEY_PATH}")
        print("       Verifica que EC2_KEY_PATH en el .env sea la ruta absoluta correcta")
        return

    s3 = get_s3_client()

    # Verificar bucket
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        print(f"\nBucket s3://{S3_BUCKET} encontrado")
    except Exception:
        print(f"\nERROR: No se encontro el bucket s3://{S3_BUCKET}")
        print("       Crealo en la consola AWS -> S3 -> Crear bucket")
        return

    ensure_s3_structure(s3)

    # Ingestar desde cada fuente (errores no detienen las demas)
    errors = []

    try:
        ingest_from_rds(s3)
    except Exception as e:
        print(f"  ERROR en RDS: {e}")
        errors.append("RDS")

    try:
        ingest_from_ec2(s3)
    except Exception as e:
        print(f"  ERROR en EC2: {e}")
        errors.append("EC2")

    try:
        ingest_from_url(s3)
    except Exception as e:
        print(f"  ERROR en URL: {e}")
        errors.append("URL")

    # Resumen final
    elapsed = (datetime.now() - start).seconds
    print("\n" + "=" * 55)
    if not errors:
        print(f"  Ingesta completada en {elapsed}s - 0 errores")
    else:
        print(f"  Ingesta con errores en: {', '.join(errors)}")
    print(f"\n  Datos en S3:")
    print(f"    s3://{S3_BUCKET}/raw/rds/places.csv")
    print(f"    s3://{S3_BUCKET}/raw/files/place_hours.csv")
    print(f"    s3://{S3_BUCKET}/raw/files/place_types.csv")
    print(f"    s3://{S3_BUCKET}/raw/url/encuesta_cultura_2019.csv")
    print("=" * 55)


if __name__ == "__main__":
    main()