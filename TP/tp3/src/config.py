"""Constantes y rutas del proyecto: URLs de GDELT, muestra y variables."""

from pathlib import Path

# --------------------------------------------------------------------------
# Rutas del repositorio
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = DATA_PROCESSED / "figures"

EVENTS_PARQUET = DATA_PROCESSED / "eventos.parquet"
WAREHOUSE_DB = DATA_PROCESSED / "almacen.sqlite"
MATRIX_PARQUET = DATA_PROCESSED / "matriz_datos.parquet"
FIPS_LOOKUP_TXT = DATA_RAW / "FIPS.country.txt"

# --------------------------------------------------------------------------
# GDELT 2.0
# --------------------------------------------------------------------------
MASTER_FILE_LIST_URL = "https://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
CODEBOOK_URL = "https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf"
CAMEO_MANUAL_URL = "https://gdeltproject.org/data/documentation/CAMEO.Manual.1.1b3.pdf"

# Tabla de códigos de país FIPS 10-4 (los que usa ``ActionGeo_CountryCode``)
# con su nombre.
FIPS_LOOKUP_URL = "https://www.gdeltproject.org/data/lookups/FIPS.country.txt"

EVENT_FILE_SUFFIX = ".export.CSV.zip"

# --------------------------------------------------------------------------
# Muestra
# --------------------------------------------------------------------------
# Una semana completa (lunes a domingo), para que todos los días de la semana
# pesen igual en la muestra. Rango cerrado, formato YYYYMMDD.
START_DATE = "20260928"
END_DATE = "20261004"

# De los 4 archivos de 15 minutos de cada hora se toma sólo el de hh:00 (un
# archivo por hora). Así la muestra cubre las 24 horas de los 7 días sin
# descargar los 672 archivos de la semana.
SAMPLE_MINUTES = ("00",)

# --------------------------------------------------------------------------
# Esquema de los eventos
# --------------------------------------------------------------------------
# Columnas leídas del archivo de eventos (61 columnas sin encabezado,
# separadas por tab; índices 0-indexados según el codebook de GDELT 2.0).
EVENT_COLUMNS = {
    0: "GLOBALEVENTID",
    1: "SQLDATE",
    5: "Actor1Code",
    12: "Actor1Type1Code",
    15: "Actor2Code",
    22: "Actor2Type1Code",
    26: "EventCode",
    27: "EventBaseCode",
    28: "EventRootCode",
    29: "QuadClass",
    30: "GoldsteinScale",
    31: "NumMentions",
    32: "NumSources",
    33: "NumArticles",
    34: "AvgTone",
    53: "ActionGeo_CountryCode",
}
EVENT_DTYPES = {
    "GLOBALEVENTID": "int64",
    "SQLDATE": "string",
    "Actor1Code": "string",
    "Actor1Type1Code": "string",
    "Actor2Code": "string",
    "Actor2Type1Code": "string",
    "EventCode": "string",
    "EventBaseCode": "string",
    "EventRootCode": "string",
    "QuadClass": "int8",
    "GoldsteinScale": "float64",
    "NumMentions": "int32",
    "NumSources": "int32",
    "NumArticles": "int32",
    "AvgTone": "float64",
    "ActionGeo_CountryCode": "string",
}

# --------------------------------------------------------------------------
# Variables del análisis
# --------------------------------------------------------------------------
# Variables continuas: el tono y el impacto de Goldstein que pide la
# consigna, más las 3 métricas de cobertura del hecho del TP2. Las de
# cobertura son conteos con cola larga a la derecha, por eso entran en
# escala log(1 + x) (ver ``features.build_events``).
CONTINUOUS_LABELS = {
    "goldstein": "Escala de Goldstein",
    "tono": "Tono promedio",
    "log_menciones": "log(1 + menciones)",
    "log_fuentes": "log(1 + fuentes)",
    "log_articulos": "log(1 + artículos)",
}
CONTINUOUS = list(CONTINUOUS_LABELS)

# Variables categóricas que se codifican como indicadoras.
CATEGORICAL_LABELS = {
    "actor1_categoria": "Categoría del actor 1",
    "actor2_categoria": "Categoría del actor 2",
    "interaccion": "Tipo de interacción (CAMEO raíz)",
    "region": "Región del evento",
}
CATEGORICAL = list(CATEGORICAL_LABELS)

# País donde ocurre el evento: no entra en la matriz, se usa para agrupar
# (vectores de medias por país).
COUNTRY = "pais"

# Etiquetas de valores faltantes en los actores: el actor no existe (evento
# con un solo actor) o existe pero CAMEO no le asignó un tipo (p. ej. un
# país o una persona sin rol identificado).
NO_ACTOR = "SIN_ACTOR"
NO_TYPE = "SIN_TIPO"

# Tipos CAMEO de actor (``Actor*Type1Code``) agrupados en la
# ``categoria_actor`` de ``DIM_ACTOR`` del TP2. Sin esta agrupación, con el
# umbral del 5% sólo sobrevive ``GOV`` y el resto de los tipos -policía,
# justicia, empresas, educación, etc.- termina mezclado en ``OTHER``.
# Un código que no figure acá conserva su código como categoría.
ACTOR_CATEGORIES = {
    "Estado y política": "GOV LEG JUD UIS OPP ELI",
    "Seguridad": "COP MIL SPY",
    "Grupos armados y crimen": "CRM UAF REB INS SEP RAD",
    "Economía": "BUS MNC AGR",
    "Sociedad civil": "CVL EDU MED HLH LAB REF HRI ENV SET IMG",
    "Organizaciones": "IGO NGO INT",
}
ACTOR_TYPE_TO_CATEGORY = {
    code: category for category, codes in ACTOR_CATEGORIES.items() for code in codes.split()
}

# Reducción de cardinalidad: las categorías con frecuencia relativa menor a
# este umbral se agrupan en ``OTHER_LABEL``.
MIN_CATEGORY_SHARE = 0.05
OTHER_LABEL = "OTHER"

# Clase general (QuadClass) de cada evento, según el codebook de GDELT.
QUAD_CLASS_LABELS = {
    1: "Cooperación verbal",
    2: "Cooperación material",
    3: "Conflicto verbal",
    4: "Conflicto material",
}

# Raíces CAMEO de acción (EventRootCode), según el manual CAMEO.
CAMEO_ROOT_LABELS = {
    "01": "Declaración pública",
    "02": "Apelar",
    "03": "Expresar intención de cooperar",
    "04": "Consultar",
    "05": "Cooperación diplomática",
    "06": "Cooperación material",
    "07": "Proveer ayuda",
    "08": "Ceder",
    "09": "Investigar",
    "10": "Exigir",
    "11": "Desaprobar",
    "12": "Rechazar",
    "13": "Amenazar",
    "14": "Protestar",
    "15": "Exhibir fuerza",
    "16": "Reducir relaciones",
    "17": "Coerción",
    "18": "Agresión",
    "19": "Combate",
    "20": "Violencia masiva no convencional",
}

# --------------------------------------------------------------------------
# Descripción multivariante
# --------------------------------------------------------------------------
# Cantidad de países (los de más eventos) para los vectores de medias y las
# correlaciones por país.
TOP_COUNTRIES = 10

# --------------------------------------------------------------------------
# Análisis de componentes principales
# --------------------------------------------------------------------------
# Variables de la matriz que no entran en el ACP: menciones y artículos
# tienen correlación 0,99 (miden lo mismo); con las dos, la cobertura
# pesaría doble. Se conserva menciones.
PCA_EXCLUDED = ["log_articulos"]

# --------------------------------------------------------------------------
# Estilo de los gráficos (el mismo de la clase 04)
# --------------------------------------------------------------------------
# Escala divergente para correlaciones y desvíos: azul (negativo) - gris -
# rojo (positivo).
DIVERGING_COLORS = ["#104281", "#2a78d6", "#f0efec", "#e34948", "#8f1f1f"]
# Escala secuencial (un solo tono, claro -> oscuro) para distancias.
SEQUENTIAL_COLORS = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
ACCENT = "#2a78d6"
# Segundo color, para resaltar observaciones (outliers) sobre el azul.
HIGHLIGHT = "#eb6834"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
