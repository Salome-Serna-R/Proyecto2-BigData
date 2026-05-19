# Proyecto 2 — Big Data Pipeline en AWS
### ST0263 Tópicos Especiales en Telemática — EAFIT 2026-1

---

## ¿Qué hace este proyecto?

Construye un pipeline completo de Big Data sobre AWS que toma datos de múltiples fuentes reales, los centraliza en un Data Lake, los procesa y limpia, y finalmente los analiza para responder preguntas de negocio sobre los lugares de interés en Medellín.

```
┌─────────────────┐     ┌──────────────────────────────────────┐     ┌─────────────────┐
│  FUENTES DE     │     │         DATA LAKE — AWS S3           │     │    ANÁLISIS     │
│  DATOS          │     │                                      │     │    Y SALIDA     │
│                 │     │  raw/        trusted/    refined/    │     │                 │
│  RDS MariaDB  ──┼──▶  │  (crudo)  ──▶ (limpio) ──▶ (listo) │──▶  │  Athena/Hive   │
│  EC2 archivos ──┼──▶  │                                      │     │  PySpark        │
│  URL pública  ──┼──▶  │  Glue + Spark procesan raw→trusted  │     │  Streamlit      │
│                 │     │  Glue Catalog cataloga las tablas    │     │  Matplotlib     │
└─────────────────┘     └──────────────────────────────────────┘     └─────────────────┘
    Punto 2                    Puntos 3, 4, 5                            Puntos 6, 7, 8
```

---

## Caso de Estudio

Análisis geoespacial de ~960 lugares de interés en Medellín (restaurantes, cafés, bares, galerías, etc.) cruzado con datos de percepción ciudadana de la Encuesta de Cultura Ciudadana 2019 de la Alcaldía de Medellín.

**Pregunta central:** ¿Qué barrios de Medellín concentran la mejor oferta de lugares según rating, categoría y horarios, y cómo se relaciona eso con la percepción de seguridad de sus habitantes?

---

## Las 3 zonas del Data Lake

| Zona | Ruta en S3 | Qué contiene | Quién escribe ahí |
|---|---|---|---|
| **raw** | `s3://proyecto2-bigdata/raw/` | Datos crudos tal como llegan de la fuente, sin modificar | Script de ingesta (Punto 3) |
| **trusted** | `s3://proyecto2-bigdata/trusted/` | Datos limpios: tipos corregidos, nulos manejados, tablas normalizadas en Parquet | AWS Glue (Punto 4) |
| **refined** | `s3://proyecto2-bigdata/refined/` | Agregaciones y resultados listos para visualizar | PySpark / Athena (Puntos 6-7) |

> **Regla de oro:** los datos en `raw/` nunca se modifican. Si algo sale mal en el procesamiento, siempre puedes reprocesar desde `raw/`.

---

## Tecnologías utilizadas

| Tecnología | Para qué se usa |
|---|---|
| **AWS RDS MariaDB** | Simula una base de datos operacional (fuente 1) |
| **AWS EC2** | Simula un servidor de archivos con CSVs (fuente 2) |
| **URL pública (MeData)** | Dataset abierto de la Alcaldía de Medellín (fuente 3) |
| **AWS S3** | Data Lake — almacenamiento central del proyecto |
| **AWS Glue** | ETL serverless: limpieza y transformación raw → trusted |
| **Apache Spark / PySpark** | Procesamiento distribuido de datos |
| **AWS Glue Data Catalog** | Catálogo de tablas SQL sobre archivos en S3 |
| **AWS Athena** | SQL interactivo directamente sobre S3 |
| **EMR / Hive** | Procesamiento y consultas SQL a escala |
| **Python** | Scripts de ingesta, análisis PySpark, visualización |
| **Streamlit** | API y visualización web de resultados |
| **Matplotlib / Pandas** | Gráficas y análisis exploratorio |

---

## Datasets

| Dataset | Filas | Formato | Fuente |
|---|---|---|---|
| `places` — lugares de interés | ~960 | CSV / JSON | Google Maps API (proyecto Ferv) |
| `place_hours` — horarios por día | ~6,720 | CSV | Derivado de places |
| `place_types` — categorías | ~1,400 | CSV | Derivado de places |
| Encuesta Cultura Ciudadana 2019 | ~3,800 | CSV | medata.gov.co |

---

## Estructura del Repositorio

```
proyecto2-bigdata/
│
├── punto1-caso-estudio/
│   └── README.md                  # Caso de estudio, preguntas de negocio, descripción datasets
│
├── punto2-fuentes-datos/
│   ├── rds/
│   │   └── schema.sql             # DDL para crear tablas en RDS MariaDB
│   ├── ec2/
│   │   └── setup.sh               # Comandos para montar EC2 y subir archivos
│   └── url/
│       └── source.md              # URL y descripción del dataset público
│
├── punto3-ingesta/
│   ├── ingest_rds.py              # Extrae datos de RDS → S3 raw/rds/
│   ├── ingest_ec2.py              # Copia archivos de EC2 → S3 raw/files/
│   ├── ingest_url.py              # Descarga URL → S3 raw/url/
│   └── README.md
│
├── punto4-glue-spark/
│   ├── glue_job_raw_to_trusted.py # Script PySpark para AWS Glue
│   └── README.md
│
├── punto5-catalogacion/
│   ├── create_tables_hive.sql     # DDL Hive para catalogar tablas
│   └── README.md
│
├── punto6-sql-analitico/
│   ├── queries_athena.sql         # Consultas SQL en Athena
│   ├── queries_hive.sql           # Consultas SQL en Hive
│   └── README.md
│
├── punto7-pyspark/
│   ├── analysis.py                # Análisis descriptivo con PySpark
│   └── README.md
│
├── punto8-visualizacion/
│   ├── app.py                     # App Streamlit
│   ├── charts.py                  # Gráficas con matplotlib
│   └── README.md
│
├── data/
│   ├── csv/                       # CSVs generados localmente (no se suben a git)
│   └── sample/                    # Muestra pequeña para pruebas
│
├── prepare_data.py                # Convierte JSONs → CSVs (preprocesamiento local)
├── .gitignore
└── README.md                      # ← este archivo
```

---

## Cómo reproducir el proyecto

### Prerrequisitos
- Cuenta AWS Academy activa
- Python 3.10+
- `pip install pandas boto3 pymysql streamlit matplotlib pyspark`

### Paso a paso

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/proyecto2-bigdata
cd proyecto2-bigdata

# 2. Preparar los datos localmente
python prepare_data.py --input ./data/places_json --output ./data/csv

# 3. Seguir las instrucciones de cada punto en orden:
#    punto2 → punto3 → punto4 → punto5 → punto6 → punto7 → punto8
```

> Cada carpeta tiene su propio `README.md` con instrucciones detalladas y capturas de pantalla.

---

## Integrantes

| Nombre | Email EAFIT |
|---|---|
| << nombre >> | << email >> |
| << nombre >> | << email >> |
| << nombre >> | << email >> |

**Profesor:** Álvaro Ospina — aeospinas@eafit.edu.co  
**Nube:** AWS Academy