"""Limpieza de la OBT: ceros que en realidad son datos faltantes."""

from __future__ import annotations

import pandas as pd

# Columnas donde el 0 es un faltante codificado: "sin geografía".
GEO_TYPE_COLUMNS = ["Actor1Geo_Type", "Actor2Geo_Type", "ActionGeo_Type"]

# Variables continuas donde un 0 exacto no es una medición sino un valor por
# defecto (ver la distribución de AvgTone en el notebook).
ZERO_AS_MISSING = ["AvgTone"]


def zeros_to_null(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Devuelve una copia de ``df`` con los ceros de ``columns`` reemplazados por nulos."""
    cleaned = df.copy()
    for column in columns:
        cleaned[column] = cleaned[column].mask(cleaned[column] == 0)
    return cleaned


def null_counts(before: pd.DataFrame, after: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Cantidad y porcentaje de nulos de ``columns`` antes y después de un cambio."""
    table = pd.DataFrame({
        "nulos antes": before[columns].isna().sum(),
        "nulos después": after[columns].isna().sum(),
    })
    table["nulos agregados"] = table["nulos después"] - table["nulos antes"]
    table["% nulos después"] = table["nulos después"] / len(after) * 100
    table.index.name = "columna"
    return table
