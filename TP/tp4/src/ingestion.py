"""Descarga de los archivos de eventos de GDELT dentro de la ventana de tiempo."""

from __future__ import annotations

import io
import zipfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from .config import (
    EVENT_COLUMNS,
    EVENT_FILE_SUFFIX,
    EVENT_NUMERIC,
    EVENTS_RAW_DIR,
    MASTER_FILE_LIST_URL,
    WINDOW_DAYS,
    WINDOW_END,
)


def window_bounds(end: str = WINDOW_END, days: int = WINDOW_DAYS) -> tuple[str, str]:
    """Primer y último instante (``YYYYMMDDhhmmss``) de la ventana, inclusive.

    La ventana son ``days`` días que terminan en ``end``: con archivos cada
    15 minutos, el primero es ``end - days + 15 min``.
    """
    fin = datetime.strptime(end, "%Y%m%d%H%M%S")
    inicio = fin - timedelta(days=days) + timedelta(minutes=15)
    return inicio.strftime("%Y%m%d%H%M%S"), end


def iter_event_urls(start: str, end: str, session: requests.Session | None = None) -> Iterator[str]:
    """URLs de los archivos de eventos con instante entre ``start`` y ``end``.

    Recorre la lista maestra en streaming (tiene una línea por archivo
    publicado desde 2015) y descarta al vuelo las menciones, el GKG y los
    archivos fuera de la ventana.
    """
    client = session or requests
    with client.get(MASTER_FILE_LIST_URL, stream=True, timeout=120) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            parts = line.split() if line else []
            if len(parts) != 3 or not parts[2].endswith(EVENT_FILE_SUFFIX):
                continue
            if start <= Path(parts[2]).name[:14] <= end:
                yield parts[2]


def read_event_file(
    url: str,
    session: requests.Session | None = None,
    cache_dir: str | Path = EVENTS_RAW_DIR,
) -> pd.DataFrame | None:
    """Descarga (o lee del disco) un archivo de 15 minutos con sus 61 columnas.

    El ZIP se guarda en ``cache_dir`` y en ejecuciones siguientes se lee de
    ahí. Devuelve ``None`` si el archivo no existe en el servidor.
    """
    cache_path = Path(cache_dir) / Path(url).name
    if cache_path.exists():
        content = cache_path.read_bytes()
    else:
        response = (session or requests).get(url, timeout=60)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        content = response.content
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(content)

    # Todo se lee como texto y las numéricas se convierten después: pueden
    # venir vacías, y un entero vacío haría fallar a read_csv.
    with zipfile.ZipFile(io.BytesIO(content)) as zf, zf.open(zf.namelist()[0]) as f:
        events = pd.read_csv(f, sep="\t", header=None, names=EVENT_COLUMNS,
                             dtype="string", encoding="latin-1")
    for column, dtype in EVENT_NUMERIC.items():
        numeric = pd.to_numeric(events[column], errors="coerce")
        events[column] = numeric.astype("Float64" if dtype.startswith("float") else "Int64")
    return events


def download_events(
    start: str,
    end: str,
    max_workers: int = 8,
    show_progress: bool = True,
) -> tuple[pd.DataFrame, int]:
    """Descarga en paralelo todos los archivos de la ventana y los concatena.

    Returns
    -------
    events : pd.DataFrame
        Todos los eventos de la ventana, sin duplicados de ``GLOBALEVENTID``.
    n_files : int
        Cantidad de archivos de 15 minutos leídos.
    """
    session = requests.Session()
    urls = list(iter_event_urls(start, end, session=session))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        chunks = executor.map(lambda url: read_event_file(url, session=session), urls)
        if show_progress:
            chunks = tqdm(chunks, total=len(urls), desc="Archivos GDELT")
        frames = [chunk for chunk in chunks if chunk is not None]
    events = pd.concat(frames, ignore_index=True)
    # Un evento puede reaparecer en otro archivo si GDELT lo actualiza.
    events = events.drop_duplicates("GLOBALEVENTID", keep="first").reset_index(drop=True)
    return events, len(frames)
