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
