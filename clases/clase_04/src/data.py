"""Carga del Wine recognition dataset.

scikit-learn trae el dataset empaquetado (``load_wine``), por lo que no hace
falta descargar nada: se arma el DataFrame y se guarda una copia en CSV.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.datasets import load_wine

from .config import CLASS_NAMES, DUMMY_COLUMNS, FEATURES, RAW_CSV, TARGET


def load_wine_df(csv_path: str | Path | None = RAW_CSV) -> pd.DataFrame:
    """Carga el dataset Wine como DataFrame, con el cultivar como categoría.

    Parameters
    ----------
    csv_path : str | Path | None
        Dónde guardar una copia cruda en CSV (por defecto ``data/raw/wine.csv``).
        Con ``None`` no se guarda nada.

    Returns
    -------
    pd.DataFrame
        178 filas: las 13 variables químicas (``FEATURES``) más la columna
        ``cultivar`` (``class_0``, ``class_1``, ``class_2``).
    """
    raw = load_wine()
    wine = pd.DataFrame(raw.data, columns=FEATURES)
    wine[TARGET] = pd.Categorical.from_codes(raw.target, CLASS_NAMES)

    if csv_path is not None:
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        wine.to_csv(csv_path, index=False)
    return wine


def add_class_dummies(wine: pd.DataFrame) -> pd.DataFrame:
    """Agrega las variables indicadoras (0/1) del cultivar.

    Devuelve una copia con las columnas ``DUMMY_COLUMNS``: ``x_class_0`` vale 1
    si el vino es de ``class_0`` y 0 si no, e ídem ``x_class_1``.
    """
    coded = wine.copy()
    for column in DUMMY_COLUMNS:
        coded[column] = (coded[TARGET] == column.removeprefix("x_")).astype(int)
    return coded
