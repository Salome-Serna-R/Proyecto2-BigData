# Punto 1 — Caso de Estudio y Preguntas de Negocio

## Descripción del Caso de Estudio

Este proyecto analiza el ecosistema de lugares de interés en la ciudad de **Medellín, Colombia**, combinando dos fuentes de datos complementarias:

1. **Dataset de lugares de interés (Google Maps API):** ~960 establecimientos distribuidos en 198 barrios de la ciudad, incluyendo restaurantes, cafés, bares, galerías de arte, tiendas y otros. Cada registro contiene nombre, dirección, barrio, coordenadas geográficas, rating, nivel de precios, tipos de lugar, horarios de atención y conteo de reseñas.

2. **Encuesta de Cultura Ciudadana de Medellín 2019 (MeData - Alcaldía de Medellín):** Encuesta aplicada a ciudadanos de Medellín con información sobre percepción de seguridad, movilidad, estrato socioeconómico, confianza institucional y tolerancia social por zona de la ciudad.

El objetivo es construir un **pipeline de Big Data sobre AWS** que permita ingestar, transformar y analizar estos datos de forma integrada para responder preguntas relevantes para diferentes actores de la ciudad, como la Alcaldía, agencias de turismo, entre otros.

---

## Fuentes de Datos

| # | Dataset | Formato | Registros | Fuente simulada en AWS |
|---|---|---|---|---|
| 1 | Lugares de interés — tabla principal | CSV | ~960 filas | RDS MariaDB |
| 2 | Horarios por lugar (explotado) | CSV | ~6,720 filas | Archivos en EC2 |
| 3 | Tipos de lugar (explotado) | CSV | ~1,400 filas | Archivos en EC2 |
| 4 | Encuesta Cultura Ciudadana 2019 | CSV | ~3,800 filas | URL pública (MeData) |

**URL fuente pública (Punto 2):**
```
https://medata.gov.co/dataset/1-009-05-000270 

```

---

## Preguntas de Negocio

### P1 — ¿Cuál es el barrio de Medellín con mejor rating promedio de lugares de interés?
**Justificación:** Permite identificar zonas de alta calidad percibida para turismo y planificación urbana.  
**Datos usados:** `places.csv` → columnas `neighborhood`, `rating`  
**Herramienta de respuesta:** Athena / SparkSQL

---

### P2 — ¿Qué categoría de lugar concentra el mayor volumen de reseñas y cuál tiene el rating promedio más alto?
**Justificación:** Ayuda a entender qué tipo de establecimientos generan más engagement ciudadano.  
**Datos usados:** `place_types.csv` + `places.csv` → columnas `type`, `review_count`, `rating`  
**Herramienta de respuesta:** Athena / PySpark

---

### P3 — ¿Qué días de la semana tienen mayor cobertura de lugares abiertos y qué categorías operan más en fin de semana?
**Justificación:** Útil para planificación de recorridos turísticos y análisis de oferta por día.  
**Datos usados:** `place_hours.csv` + `place_types.csv` → columnas `day_en`, `is_open`, `type`  
**Herramienta de respuesta:** SparkSQL / PySpark

---

### P4 — ¿Los barrios con mayor percepción de seguridad (según la Encuesta de Cultura Ciudadana) tienen también mejores ratings en sus lugares de interés?
**Justificación:** Cruza percepción ciudadana con calidad de oferta gastronómica/cultural. Pregunta de alto valor analítico.  
**Datos usados:** `places.csv` + `encuesta_cultura_ciudadana.csv` → cruce por `neighborhood` / zona  
**Herramienta de respuesta:** PySpark / Athena

---

### P5 — ¿Existe relación entre el nivel de precio (`price_level`) y el rating promedio por categoría de lugar?
**Justificación:** Permite evaluar si los lugares más costosos tienen mejor percepción de calidad.  
**Datos usados:** `places.csv` + `place_types.csv` → columnas `price_level`, `rating`, `type`  
**Herramienta de respuesta:** Athena / matplotlib (visualización)

---

## Estructura del Dataset Principal

### `places.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| place_id | STRING | Identificador único del lugar (Google Maps) |
| name | STRING | Nombre del establecimiento |
| address | STRING | Dirección completa |
| neighborhood | STRING | Barrio en Medellín |
| lat | DOUBLE | Latitud geográfica |
| lng | DOUBLE | Longitud geográfica |
| rating | DOUBLE | Rating promedio (1.0 – 5.0) |
| price_level | INT | Nivel de precios (1=bajo, 4=alto, null=sin dato) |
| review_count | INT | Número total de reseñas |

### `place_hours.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| place_id | STRING | FK → places |
| day_es | STRING | Día en español (lunes, martes…) |
| day_en | STRING | Día en inglés (Monday, Tuesday…) |
| is_open | BOOLEAN | True si el lugar abre ese día |
| open_time | STRING | Hora de apertura (HH:MM) |
| close_time | STRING | Hora de cierre (HH:MM) |

### `place_types.csv`
| Campo | Tipo | Descripción |
|---|---|---|
| place_id | STRING | FK → places |
| type | STRING | Categoría del lugar (restaurant, cafe, bar…) |

---

## Estadísticas Iniciales del Dataset

- **Total lugares:** 960
- **Barrios cubiertos:** 198
- **Rating promedio:** 4.38
- **Top barrio:** El Poblado (567 lugares)
- **Top categoría:** restaurant (519 lugares)
- **Período encuesta cultura ciudadana:** 2019

---

## Repositorio

La estructura del repositorio es la siguiente:

```
proyecto2-bigdata/
├── punto1-caso-estudio/
│   └── README.md              ← este archivo
├── punto2-fuentes-datos/
│   ├── rds/schema.sql
│   ├── ec2/
│   └── url/
├── punto3-ingesta/
├── punto4-glue-spark/
├── punto5-catalogacion/
├── punto6-sql-analitico/
├── punto7-pyspark/
├── punto8-visualizacion/
└── README.md
```