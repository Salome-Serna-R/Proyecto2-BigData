# Aplicación Streamlit - Visualización de lugares de interés

## Objetivo

Construir una aplicación de visualización de datos para explorar información de lugares de interés en Medellín.

La aplicación permite analizar barrios, tipos de lugar, rating promedio, volumen de reseñas, niveles de precio y disponibilidad en fin de semana.

## Herramientas utilizadas

- Python
- Streamlit
- pandas
- Plotly

## Estructura

```txt
streamlit_app/
  README.md
  app.py
  requirements.txt
```

La aplicación lee archivos ubicados en:

```txt
../api/sample_data/
```

Archivos esperados:

```txt
trusted_places_clean.csv
trusted_place_types_clean.csv
trusted_place_hours_clean.csv
```

## Instalación

Desde la carpeta:

```txt
punto8-visualizacion/streamlit_app
```

Crear ambiente virtual:

```powershell
python -m venv .venv
```

Activar ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

## Ejecución

Desde la carpeta `streamlit_app` ejecutar:

```powershell
python -m streamlit run app.py
```

La aplicación se abrirá normalmente en:

```txt
http://localhost:8501
```

## Funcionalidades

La aplicación incluye:

1. Métricas generales:
   - Lugares filtrados.
   - Rating promedio.
   - Total de reseñas.
   - Lugares abiertos en fin de semana.

2. Filtros interactivos:
   - Barrio.
   - Tipo de lugar principal.
   - Rating mínimo.
   - Solo lugares abiertos en fin de semana.
   - Cantidad de elementos en rankings.

3. Visualizaciones:
   - Top barrios por cantidad de lugares.
   - Tipos de lugar más frecuentes.
   - Rating promedio por nivel de precio.
   - Tabla de lugares ordenados por rating y reseñas.

4. Conclusión descriptiva:
   - Resumen automático de los principales hallazgos según los filtros aplicados.

## Evidencias sugeridas

Guardar capturas de:

1. Aplicación ejecutándose en navegador.
2. Dashboard principal con métricas y gráficos.
3. Filtros aplicados desde la barra lateral.
4. Tabla de resultados.
5. Conclusión descriptiva generada por la aplicación.

## Relación con API Gateway

La aplicación Streamlit y la API Gateway forman dos formas complementarias de consultar los datos:

- Streamlit permite una exploración visual e interactiva.
- API Gateway expone consultas HTTP en formato JSON.

Ambos componentes se basan en la misma estructura de datos trusted del proyecto.

## Reemplazo por datos definitivos

Los archivos locales de `sample_data/` pueden ser reemplazados por los outputs definitivos del proceso raw → trusted, siempre que mantengan la estructura de columnas esperada por la aplicación.

Si los nombres de columnas cambian, se debe ajustar la lectura y transformación inicial en `app.py`.