# Punto 3 — Ingesta Automática al Data Lake (S3)

## ¿Qué hace este punto?

Lee datos de las **3 fuentes del Punto 2** y los sube automáticamente
a la zona `raw/` del Data Lake en S3. Un solo comando hace todo.

```
RDS MariaDB  ──────────────────▶  s3://proyecto2-bigdata/raw/rds/places.csv
EC2 archivos ──────────────────▶  s3://proyecto2-bigdata/raw/files/place_hours.csv
                                  s3://proyecto2-bigdata/raw/files/place_types.csv
URL MeData   ──────────────────▶  s3://proyecto2-bigdata/raw/url/encuesta_cultura_2019.csv
```

> Los datos en `raw/` nunca se modifican. Son la copia fiel de las fuentes originales.

---

## Prerrequisitos

- Punto 2 completado (RDS con datos, EC2 con archivos, URL verificada)
- Bucket S3 creado: `proyecto2-bigdata`
- AWS Academy activo (las credenciales de boto3 se toman automáticamente)

```bash
pip install pandas pymysql boto3 requests paramiko python-dotenv
```

---

## Paso 1 — Crear el bucket S3

1. Ir a **AWS Console → S3 → Create bucket**
2. Configurar:

| Campo | Valor |
|---|---|
| Bucket name | `proyecto2-bigdata` |
| Region | `us-east-1` |
| Block public access | Dejar activado (default) |
| Versioning | Disabled |

3. Click **Create bucket**

La estructura de carpetas la crea automáticamente el script.

---

## Paso 2 — Configurar el archivo .env

En la carpeta `punto3-ingesta/` crear el archivo `.env`:

```env
# RDS
RDS_HOST=tu-endpoint.rds.amazonaws.com
RDS_PORT=3306
RDS_USER=admin
RDS_PASSWORD=Proyecto2024*
RDS_DB=medellin_places

# EC2
EC2_HOST=ec2-XX-XX-XX-XX.compute-1.amazonaws.com
EC2_USER=ec2-user
EC2_KEY_PATH=/ruta/absoluta/a/tu-keypair.pem
EC2_REMOTE_DIR=/home/ec2-user/data

# S3
S3_BUCKET=proyecto2-bigdata
AWS_REGION=us-east-1
```

> ⚠️ Este archivo está en `.gitignore` — nunca lo subas al repo.

---

## Paso 3 — Ejecutar la ingesta

```bash
cd punto3-ingesta
python ingest.py
```

Salida esperada:

```
=======================================================
  Punto 3 — Ingesta automática a S3 Data Lake
  Bucket: s3://proyecto2-bigdata
  Inicio: 2026-05-26 10:00:00
=======================================================
✅ Bucket s3://proyecto2-bigdata encontrado
  Estructura de S3 verificada en s3://proyecto2-bigdata/

📦 Fuente 1 — RDS MariaDB
  Leyendo tabla 'places'...
    ✅ s3://proyecto2-bigdata/raw/rds/places.csv  (960 filas)
  RDS ✅

📦 Fuente 2 — EC2 Archivos
  Leyendo /home/ec2-user/data/place_hours.csv...
    ✅ s3://proyecto2-bigdata/raw/files/place_hours.csv  (6,720 filas)
  Leyendo /home/ec2-user/data/place_types.csv...
    ✅ s3://proyecto2-bigdata/raw/files/place_types.csv  (1,400 filas)
  EC2 ✅

📦 Fuente 3 — URL Pública (MeData)
  Descargando desde https://medata.gov.co/...
    ✅ s3://proyecto2-bigdata/raw/url/encuesta_cultura_2019.csv  (XXX KB)
  URL ✅

=======================================================
  ✅ Ingesta completada en 12s — 0 errores

  Datos disponibles en:
    s3://proyecto2-bigdata/raw/rds/places.csv
    s3://proyecto2-bigdata/raw/files/place_hours.csv
    s3://proyecto2-bigdata/raw/files/place_types.csv
    s3://proyecto2-bigdata/raw/url/encuesta_cultura_2019.csv
=======================================================
```

---

## Paso 4 — Verificar en la consola AWS

1. Ir a **AWS Console → S3 → proyecto2-bigdata**
2. Navegar a `raw/` y verificar que existen las 4 subcarpetas
3. Verificar que cada archivo tiene el tamaño correcto:

| Archivo | Tamaño esperado |
|---|---|
| `raw/rds/places.csv` | ~150 KB |
| `raw/files/place_hours.csv` | ~400 KB |
| `raw/files/place_types.csv` | ~50 KB |
| `raw/url/encuesta_cultura_2019.csv` | variable |

---

## Estructura del Data Lake después de este punto

```
s3://proyecto2-bigdata/
├── raw/                          ← ✅ lleno después de este punto
│   ├── rds/
│   │   └── places.csv
│   ├── files/
│   │   ├── place_hours.csv
│   │   └── place_types.csv
│   └── url/
│       └── encuesta_cultura_2019.csv
├── trusted/                      ← ⬜ Glue lo llena en Punto 4
└── refined/                      ← ⬜ PySpark lo llena en Punto 7
```

---

## Estructura de archivos de este punto

```
punto3-ingesta/
├── ingest.py    ← script principal, corre todo
├── .env         ← credenciales (NO subir a git)
└── README.md    ← este archivo
```
