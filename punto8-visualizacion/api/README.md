# Punto 8 - API Gateway y Lambda para consultas analíticas

## Objetivo

Exponer resultados analíticos mediante una API HTTP usando AWS API Gateway y AWS Lambda.

La API permite consultar información procesada a partir de archivos CSV almacenados en la zona `trusted/` del Data Lake en S3. Las respuestas se devuelven en formato JSON y pueden ser consumidas desde navegador, herramientas HTTP o aplicaciones de visualización.

## Arquitectura

```txt
S3 trusted/
  ├── places_clean.csv
  ├── place_types_clean.csv
  └── place_hours_clean.csv
        ↓
AWS Lambda
        ↓
API Gateway HTTP API
        ↓
Cliente HTTP
```

## Archivos de entrada esperados

La función Lambda espera encontrar los siguientes archivos en S3:

```txt
trusted/places_clean.csv
trusted/place_types_clean.csv
trusted/place_hours_clean.csv
```

Estos archivos representan la salida del procesamiento raw → trusted realizado en etapas anteriores del proyecto.

## Archivo principal

```txt
lambda_function.py
```

Este archivo contiene la lógica de la función Lambda. La función:

1. Lee archivos CSV desde S3.
2. Normaliza tipos básicos de datos.
3. Relaciona lugares con tipos de lugar y horarios.
4. Aplica filtros recibidos por query parameters.
5. Calcula métricas descriptivas.
6. Devuelve respuestas JSON.

## Creación del bucket S3

Crear un bucket S3 en la misma región donde se ejecutará Lambda y API Gateway.

Ejemplo de nombre:

```txt
proyecto2-bigdata-<identificador>
```

Dentro del bucket crear el prefijo:

```txt
trusted/
```

Subir allí los archivos:

```txt
places_clean.csv
place_types_clean.csv
place_hours_clean.csv
```

## Creación de la función Lambda

1. Ir al servicio **AWS Lambda**.
2. Seleccionar **Create function**.
3. Elegir **Author from scratch**.
4. Configurar:
   - Function name: `proyecto2-punto8-analytics-api`
   - Runtime: `Python 3.14` o versión Python disponible en el laboratorio.
   - Architecture: `x86_64`
5. En permisos, seleccionar **Use an existing role**.
6. Usar el rol disponible del laboratorio, por ejemplo `LabRole`.
7. Crear la función.

## Consideraciones sobre permisos del laboratorio

El ambiente de AWS Academy puede restringir la creación de nuevos roles IAM. Por esta razón, la función Lambda se configuró usando un rol existente del laboratorio.

Durante la creación de la función se seleccionó la opción:

```txt
Use an existing role
```

en lugar de crear un rol nuevo automáticamente.

## Código de Lambda

Copiar el contenido de:

```txt
lambda_function.py
```

en el editor de código de AWS Lambda y seleccionar:

```txt
Deploy
```

## Variables de entorno

Configurar las siguientes variables de entorno en Lambda:

```txt
BUCKET_NAME=<nombre-del-bucket>
PLACES_KEY=trusted/places_clean.csv
TYPES_KEY=trusted/place_types_clean.csv
HOURS_KEY=trusted/place_hours_clean.csv
```

Ejemplo:

```txt
BUCKET_NAME=proyecto2-bigdata-brahiam-punto8
PLACES_KEY=trusted/places_clean.csv
TYPES_KEY=trusted/place_types_clean.csv
HOURS_KEY=trusted/place_hours_clean.csv
```

## Permisos requeridos

La función Lambda debe tener permiso para leer objetos desde el bucket S3.

Permiso requerido:

```txt
s3:GetObject
```

Recurso esperado:

```txt
arn:aws:s3:::<bucket>/trusted/*
```

En el laboratorio, este permiso puede estar incluido en el rol existente. Si no lo está, se debe agregar una política al rol de ejecución de Lambda.

## Pruebas desde Lambda

### Prueba 1 - Summary

Evento de prueba:

```json
{
  "rawPath": "/summary",
  "queryStringParameters": {}
}
```

Resultado esperado:

```json
{
  "statusCode": 200,
  "body": "{...}"
}
```

La respuesta debe incluir métricas como:

```txt
records
average_rating
total_reviews
average_price_level
```

### Prueba 2 - Records filtrados

Evento de prueba:

```json
{
  "rawPath": "/records",
  "queryStringParameters": {
    "type": "restaurant",
    "min_rating": "4.5",
    "limit": "10"
  }
}
```

La respuesta debe devolver registros filtrados por tipo de lugar y rating mínimo.

## Creación de API Gateway

1. Ir a **API Gateway**.
2. Crear una **HTTP API**.
3. Agregar integración con Lambda.
4. Seleccionar la función:

```txt
proyecto2-punto8-analytics-api
```

5. Usar payload format version:

```txt
2.0
```

6. Configurar las rutas:

```txt
GET /summary
GET /records
GET /by-neighborhood
GET /by-type
```

7. Usar stage:

```txt
$default
```

8. Mantener auto-deploy habilitado.

## Endpoints disponibles

### GET /summary

Devuelve métricas generales del dataset.

Ejemplo:

```txt
/summary
```

### GET /records

Devuelve registros filtrados.

Ejemplo:

```txt
/records?type=restaurant&min_rating=4.5&limit=10
```

### GET /by-neighborhood

Devuelve agregación por barrio.

Ejemplo:

```txt
/by-neighborhood?limit=10
```

### GET /by-type

Devuelve agregación por tipo de lugar.

Ejemplo:

```txt
/by-type?limit=10
```

## Ejecución desde navegador

Después de crear API Gateway, copiar el **Invoke URL** del stage `$default`.

Ejemplo:

```txt
https://<api-id>.execute-api.us-east-1.amazonaws.com
```

Probar los endpoints:

```txt
https://<api-id>.execute-api.us-east-1.amazonaws.com/summary
```

```txt
https://<api-id>.execute-api.us-east-1.amazonaws.com/records?type=restaurant&min_rating=4.5&limit=10
```

```txt
https://<api-id>.execute-api.us-east-1.amazonaws.com/by-neighborhood?limit=10
```

```txt
https://<api-id>.execute-api.us-east-1.amazonaws.com/by-type?limit=10
```

## Evidencias sugeridas

Guardar capturas de:

1. Bucket S3 con el prefijo `trusted/`.
2. Archivos CSV cargados en `trusted/`.
3. Función Lambda creada.
4. Variables de entorno configuradas.
5. Código Lambda desplegado.
6. Prueba `/summary` ejecutada desde Lambda.
7. Prueba `/records` ejecutada desde Lambda.
8. API Gateway con rutas configuradas.
9. Invoke URL del stage `$default`.
10. Endpoint `/summary` respondiendo desde navegador.
11. Endpoint `/records` respondiendo desde navegador.
12. Endpoint `/by-neighborhood` o `/by-type` respondiendo desde navegador.

## Nota sobre los datos

La API se diseñó para leer archivos ubicados en la zona `trusted/` del Data Lake. Si los archivos finales generados por el pipeline tienen los mismos nombres de columnas, basta con reemplazar los CSV existentes en S3. Si cambian los nombres de columnas, se debe ajustar la lógica de lectura en `lambda_function.py`.