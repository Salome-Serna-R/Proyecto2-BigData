#!/bin/bash
# Proyecto 2 - Big Data ST0263
# Script: punto2-fuentes-datos/ec2/setup_ec2.sh
#
# Ejecutar desde tu máquina LOCAL (no desde EC2)
# Sube los archivos CSV a la instancia EC2 y los organiza
#
# Uso:
#   chmod +x setup_ec2.sh
#   ./setup_ec2.sh tu-keypair.pem ec2-XX-XX-XX-XX.compute.amazonaws.com

set -e  # salir si cualquier comando falla

# ── Argumentos ─────────────────────────────────────────────
KEY_FILE=$1
EC2_HOST=$2

if [ -z "$KEY_FILE" ] || [ -z "$EC2_HOST" ]; then
    echo "Uso: ./setup_ec2.sh <ruta-keypair.pem> <ec2-host>"
    echo "Ejemplo: ./setup_ec2.sh ~/Downloads/proyecto2.pem ec2-3-92-10-5.compute.amazonaws.com"
    exit 1
fi
# ───────────────────────────────────────────────────────────

EC2_USER="ec2-user"
REMOTE_DIR="/home/ec2-user/data"
CSV_DIR="../../data/csv"

echo "=============================================="
echo "  Punto 2 — Setup EC2 y subida de archivos"
echo "=============================================="

# 1. Crear directorio en EC2
echo ""
echo "📁 Creando directorio $REMOTE_DIR en EC2..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" \
    "mkdir -p $REMOTE_DIR"

# 2. Subir CSVs
echo ""
echo "📤 Subiendo archivos CSV..."

for FILE in place_hours.csv place_types.csv; do
    LOCAL_PATH="$CSV_DIR/$FILE"
    if [ -f "$LOCAL_PATH" ]; then
        echo "  Subiendo $FILE..."
        scp -i "$KEY_FILE" "$LOCAL_PATH" "$EC2_USER@$EC2_HOST:$REMOTE_DIR/"
        echo "  ✅ $FILE subido"
    else
        echo "  ⚠️  No encontré $LOCAL_PATH — verifica la ruta"
    fi
done

# 3. Verificar que quedaron bien
echo ""
echo "🔍 Verificando archivos en EC2..."
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_HOST" "
    echo 'Archivos en $REMOTE_DIR:'
    ls -lh $REMOTE_DIR/
    echo ''
    echo 'Primeras 2 líneas de place_hours.csv:'
    head -2 $REMOTE_DIR/place_hours.csv
    echo ''
    echo 'Primeras 2 líneas de place_types.csv:'
    head -2 $REMOTE_DIR/place_types.csv
"

echo ""
echo "✅ EC2 lista! Archivos disponibles en $EC2_USER@$EC2_HOST:$REMOTE_DIR"
echo "=============================================="
