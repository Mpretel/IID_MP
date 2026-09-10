"""Constantes y rutas del proyecto: URLs de GDELT y esquema de los eventos."""

from pathlib import Path

# --------------------------------------------------------------------------
# Rutas del repositorio
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# --------------------------------------------------------------------------
# GDELT 2.0
# --------------------------------------------------------------------------
# Lista maestra de URLs, actualizada cada 15 minutos, con todos los archivos
# publicados desde 2015 (eventos, menciones y GKG).
MASTER_FILE_LIST_URL = "https://data.gdeltproject.org/gdeltv2/masterfilelist.txt"

# Documentación de referencia (codebook de eventos CAMEO y manual de campos).
CODEBOOK_URL = "https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf"
CAMEO_MANUAL_URL = "https://gdeltproject.org/data/documentation/CAMEO.Manual.1.1b3.pdf"

# Fecha desde la que se calculan las métricas diarias (consigna del TP).
START_DATE = "20260902"

# Sufijo que identifica los archivos de eventos dentro de la lista maestra
# (se ignoran los de menciones, ``.mentions.CSV.zip``, y GKG,
# ``.gkg.csv.zip``, que no hacen falta para este análisis).
EVENT_FILE_SUFFIX = ".export.CSV.zip"

# El archivo de eventos tiene 61 columnas sin encabezado, separadas por tab
# (formato GDELT 2.0, ver codebook). Para las métricas pedidas sólo hacen
# falta 2: los conteos de fuentes y artículos por evento (columnas 33 y 34,
# 1-indexadas). No hace falta leer la columna de fecha: todos los eventos de
# un mismo archivo de 15 minutos comparten el mismo DATEADDED -la fecha en
# que GDELT los registró-, que es justamente la fecha embebida en el nombre
# del archivo (ver ``master_list.date_from_url``). Leer sólo estas 2
# columnas -en vez de las 61- reduce mucho el uso de memoria y el tiempo de
# parseo de cada archivo.
EVENT_USECOLS = [32, 33]
EVENT_COLUMN_NAMES = ["NumSources", "NumArticles"]
EVENT_DTYPES = {
    "NumSources": "int32",
    "NumArticles": "int32",
}

# Los 61 nombres de columna completos del esquema de eventos GDELT 2.0, en
# orden. Se usan sólo con fines ilustrativos/exploratorios en el notebook
# (para mostrar cómo son los datos crudos); el pipeline de producción sólo
# lee las columnas de ``EVENT_USECOLS``.
EVENT_ALL_COLUMN_NAMES = [
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
