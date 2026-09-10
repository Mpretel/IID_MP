"""Descarga y parseo de un archivo de eventos de 15 minutos de GDELT."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from .config import EVENT_COLUMN_NAMES, EVENT_DTYPES, EVENT_USECOLS


def fetch_event_file(
    url: str,
    session: requests.Session | None = None,
    cache_dir: str | Path | None = None,
) -> pd.DataFrame | None:
    """Descarga un ``.export.CSV.zip`` y devuelve sólo las columnas necesarias.

    Si ``cache_dir`` está definido, el zip crudo se guarda ahí y en llamadas
    futuras se lee del disco en vez de volver a descargarlo (evita
    re-descargar todo al reejecutar el notebook).

    Devuelve ``None`` si el archivo no existe en el servidor (algunos
    intervalos pueden faltar, p. ej. por mantenimiento del lado de GDELT).
    """
    cache_path = Path(cache_dir) / Path(url).name if cache_dir is not None else None
    content: bytes | None = None
    if cache_path is not None and cache_path.exists():
        content = cache_path.read_bytes()

    if content is None:
        client = session or requests
        response = client.get(url, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        content = response.content
        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(content)

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        with zf.open(zf.namelist()[0]) as f:
            return pd.read_csv(
                f,
                sep="\t",
                header=None,
                usecols=EVENT_USECOLS,
                names=EVENT_COLUMN_NAMES,
                dtype=EVENT_DTYPES,
                encoding="latin-1",
            )
