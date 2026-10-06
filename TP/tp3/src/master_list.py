"""Lectura y filtrado de la lista maestra de archivos de GDELT.

Igual que en el TP1: la lista maestra (``masterfilelist.txt``) tiene una
línea por archivo publicado desde 2015, con el formato
``<tamaño> <md5> <url>``. Se la recorre en streaming y se descartan al vuelo
las líneas que no correspondan a archivos de eventos de la muestra.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

import requests

from .config import END_DATE, EVENT_FILE_SUFFIX, MASTER_FILE_LIST_URL, SAMPLE_MINUTES, START_DATE


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


def timestamp_from_url(url: str) -> str:
    """Instante (``YYYYMMDDhhmmss``) embebido en el nombre del archivo."""
    return Path(url).name[:14]


def filter_event_urls(
    lines: Iterable[str],
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    minutes: tuple[str, ...] = SAMPLE_MINUTES,
) -> Iterator[str]:
    """Filtra las URLs de eventos de la muestra.

    Se queda con los archivos ``.export.CSV.zip`` con fecha entre
    ``start_date`` y ``end_date`` (inclusive, ``YYYYMMDD``) cuyo minuto esté
    en ``minutes`` (p. ej. ``("00",)`` = un archivo por hora).
    """
    for line in lines:
        url = _url_from_line(line)
        if url is None or not url.endswith(EVENT_FILE_SUFFIX):
            continue
        timestamp = timestamp_from_url(url)
        if start_date <= timestamp[:8] <= end_date and timestamp[10:12] in minutes:
            yield url
