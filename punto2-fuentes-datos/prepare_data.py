"""
Proyecto 2 - Big Data ST0263
Script: prepare_data.py

Convierte los JSONs de Google Maps a 3 CSVs listos para subir a S3/RDS:
  - places.csv        → tabla principal (960 filas aprox)
  - place_hours.csv   → horarios explotados (~6,720 filas)
  - place_types.csv   → tipos explotados (~1,400 filas)

Uso:
  python prepare_data.py --input ./data/places_json --output ./data/csv

Requisitos:
  pip install pandas
"""

import json
import os
import argparse
import pandas as pd
from pathlib import Path


def load_json_files(input_dir: str) -> list[dict]:
    """Carga todos los JSONs de una carpeta."""
    records = []
    input_path = Path(input_dir)
    json_files = list(input_path.glob("*.json"))

    print(f"📂 Encontrados {len(json_files)} archivos JSON en {input_dir}")

    for file in json_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                records.append(data)
        except Exception as e:
            print(f"  ⚠️  Error leyendo {file.name}: {e}")

    print(f"✅ Cargados {len(records)} lugares correctamente")
    return records


def build_places_df(records: list[dict]) -> pd.DataFrame:
    """
    Tabla principal: un registro por lugar.
    Campos: place_id, name, address, neighborhood, lat, lng,
            rating, price_level, review_count
    """
    rows = []
    for r in records:
        rows.append({
            "place_id":     r.get("place_id", ""),
            "name":         r.get("name", ""),
            "address":      r.get("address", ""),
            "neighborhood": r.get("neighborhood", ""),
            "lat":          r.get("lat"),
            "lng":          r.get("lng"),
            "rating":       r.get("rating"),
            "price_level":  r.get("price_level"),
            "review_count": r.get("review_count", 0),
        })
    df = pd.DataFrame(rows)
    print(f"  📋 places.csv          → {len(df):,} filas, {len(df.columns)} columnas")
    return df


def build_hours_df(records: list[dict]) -> pd.DataFrame:
    """
    Tabla de horarios: un registro por (lugar, día).
    Parsea strings como 'lunes: 11:00–19:00' en columnas separadas.
    """
    rows = []
    DAY_MAP = {
        "lunes": "Monday", "martes": "Tuesday", "miércoles": "Wednesday",
        "jueves": "Thursday", "viernes": "Friday", "sábado": "Saturday",
        "domingo": "Sunday"
    }

    for r in records:
        place_id = r.get("place_id", "")
        hours = r.get("hours") or []

        for entry in hours:
            # Formato esperado: "lunes: 11:00–19:00" o "domingo: Cerrado"
            if ":" not in entry:
                continue

            day_raw, _, schedule = entry.partition(":")
            day_raw = day_raw.strip().lower()
            schedule = schedule.strip()

            is_open = schedule.lower() != "cerrado"
            open_time = None
            close_time = None

            if is_open and "–" in schedule:
                parts = schedule.split("–")
                open_time  = parts[0].strip()
                close_time = parts[1].strip() if len(parts) > 1 else None

            rows.append({
                "place_id":   place_id,
                "day_es":     day_raw,
                "day_en":     DAY_MAP.get(day_raw, day_raw),
                "is_open":    is_open,
                "open_time":  open_time,
                "close_time": close_time,
                "raw":        entry,
            })

    df = pd.DataFrame(rows)
    print(f"  🕐 place_hours.csv     → {len(df):,} filas, {len(df.columns)} columnas")
    return df


def build_types_df(records: list[dict]) -> pd.DataFrame:
    """
    Tabla de tipos: un registro por (lugar, tipo).
    Explota el array 'types' en filas individuales.
    """
    rows = []
    for r in records:
        place_id = r.get("place_id", "")
        types = r.get("types") or []

        for t in types:
            rows.append({
                "place_id": place_id,
                "type":     t,
            })

    df = pd.DataFrame(rows)
    print(f"  🏷️  place_types.csv     → {len(df):,} filas, {len(df.columns)} columnas")
    return df


def save_csvs(dfs: dict[str, pd.DataFrame], output_dir: str):
    """Guarda los DataFrames como CSVs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for name, df in dfs.items():
        filepath = output_path / f"{name}.csv"
        df.to_csv(filepath, index=False, encoding="utf-8")
        size_kb = filepath.stat().st_size / 1024
        print(f"  💾 Guardado: {filepath}  ({size_kb:.1f} KB)")


def print_summary(dfs: dict[str, pd.DataFrame]):
    """Imprime un resumen rápido de los datos."""
    places = dfs.get("places")
    if places is None:
        return

    print("\n📊 Resumen del dataset:")
    print(f"  Total lugares:        {len(places):,}")
    print(f"  Con rating:           {places['rating'].notna().sum():,}")
    print(f"  Con price_level:      {places['price_level'].notna().sum():,}")
    print(f"  Rating promedio:      {places['rating'].mean():.2f}")
    print(f"  Barrios únicos:       {places['neighborhood'].nunique()}")

    top_barrios = places['neighborhood'].value_counts().head(5)
    print(f"\n  Top 5 barrios por número de lugares:")
    for barrio, count in top_barrios.items():
        print(f"    {barrio:<30} {count} lugares")

    if "place_types" in dfs:
        top_types = dfs["place_types"]["type"].value_counts().head(5)
        print(f"\n  Top 5 tipos de lugar:")
        for t, count in top_types.items():
            print(f"    {t:<35} {count} lugares")


def main():
    parser = argparse.ArgumentParser(
        description="Convierte JSONs de Google Maps a CSVs para el proyecto Big Data"
    )
    parser.add_argument(
        "--input",
        default="./data/places_json",
        help="Carpeta con los archivos JSON (default: ./data/places_json)"
    )
    parser.add_argument(
        "--output",
        default="./data/csv",
        help="Carpeta de salida para los CSVs (default: ./data/csv)"
    )
    args = parser.parse_args()

    print("=" * 55)
    print("  Proyecto 2 Big Data - Preparación de datos")
    print("=" * 55)

    # 1. Cargar JSONs
    records = load_json_files(args.input)
    if not records:
        print("❌ No se encontraron JSONs. Verifica la carpeta --input")
        return

    # 2. Construir DataFrames
    print("\n🔧 Construyendo tablas...")
    dfs = {
        "places":      build_places_df(records),
        "place_hours": build_hours_df(records),
        "place_types": build_types_df(records),
    }

    # 3. Guardar CSVs
    print(f"\n💾 Guardando CSVs en {args.output}...")
    save_csvs(dfs, args.output)

    # 4. Resumen
    print_summary(dfs)

    print("\n✅ Listo! Próximo paso: subir los CSVs a S3 raw/ y a RDS MariaDB")
    print("=" * 55)


if __name__ == "__main__":
    main()
