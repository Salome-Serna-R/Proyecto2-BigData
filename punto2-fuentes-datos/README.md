# Punto 2 — Fuentes de Datos

## ¿Qué hace este punto?

Simula un escenario real de empresa donde los datos viven en **tres fuentes distintas** antes de ser centralizados en el Data Lake. El pipeline de ingesta (Punto 3) leerá directamente desde estas fuentes.

```
places.csv          ──▶  RDS MariaDB       (base de datos operacional)
place_hours.csv     ──▶  EC2               (servidor de archivos)
place_types.csv     ──▶  EC2               (servidor de archivos)
encuesta medata     ──▶  URL pública       (API/dataset abierto)
```

---

## Prerrequisitos

- Cuenta AWS Academy activa con laboratorio iniciado
- Python 3.10+ con: `pip install pandas pymysql python-dotenv requests`
- Los 3 CSVs generados por `prepare_data.py` en `data/csv/`
- Terminal con acceso a SSH y SCP

---

## Fuente 1 — RDS MariaDB

### Qué contiene
La tabla principal `places` con los ~960 lugares de interés: `place_id`, `name`, `neighborhood`, `lat`, `lng`, `rating`, `price_level`, `review_count`.

### Paso 1 — Crear la instancia RDS en AWS Academy

1. Ir a **AWS Console → RDS → Create database**
2. Configurar con estos valores exactos:

| Campo | Valor |
|---|---|
| Engine | MariaDB |
| Version | 10.6 (o la disponible) |
| Template | Free tier |
| DB instance identifier | `proyecto2-db` |
| Master username | `admin` |
| Master password | `Proyecto2024*` (anótala) |
| Instance class | `db.t3.micro` |
| Storage | 20 GB gp2 |
| **Public access** | **YES** ← obligatorio |
| VPC security group | Crear nuevo |

3. Esperar ~5 minutos hasta que el estado sea **Available**
4. Copiar el **Endpoint** (algo como `proyecto2-db.xxxx.us-east-1.rds.amazonaws.com`)

### Paso 2 — Abrir el puerto 3306

1. Ir a **EC2 → Security Groups**
2. Buscar el security group que se creó con la RDS
3. **Inbound rules → Edit → Add rule:**
   - Type: `MySQL/Aurora`
   - Port: `3306`
   - Source: `0.0.0.0/0`

### Paso 3 — Crear las tablas

Conectarse y ejecutar el schema:

```bash
mysql -h TU_ENDPOINT -u admin -pProyecto2024* < rds/schema.sql
```

O si no tienes mysql CLI, usar **MySQL Workbench** o **DBeaver** con los datos de conexión.

### Paso 4 — Cargar los datos

Crear el archivo `punto2-fuentes-datos/.env`:

```env
RDS_HOST=tu-endpoint.rds.amazonaws.com
RDS_PORT=3306
RDS_USER=admin
RDS_PASSWORD=Proyecto2024*
RDS_DB=medellin_places
```

Ejecutar el script:

```bash
cd punto2-fuentes-datos
python rds/load_rds.py
```

Salida esperada:
```
✅ places: 960 filas insertadas
📊 Verificación RDS:
  Total filas en places: 960
  Rating promedio: 4.38
  Top 5 barrios:
    El Poblado                     567 lugares
    ...
```

### Verificación rápida

```sql
-- Conectarse a RDS y correr:
SELECT COUNT(*) FROM places;               -- debe dar ~960
SELECT * FROM places LIMIT 5;
SELECT neighborhood, COUNT(*) as total 
FROM places 
GROUP BY neighborhood 
ORDER BY total DESC 
LIMIT 10;
```

---

## Fuente 2 — EC2 (Archivos)

### Qué contiene
Dos archivos CSV en una instancia EC2:
- `place_hours.csv` (~6,720 filas) — horarios por lugar y día
- `place_types.csv` (~1,400 filas) — categorías por lugar

### Paso 1 — Lanzar la instancia EC2

1. Ir a **AWS Console → EC2 → Launch instance**
2. Configurar:

| Campo | Valor |
|---|---|
| Name | `proyecto2-files` |
| AMI | Amazon Linux 2023 |
| Instance type | `t2.micro` |
| Key pair | Crear nuevo → descargar `.pem` → guardar bien |
| Security group | Permitir SSH (puerto 22) desde `0.0.0.0/0` |
| Storage | 8 GB (default) |

3. Click **Launch instance**
4. Esperar ~2 minutos hasta que el estado sea **Running**
5. Copiar la **Public IPv4 DNS** (algo como `ec2-3-92-10-5.compute-1.amazonaws.com`)

### Paso 2 — Subir los archivos

```bash
# En tu máquina local, desde la raíz del proyecto:
chmod 400 ruta/a/tu-keypair.pem

cd punto2-fuentes-datos
chmod +x ec2/setup_ec2.sh
./ec2/setup_ec2.sh ruta/a/tu-keypair.pem ec2-XX-XX-XX-XX.compute-1.amazonaws.com
```

Salida esperada:
```
📁 Creando directorio /home/ec2-user/data en EC2...
📤 Subiendo archivos CSV...
  ✅ place_hours.csv subido
  ✅ place_types.csv subido
🔍 Verificando archivos en EC2...
Archivos en /home/ec2-user/data:
-rw-r--r-- place_hours.csv  420K
-rw-r--r-- place_types.csv   55K
```

### Verificación manual

```bash
# Conectarse a la EC2
ssh -i tu-keypair.pem ec2-user@TU_IP_EC2

# Verificar archivos
ls -lh ~/data/
wc -l ~/data/place_hours.csv    # debe dar ~6721 (6720 + header)
wc -l ~/data/place_types.csv    # debe dar ~1401
head -3 ~/data/place_hours.csv
```

---

## Fuente 3 — URL Pública (MeData)

### Qué contiene
Dataset de la **Encuesta de Cultura Ciudadana de Medellín 2019** publicado por la Alcaldía de Medellín en el portal de datos abiertos MeData.

| Campo | Valor |
|---|---|
| Nombre | Encuesta de Cultura Ciudadana Medellín 2019 |
| Fuente | Alcaldía de Medellín — MeData |
| URL del dataset | https://medata.gov.co/dataset/1-009-05-000270 |
| Formato | CSV |
| Filas aprox. | ~3,800 encuestados |

### Por qué esta fuente no requiere montar nada

Esta es una fuente **ya disponible en internet**. El script de ingesta (Punto 3) la descarga directamente desde la URL al momento de ejecutarse. Esto simula el escenario real donde una fuente externa expone datos via HTTP.

### Verificar que la URL funciona

```bash
python url/fetch_url_source.py
```

O manualmente:
```bash
curl -L "https://medata.gov.co/sites/default/files/distribution/1-009-05-000270/encuesta_cultura_2019.csv" \
     -o data/csv/encuesta_cultura_ciudadana.csv
```

---

## Resumen de las 3 fuentes

| Fuente | Tipo | Host | Datos | Estado |
|---|---|---|---|---|
| RDS MariaDB | Base de datos | `proyecto2-db.xxxx.rds.amazonaws.com` | `places` (960 filas) | ⬜ Pendiente |
| EC2 Archivos | Servidor de archivos | `ec2-XX-XX.compute.amazonaws.com` | `place_hours`, `place_types` | ⬜ Pendiente |
| URL MeData | HTTP público | `medata.gov.co` | Encuesta Cultura Ciudadana 2019 | ✅ Disponible |

> Actualiza este README con los endpoints reales de RDS y EC2 una vez creados, y cambia el estado a ✅

---

## Estructura de archivos de este punto

```
punto2-fuentes-datos/
├── rds/
│   ├── schema.sql        # DDL para crear las tablas en MariaDB
│   └── load_rds.py       # Script para cargar places.csv → RDS
├── ec2/
│   └── setup_ec2.sh      # Script para subir CSVs a EC2 via SCP
├── url/
│   └── fetch_url_source.py  # Verifica y descarga el dataset público
├── .env                  # ← NO subir a git (está en .gitignore)
└── README.md             # ← este archivo
```
