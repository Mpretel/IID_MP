"""Lectura y filtrado de la lista maestra de archivos de GDELT.

La lista maestra (``masterfilelist.txt``) tiene una línea por archivo
publicado desde 2015 -varios millones de líneas-, con el formato
``<tamaño> <md5> <url>``. Se la recorre en streaming, sin cargarla entera en
memoria, y se descartan al vuelo las líneas que no correspondan a archivos de
eventos dentro del rango de fechas pedido.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

import requests

from .config import EVENT_FILE_SUFFIX, MASTER_FILE_LIST_URL, START_DATE


def iter_master_file_list(
    url: str = MASTER_FILE_LIST_URL,
    session: requests.Session | None = None,
) -> Iterator[str]:
    """Recorre ``masterfilelist.txt`` línea por línea vía streaming HTTP."""
    client = session or requests
    with client.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if line:
                yield line


def _url_from_line(line: str) -> str | None:
    parts = line.split()
    if len(parts) != 3:
        return None
    return parts[2]


def date_from_url(url: str) -> str:
    """Fecha (``YYYYMMDD``) de ingesta a GDELT embebida en el nombre del archivo.

    Todos los eventos de un mismo archivo de 15 minutos fueron agregados a
    GDELT (``DATEADDED``) en ese mismo instante, así que esta fecha equivale
    a agrupar por ``DATEADDED`` sin necesidad de leer esa columna.
    """
    return Path(url).name[:8]


def filter_event_urls(
    lines: Iterable[str],
    start_date: str = START_DATE,
) -> Iterator[str]:
    """Filtra las URLs de archivos de eventos con fecha >= ``start_date``.

    Ignora los archivos de menciones y de GKG, y cualquier línea malformada.
    ``start_date`` tiene formato ``YYYYMMDD``, igual que el prefijo del
    nombre de archivo (p. ej. ``20260902000000.export.CSV.zip``).
    """
    for line in lines:
        url = _url_from_line(line)
        if url is None or not url.endswith(EVENT_FILE_SUFFIX):
            continue
        if date_from_url(url) >= start_date:
            yield url
