"""
Proyecto 2 - Big Data ST0263
Script: punto2-fuentes-datos/rds/load_rds.py

Carga los CSVs de places a RDS MariaDB.

Uso:
    pip install pandas pymysql python-dotenv
    python load_rds.py

Variables de entorno necesarias (crear archivo .env):
    RDS_HOST=tu-endpoint.rds.amazonaws.com
    RDS_PORT=3306
    RDS_USER=admin
    RDS_PASSWORD=tu-password
    RDS_DB=medellin_places
"""

import os
import pandas as pd
import pymysql
from dotenv import load_dotenv

load_dotenv()

# ── Configuración ──────────────────────────────────────────
RDS_HOST     = os.getenv("RDS_HOST")
RDS_PORT     = int(os.getenv("RDS_PORT", 3306))
RDS_USER     = os.getenv("RDS_USER", "admin")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")
RDS_DB       = os.getenv("RDS_DB", "medellin_places")

CSV_PLACES = "../../data/csv/places.csv"
# ───────────────────────────────────────────────────────────


def get_connection():
    return pymysql.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        user=RDS_USER,
        password=RDS_PASSWORD,
        database=RDS_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def load_places(conn, csv_path: str):
    df = pd.read_csv(csv_path)
    # Reemplazar NaN por None para que MySQL reciba NULL
    df = df.where(pd.notna(df), None)

    sql = """
        INSERT IGNORE INTO places
            (place_id, name, address, neighborhood,
             lat, lng, rating, price_level, review_count)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows = [
        (
            row.place_id, row.name, row.address, row.neighborhood,
            row.lat, row.lng, row.rating, row.price_level, row.review_count,
        )
        for row in df.itertuples(index=False)
    ]

    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    print(f"  ✅ places: {len(rows)} filas insertadas")


def verify(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM places")
        total = cur.fetchone()["total"]
        cur.execute("SELECT AVG(rating) as avg_rating FROM places")
        avg   = cur.fetchone()["avg_rating"]
        cur.execute("SELECT neighborhood, COUNT(*) as cnt FROM places GROUP BY neighborhood ORDER BY cnt DESC LIMIT 5")
        top   = cur.fetchall()

    print(f"\n📊 Verificación RDS:")
    print(f"  Total filas en places: {total}")
    print(f"  Rating promedio:       {avg:.2f}")
    print(f"  Top 5 barrios:")
    for row in top:
        print(f"    {row['neighborhood']:<30} {row['cnt']} lugares")


def main():
    print("=" * 50)
    print("  Punto 2 — Carga de datos a RDS MariaDB")
    print("=" * 50)

    if not RDS_HOST or not RDS_PASSWORD:
        print("❌ Faltan variables de entorno. Crea un archivo .env con RDS_HOST y RDS_PASSWORD")
        return

    print(f"\n🔌 Conectando a {RDS_HOST}...")
    conn = get_connection()
    print("  Conexión exitosa!")

    print("\n📥 Cargando datos...")
    load_places(conn, CSV_PLACES)

    verify(conn)
    conn.close()

    print("\n✅ Listo! RDS MariaDB tiene los datos de places.")
    print("=" * 50)


if __name__ == "__main__":
    main()
