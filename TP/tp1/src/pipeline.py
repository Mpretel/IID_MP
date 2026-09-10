"""Orquesta la descarga en paralelo y la agregación diaria de eventos GDELT."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from .aggregate import DailyAccumulator
from .config import DATA_RAW, START_DATE
from .fetch import fetch_event_file
from .master_list import date_from_url, filter_event_urls, iter_master_file_list


def build_daily_stats(
    start_date: str = START_DATE,
    cache_dir: str | Path | None = DATA_RAW,
    max_workers: int = 8,
    show_progress: bool = True,
) -> pd.DataFrame:
    """Calcula las métricas diarias de eventos GDELT desde ``start_date``.

    1. Recorre la lista maestra en streaming y se queda con las URLs de
       eventos (``.export.CSV.zip``) dentro del rango de fechas pedido.
    2. Descarga esos archivos en paralelo: la descarga es I/O-bound -la
       mayor parte del tiempo se espera a la red, no se usa CPU- así que
       varios workers concurrentes aceleran el total sin costo extra de
       memoria por sí solos.
    3. Agrega cada archivo apenas llega y lo descarta (ver
       :class:`~src.aggregate.DailyAccumulator`), procesando todo en
       batches de 15 minutos en vez de concatenar los eventos crudos de
       varios días en un único DataFrame gigante.
    """
    session = requests.Session()
    urls = list(filter_event_urls(iter_master_file_list(session=session), start_date))

    accumulator = DailyAccumulator()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(fetch_event_file, url, session=session, cache_dir=cache_dir): url
            for url in urls
        }
        completed = as_completed(future_to_url)
        if show_progress:
            completed = tqdm(completed, total=len(future_to_url), desc="Archivos GDELT")
        for future in completed:
            chunk = future.result()
            if chunk is not None and not chunk.empty:
                accumulator.update(date_from_url(future_to_url[future]), chunk)

    return accumulator.to_dataframe()
