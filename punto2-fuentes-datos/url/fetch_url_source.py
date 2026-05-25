"""
Proyecto 2 - Big Data ST0263
Script: punto2-fuentes-datos/url/fetch_url_source.py

Descarga el dataset público de MeData (Alcaldía de Medellín)
y lo guarda localmente para verificación antes de ingestarlo a S3.

Dataset: Encuesta de Cultura Ciudadana - Medellín 2019
URL: https://medata.gov.co/dataset/1-009-05-000270

Uso:
    pip install requests
    python fetch_url_source.py
"""

import requests
import os
from pathlib import Path

# ── URL de descarga directa del CSV ───────────────────────
# Esta es la URL que usará el script de ingesta (Punto 3)
# para descargar el archivo y subirlo a S3 raw/url/
DATASET_URL = "https://medata.gov.co/sites/default/files/distribution/1-009-05-000270/encuesta_cultura_2019.csv"
OUTPUT_DIR  = Path("../../data/csv")
OUTPUT_FILE = OUTPUT_DIR / "encuesta_cultura_ciudadana.csv"
# ───────────────────────────────────────────────────────────


def download_dataset(url: str, output_path: Path) -> bool:
    """Descarga el dataset desde la URL pública."""
    print(f"🌐 Descargando desde:\n   {url}")

    try:
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        total = 0
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total += len(chunk)

        size_kb = total / 1024
        print(f"  ✅ Descargado: {output_path} ({size_kb:.1f} KB)")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"  ❌ Error HTTP: {e}")
        print("  💡 Verifica la URL directa de descarga en medata.gov.co")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def verify_csv(path: Path):
    """Muestra las primeras líneas del CSV descargado."""
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = [f.readline() for _ in range(3)]

    print(f"\n📋 Primeras líneas del archivo:")
    for i, line in enumerate(lines):
        preview = line[:120] + "..." if len(line) > 120 else line
        print(f"  [{i}] {preview.strip()}")


def main():
    print("=" * 55)
    print("  Punto 2 — Fuente URL: MeData Medellín")
    print("=" * 55)
    print(f"\n📌 Dataset: Encuesta Cultura Ciudadana Medellín 2019")
    print(f"📌 Fuente:  medata.gov.co")
    print(f"📌 URL:     {DATASET_URL}")

    success = download_dataset(DATASET_URL, OUTPUT_FILE)

    if success:
        verify_csv(OUTPUT_FILE)
        print(f"\n✅ Dataset disponible en: {OUTPUT_FILE}")
        print("   El script de ingesta (Punto 3) usará directamente la URL,")
        print("   no este archivo local.")
    else:
        print("\n⚠️  Si la descarga falla, descarga el CSV manualmente desde:")
        print("   https://medata.gov.co/dataset/1-009-05-000270")
        print("   y guárdalo en data/csv/encuesta_cultura_ciudadana.csv")

    print("=" * 55)


if __name__ == "__main__":
    main()
