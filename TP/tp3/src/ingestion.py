from pathlib import Path
from urllib.request import urlopen, urlretrieve
import pandas as pd
import zipfile
from src.gdelt_columns import GDELT_COLUMNS
import requests
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

MASTER_URL = (
    "https://data.gdeltproject.org/"
    "gdeltv2/masterfilelist.txt"
)

def obtener_url_eventos():
    """Busca la URL del último archivo de eventos."""

    ultima_url = None

    with urlopen(MASTER_URL, timeout=120) as respuesta:
        for linea in respuesta:
            texto = linea.decode("utf-8").strip()
            partes = texto.split()

            if len(partes) >= 3:
                url = partes[2]

                if url.endswith(".export.CSV.zip"):
                    ultima_url = url

    if ultima_url is None:
        raise RuntimeError(
            "No se encontraron archivos de eventos."
        )

    return ultima_url


def descargar_eventos(url=None):
    """
    Descarga un archivo ZIP de eventos GDELT.

    Si url es None, descarga el archivo más reciente.
    Si se proporciona una URL, descarga ese archivo.
    """

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if url is None:
        url = obtener_url_eventos()

    nombre = url.rsplit("/", 1)[-1]
    destino = RAW_DIR / nombre

    if not destino.exists():
        print("Descargando:", nombre)
        urlretrieve(url, destino)
    else:
        print("El archivo ya existe:", nombre)

    return destino

def leer_eventos(archivo_zip, nrows=5):
    """Lee eventos GDELT con nombres y tipos adecuados."""

    columnas_texto = [
        "Actor1Code",
        "Actor1CountryCode",
        "Actor2Code",
        "Actor2CountryCode",
        "EventCode",
        "EventBaseCode",
        "EventRootCode",
        "Actor1Geo_CountryCode",
        "Actor2Geo_CountryCode",
        "ActionGeo_CountryCode",
        "ActionGeo_ADM1Code",
        "DATEADDED",
    ]

    tipos = {
        columna: "string"
        for columna in columnas_texto
    }

    with zipfile.ZipFile(archivo_zip, "r") as zip_ref:

        nombre_csv = zip_ref.namelist()[0]

        with zip_ref.open(nombre_csv) as archivo:

            df = pd.read_csv(
                archivo,
                sep="\t",
                header=None,
                names=GDELT_COLUMNS,
                nrows=nrows,
                encoding="latin-1",
                dtype=tipos
            )

    return df

def listar_archivos_semana(fecha_inicio):

    """
    Devuelve las URLs de archivos GDELT Events
    correspondientes a siete días consecutivos.

    fecha_inicio: cadena YYYY-MM-DD
    """

    inicio = datetime.strptime(
        fecha_inicio,
        "%Y-%m-%d"
    )

    fin = inicio + timedelta(days=7)

    url_master = (
        "https://data.gdeltproject.org/"
        "gdeltv2/masterfilelist.txt"
    )

    respuesta = requests.get(
        url_master,
        timeout=120
    )

    respuesta.raise_for_status()

    archivos = []

    for linea in respuesta.text.splitlines():

        partes = linea.split()

        if len(partes) < 3:
            continue

        url = partes[2]

        # Solamente archivos de eventos
        if not url.endswith(".export.CSV.zip"):
            continue

        nombre = url.rsplit("/", 1)[-1]

        try:
            fecha_archivo = datetime.strptime(
                nombre[:14],
                "%Y%m%d%H%M%S"
            )
        except ValueError:
            continue

        if inicio <= fecha_archivo < fin:
            archivos.append(url)

    return sorted(set(archivos))