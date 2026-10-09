# TP3 — Análisis multivariante de eventos GDELT 2.0

**Caso:** el equipo de Investigación & Ciencia de Datos de un medio
internacional de noticias necesita analizar el comportamiento multivariante
del ecosistema global de noticias. Continúa el TP2: se implementa en SQLite un
almacén de datos que incluye los actores 1 y 2, el tipo de interacción, la
región del evento, el tono y el impacto estimado por la escala de Goldstein, y
sobre él se hace el análisis multivariante.

**Preguntas de investigación:**

1. Perfil multivariante de eventos: vectores de medias.
2. Topología de cobertura mediática: distancias entre perfiles.
3. Estructura de correlación entre las variables de los eventos.
4. Compresión del ecosistema: cantidad de componentes principales e
   interpretación de sus cargas.

**Datos:** los 672 archivos de eventos de 15 minutos de la semana del 28/09 al
04/10/2026 (683.432 eventos).

## Almacén de datos

Esquema estrella en SQLite (`data/gdelt.db`):

| Tabla | Contenido |
|---|---|
| `Fact_Evento` | Una fila por evento (`GlobalEventID`): Goldstein, tono, menciones, fuentes y artículos |
| `Dim_Actor` | Nombre, país y tipo del actor; el hecho la referencia dos veces (`Actor1_ID`, `Actor2_ID`) |
| `Dim_Tiempo` | Fecha, día, mes, año y fin de semana |
| `Dim_Interaccion` | Código CAMEO del evento, base, raíz y `QuadClass` |
| `Dim_Geografia` | País, región (`ADM1`), nombre del lugar y coordenadas |
| `ETL_Archivos` | Registro de los archivos ya cargados (carga incremental) |
| `Vista_Eventos` | Vista que une el hecho con sus dimensiones para el análisis |

## Estructura

```
notebooks/
  TP3.ipynb          # notebook orquestador: ETL, almacén y análisis
src/
  database.py        # ruta de la base SQLite y conexión
  schema.py          # creación de las tablas y de Vista_Eventos
  gdelt_columns.py   # nombres de las 61 columnas de eventos de GDELT 2.0
  ingestion.py       # listado de archivos de la semana, descarga y lectura
  transform.py       # armado de las dimensiones y de la tabla de hechos
  load.py            # carga de dimensiones y hechos en SQLite
  queries.py         # consultas SQL que devuelven DataFrames
  seed.py            # datos ficticios de prueba (no se usa en el análisis)
  preprocessing.py   # agrupación en OTHER (< 5%), dummies y matriz de datos
  statistics.py      # vectores de medias, distancias y correlaciones
  pca_analysis.py    # estandarización, ACP, loadings y observaciones extremas
  visualization.py   # mapas de calor, scree plot, biplot y centroides
data/
  raw/               # ZIP de eventos descargados (ignorado por git)
  gdelt.db           # almacén SQLite (ignorado por git)
```

## Uso

```bash
pip install -r ../../requirements.txt
jupyter notebook notebooks/TP3.ipynb
```

La primera ejecución descarga y carga la semana completa. Las siguientes
omiten los archivos ya registrados en `ETL_Archivos`. `RECREAR_DB = True` borra
la base y empieza de cero.

## Recursos

- [Lista maestra de archivos (actualizada cada 15 min)](https://data.gdeltproject.org/gdeltv2/masterfilelist.txt)
- [Codebook de eventos GDELT 2.0](https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)
- [Manual de campos CAMEO](https://gdeltproject.org/data/documentation/CAMEO.Manual.1.1b3.pdf)
