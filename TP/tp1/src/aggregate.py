"""Agregación incremental de métricas diarias sobre los eventos de GDELT.

Se acumulan sumas por día -cantidad de eventos, artículos y fuentes- a
medida que llega cada archivo de 15 minutos, sin retener los eventos
individuales. Así el uso de memoria queda acotado por la cantidad de días
analizados y no por la cantidad de eventos (que en varios días puede ser de
millones). Cada archivo de 15 minutos corresponde a un único día (ver
``master_list.date_from_url``), así que sumar sus totales no requiere
``groupby``.
"""

from __future__ import annotations

from collections import Counter

import pandas as pd


class DailyAccumulator:
    """Acumulador de totales diarios, actualizable en batches."""

    def __init__(self) -> None:
        self.events: Counter[str] = Counter()
        self.articles: Counter[str] = Counter()
        self.sources: Counter[str] = Counter()

    def update(self, date: str, chunk: pd.DataFrame) -> None:
        """Suma los totales de un archivo de 15 minutos (``date``, ``YYYYMMDD``)."""
        self.events[date] += len(chunk)
        self.articles[date] += int(chunk["NumArticles"].sum())
        self.sources[date] += int(chunk["NumSources"].sum())

    def to_dataframe(self) -> pd.DataFrame:
        """Consolida los totales acumulados en las métricas diarias pedidas."""
        records = [
            {
                "fecha": pd.to_datetime(date, format="%Y%m%d"),
                "cantidad_eventos": n,
                "promedio_articulos_por_evento": self.articles[date] / n,
                "promedio_fuentes_por_evento": self.sources[date] / n,
            }
            for date, n in sorted(self.events.items())
        ]
        return pd.DataFrame.from_records(records).set_index("fecha")
