"""Perfil de calidad de los datos: nulos, ceros y strings vacíos por columna."""

from __future__ import annotations

import pandas as pd


def missing_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Tipo y porcentaje de nulos, ceros y strings vacíos de cada columna.

    - **% nulos:** valores ``NaN``/``NA``/``NaT``.
    - **% ceros:** sólo en columnas numéricas; en las demás queda ``NaN``.
    - **% strings vacíos:** sólo en columnas de texto; cuenta los strings
      vacíos o con sólo espacios. En las demás queda ``NaN``.

    Los porcentajes son sobre el total de filas.
    """
    rows = {}
    for column in df.columns:
        values = df[column]
        is_numeric = pd.api.types.is_numeric_dtype(values)
        is_text = pd.api.types.is_string_dtype(values) or values.dtype == object
        rows[column] = {
            "tipo": str(values.dtype),
            "% nulos": values.isna().mean() * 100,
            "% ceros": (values == 0).mean() * 100 if is_numeric else float("nan"),
            "% strings vacíos": (
                values.astype("string").str.strip().eq("").fillna(False).mean() * 100
                if is_text else float("nan")
            ),
        }
    profile = pd.DataFrame.from_dict(rows, orient="index")
    profile.index.name = "columna"
    return profile
