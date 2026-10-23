"""Constantes y rutas del proyecto: URLs de GDELT, ventana de tiempo y esquema."""

from pathlib import Path

# --------------------------------------------------------------------------
# Rutas del repositorio
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

EVENTS_RAW_DIR = DATA_RAW / "eventos"
LOOKUPS_DIR = DATA_RAW / "lookups"
OBT_PARQUET = DATA_PROCESSED / "obt_eventos.parquet"
MATRIX_PARQUET = DATA_PROCESSED / "matriz_datos.parquet"
OUTLIERS_PARQUET = DATA_PROCESSED / "eventos_atipicos.parquet"
OUTLIERS_CSV = DATA_PROCESSED / "eventos_atipicos.csv"
FIGURES_DIR = DATA_PROCESSED / "figures"

# --------------------------------------------------------------------------
# GDELT 2.0
# --------------------------------------------------------------------------
MASTER_FILE_LIST_URL = "https://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
EVENT_FILE_SUFFIX = ".export.CSV.zip"

# Tablas de códigos de GDELT (lookups), que funcionan como dimensiones.
LOOKUPS_URL = "https://www.gdeltproject.org/data/lookups/"
LOOKUP_FILES = {
    "eventos": "CAMEO.eventcodes.txt",
    "paises_cameo": "CAMEO.country.txt",
    "tipos_actor": "CAMEO.type.txt",
    "grupos_conocidos": "CAMEO.knowngroup.txt",
    "etnias": "CAMEO.ethnic.txt",
    "religiones": "CAMEO.religion.txt",
    "paises_fips": "FIPS.country.txt",
}

# --------------------------------------------------------------------------
# Ventana de tiempo
# --------------------------------------------------------------------------
# Los últimos 7 días al momento de la ingesta: la ventana termina en el último
# archivo publicado por GDELT (lastupdate.txt el 23/10/2026) y abarca los 7
# días anteriores, 4 archivos por hora. Queda fija para que el resultado sea
# reproducible: si se calculara al ejecutar, cada corrida bajaría otra semana.
WINDOW_END = "20261023151500"
WINDOW_DAYS = 7

# --------------------------------------------------------------------------
# Esquema de los eventos
# --------------------------------------------------------------------------
# Las 61 columnas del archivo de eventos de GDELT 2.0, en orden (codebook).
EVENT_COLUMNS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
    "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_ADM2Code", "Actor1Geo_Lat",
    "Actor1Geo_Long", "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_ADM2Code", "Actor2Geo_Lat",
    "Actor2Geo_Long", "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_ADM2Code", "ActionGeo_Lat",
    "ActionGeo_Long", "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]

# Columnas numéricas; el resto se lee como texto. Los códigos (EventCode,
# FeatureID, etc.) tienen que ser texto: "042" no es lo mismo que 42.
EVENT_NUMERIC = {
    "GLOBALEVENTID": "int64",
    "MonthYear": "int32",
    "Year": "int16",
    "FractionDate": "float64",
    "IsRootEvent": "int8",
    "QuadClass": "int8",
    "GoldsteinScale": "float64",
    "NumMentions": "int32",
    "NumSources": "int32",
    "NumArticles": "int32",
    "AvgTone": "float64",
    "Actor1Geo_Type": "int8",
    "Actor1Geo_Lat": "float64",
    "Actor1Geo_Long": "float64",
    "Actor2Geo_Type": "int8",
    "Actor2Geo_Lat": "float64",
    "Actor2Geo_Long": "float64",
    "ActionGeo_Type": "int8",
    "ActionGeo_Lat": "float64",
    "ActionGeo_Long": "float64",
}

# Etiquetas que no vienen en las tablas de códigos (codebook de GDELT 2.0).
QUAD_CLASS_LABELS = {
    1: "Cooperación verbal",
    2: "Cooperación material",
    3: "Conflicto verbal",
    4: "Conflicto material",
}
GEO_TYPE_LABELS = {
    1: "País",
    2: "Estado de EE. UU.",
    3: "Ciudad de EE. UU.",
    4: "Ciudad (fuera de EE. UU.)",
    5: "Provincia o estado (fuera de EE. UU.)",
}
