"""Descarga en paralelo de la muestra de eventos GDELT."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from .config import DATA_RAW, END_DATE, EVENTS_PARQUET, START_DATE
from .fetch import fetch_event_file
from .master_list import filter_event_urls, iter_master_file_list


def download_sample(
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    cache_dir: str | Path | None = DATA_RAW,
    parquet_path: str | Path | None = EVENTS_PARQUET,
    max_workers: int = 8,
    show_progress: bool = True,
) -> pd.DataFrame:
    """Descarga los eventos de la muestra y los concatena en un DataFrame.

    A diferencia del TP1, acá sí se retienen los eventos individuales: el
    análisis multivariante trabaja sobre la matriz de observaciones. La
    muestra (un archivo por hora durante una semana, ver ``config``) son del
    orden de 10^5 eventos y entra holgada en memoria.

    Si ``parquet_path`` existe, se lee de ahí en vez de volver a recorrer la
    lista maestra; si no, el resultado se guarda ahí (con ``None`` no se lee
    ni se guarda nada).
    """
    parquet_path = Path(parquet_path) if parquet_path is not None else None
    if parquet_path is not None and parquet_path.exists():
        return pd.read_parquet(parquet_path)

    session = requests.Session()
    urls = list(filter_event_urls(iter_master_file_list(session=session), start_date, end_date))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        chunks = executor.map(
            lambda url: fetch_event_file(url, session=session, cache_dir=cache_dir), urls
        )
        if show_progress:
            chunks = tqdm(chunks, total=len(urls), desc="Archivos GDELT")
        events = pd.concat([c for c in chunks if c is not None], ignore_index=True)

    # Un mismo evento puede reaparecer en otro archivo si GDELT lo actualiza;
    # se conserva la primera aparición.
    events = events.drop_duplicates("GLOBALEVENTID", keep="first").reset_index(drop=True)

    if parquet_path is not None:
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        events.to_parquet(parquet_path, index=False)
    return events
