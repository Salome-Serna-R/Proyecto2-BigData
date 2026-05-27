# Punto 7 - Procesamiento analítico descriptivo con PySpark

## Objetivo

Realizar consultas y procesamiento analítico descriptivo usando Spark en Python mediante PySpark.

Este punto toma como entrada archivos CSV limpios provenientes de la zona `trusted/` del proyecto y genera salidas analíticas que pueden ser utilizadas como insumo para consultas, reportes y visualizaciones posteriores.

## Herramientas utilizadas

- Python
- PySpark
- Jupyter Notebook
- pandas

## Prerrequisitos

Para ejecutar PySpark localmente se requiere Java. Se recomienda instalar Eclipse Temurin JDK 17, una distribución gratuita y open source basada en OpenJDK, mantenida por Eclipse Adoptium.

También se requiere:

- Python 3.10 o superior.
- Java 17 configurado en el PATH.
- pip.
- Jupyter Notebook o VS Code con soporte para notebooks.

Validar Java:

```powershell
java -version
```

Validar Python:

```powershell
python --version
```

Validar pip:

```powershell
pip --version
```

## Estructura del directorio

```txt
punto7-pyspark/
  README.md
  requirements.txt
  data/
    trusted_places_clean.csv
    trusted_place_types_clean.csv
    trusted_place_hours_clean.csv
  notebooks/
    punto7_pyspark_analysis.ipynb
  outputs/
    places_by_neighborhood.csv
    places_by_type.csv
    weekend_coverage.csv
    price_rating_analysis.csv
    top_places_readable.csv
```

## Instalación

Desde la carpeta `punto7-pyspark`, crear un ambiente virtual:

```powershell
python -m venv .venv
```

Activar el ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación del ambiente:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

Actualizar pip:

```powershell
python -m pip install --upgrade pip
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Registrar el kernel para Jupyter:

```powershell
python -m ipykernel install --user --name proyecto2-pyspark --display-name "Proyecto 2 PySpark"
```

## Ejecución

Abrir el notebook:

```txt
notebooks/punto7_pyspark_analysis.ipynb
```

Seleccionar el kernel:

```txt
Proyecto 2 PySpark
```

Ejecutar las celdas en orden.

## Archivos de entrada

El notebook utiliza tres archivos principales:

```txt
data/trusted_places_clean.csv
data/trusted_place_types_clean.csv
data/trusted_place_hours_clean.csv
```

Estos archivos representan la salida limpia del proceso raw → trusted del proyecto.

## Procesamiento realizado

El notebook realiza las siguientes operaciones:

1. Creación de una sesión Spark local.
2. Lectura de archivos CSV con PySpark.
3. Exploración del esquema de las tablas.
4. Validación inicial de registros.
5. Relación entre lugares y tipos de lugar.
6. Relación entre lugares y horarios de atención.
7. Construcción de una vista enriquecida con nombre del lugar, barrio, tipo principal, rating, reseñas y apertura en fin de semana.
8. Cálculo de métricas por barrio.
9. Cálculo de métricas por tipo de lugar.
10. Análisis de lugares abiertos en fin de semana.
11. Análisis de rating promedio por nivel de precio.
12. Exportación de resultados analíticos a CSV.

## Salidas generadas

Los resultados se guardan en la carpeta:

```txt
outputs/
```

Archivos esperados:

```txt
outputs/places_by_neighborhood.csv
outputs/places_by_type.csv
outputs/weekend_coverage.csv
outputs/price_rating_analysis.csv
outputs/top_places_readable.csv
```

Descripción de salidas:

| Archivo | Descripción |
|---|---|
| `places_by_neighborhood.csv` | Métricas agregadas por barrio: cantidad de lugares, rating promedio y total de reseñas. |
| `places_by_type.csv` | Métricas agregadas por tipo principal de lugar. |
| `weekend_coverage.csv` | Comparación entre lugares que abren y no abren en fin de semana. |
| `price_rating_analysis.csv` | Relación entre nivel de precio y rating promedio. |
| `top_places_readable.csv` | Muestra legible de lugares ordenados por rating y reseñas, incluyendo nombre, barrio, tipo y métricas principales. |

## Uso de datos desde S3

Para reproducir localmente el análisis, se recomienda descargar los archivos trusted desde S3 hacia la carpeta `data/`.

Ejemplo:

```powershell
aws s3 cp s3://<bucket>/trusted/places_clean.csv .\data\trusted_places_clean.csv
aws s3 cp s3://<bucket>/trusted/place_types_clean.csv .\data\trusted_place_types_clean.csv
aws s3 cp s3://<bucket>/trusted/place_hours_clean.csv .\data\trusted_place_hours_clean.csv
```

Luego ejecutar el notebook normalmente.

Esta opción evita configuraciones adicionales de Spark para lectura directa desde S3 y facilita la reproducción local del proyecto.

## Relación con otros puntos

Los outputs generados en este punto pueden ser utilizados como insumo para:

- Consultas descriptivas adicionales.
- Visualizaciones del punto 8.
- Reportes expuestos mediante API Gateway.
- Comparación con resultados obtenidos mediante SQL en el punto 6.

## Nota sobre datos definitivos

Si los archivos generados por el pipeline final mantienen la misma estructura de columnas, basta con reemplazar los archivos dentro de `data/`. Si cambian los nombres de columnas, se debe ajustar la lectura y transformación inicial en el notebook.