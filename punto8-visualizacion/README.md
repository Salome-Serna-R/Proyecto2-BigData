# Punto 8 - Visualización de datos y API

## Objetivo

Implementar una aplicación de visualización de datos y una API de consulta para presentar resultados analíticos del proyecto Big Data.

Este punto utiliza archivos CSV ubicados en la zona `trusted/` del Data Lake en S3. Estos archivos representan la salida del proceso de preparación de datos del punto 4 y son utilizados como base para la visualización y la API.

## Componentes implementados

El punto 8 se divide en dos componentes principales:

1. **Aplicación de visualización con Streamlit**
   - Permite explorar los datos de lugares de interés en Medellín.
   - Muestra métricas, rankings, gráficos y tabla de resultados filtrados.
   - Se ejecuta localmente desde el repositorio.

2. **API de consulta con API Gateway y AWS Lambda**
   - Expone endpoints HTTP de solo lectura.
   - Lee archivos CSV desde S3.
   - Devuelve respuestas en formato JSON.
   - Permite filtrar y consultar resultados analíticos por parámetros.

## Arquitectura

```txt
S3 trusted/
  ├── places_clean.csv
  ├── place_types_clean.csv
  └── place_hours_clean.csv
        ↓
AWS Lambda
        ↓
API Gateway
        ↓
Cliente HTTP / navegador

Repositorio local
        ↓
Streamlit
        ↓
Dashboard interactivo
```

## Estructura del directorio

```txt
punto8-visualizacion/
  README.md
  api/
    README.md
    lambda_function.py
    sample_data/
      trusted_places_clean.csv
      trusted_place_types_clean.csv
      trusted_place_hours_clean.csv
  streamlit_app/
    README.md
    app.py
    requirements.txt
```

## Datos utilizados

Los datos corresponden al caso de estudio de lugares de interés en Medellín. Se utilizan tres archivos principales:

```txt
places_clean.csv
place_types_clean.csv
place_hours_clean.csv
```

Estos archivos deben estar disponibles en la zona `trusted/` del Data Lake en S3 para la API, y en el repositorio local para la aplicación Streamlit.

## Flujo de trabajo

1. Los datos son preparados en etapas anteriores del proyecto.
2. Los archivos limpios se almacenan en la zona `trusted/` de S3.
3. Lambda lee los archivos desde S3 y ejecuta lógica de consulta.
4. API Gateway expone rutas HTTP para consultar los resultados.
5. Streamlit permite visualizar y explorar los datos mediante una interfaz interactiva.

## Evidencias incluidas

Las evidencias del punto 8 deben incluir:

- Bucket S3 con archivos en zona `trusted/`.
- Función Lambda creada.
- Variables de entorno configuradas en Lambda.
- Pruebas de Lambda exitosas.
- API Gateway con rutas configuradas.
- Respuestas JSON desde endpoints HTTP.
- Aplicación Streamlit ejecutándose localmente.
- Dashboard con filtros, métricas, gráficos y tabla de resultados.

## Rutas principales de la API

```txt
GET /summary
GET /records
GET /by-neighborhood
GET /by-type
```

## Ejecución de Streamlit

Ver instrucciones detalladas en:

```txt
streamlit_app/README.md
```

## Configuración de API Gateway y Lambda

Ver instrucciones detalladas en:

```txt
api/README.md
```

## Nota sobre datos trusted

Durante la implementación se utilizaron archivos con la estructura esperada de la zona `trusted/`. En la integración final del proyecto, estos archivos deben corresponder a los outputs definitivos generados por el proceso de preparación de datos desde raw hacia trusted.