"""Carga y preprocesamiento del Cardiotocography dataset."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler, StandardScaler

from .config import (
    DATA_URL,
    FEATURES,
    RATE_FACTOR,
    RATE_FEATURES,
    RAW_CSV,
    SKEWED_FEATURES,
    TARGET,
)


def load_ctg(csv_path: str | Path = RAW_CSV, url: str = DATA_URL) -> tuple[pd.DataFrame, pd.Series]:
    """Carga el dataset y devuelve las variables y la etiqueta de anomalía.

    La primera vez descarga el CSV de UCI y lo guarda en ``csv_path``; las
    siguientes lo lee del disco.

    Returns
    -------
    X : pd.DataFrame
        Las 21 variables del CTG (``FEATURES``).
    y : pd.Series
        1 si el CTG no es normal (``NSP`` sospechoso o patológico), 0 si es normal.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        pd.read_csv(url).to_csv(csv_path, index=False)
    ctg = pd.read_csv(csv_path)
    return ctg[FEATURES], (ctg[TARGET] > 1).astype(int).rename("anomalia")


def robust_scale(X: pd.DataFrame) -> pd.DataFrame:
    """Escalado del notebook de clase: (x - mediana) / IQR."""
    return pd.DataFrame(RobustScaler().fit_transform(X), columns=X.columns, index=X.index)


def log_standardize(X: pd.DataFrame) -> pd.DataFrame:
    """log(1 + x) en las variables sesgadas y luego z-score en todas.

    Con ``RobustScaler``, una variable con mediana 0 y cola larga (como ``FM``,
    movimientos fetales) llega a valores de más de 100 y domina cualquier
    distancia. El logaritmo comprime esas colas antes de estandarizar.
    """
    transformed = X.copy()
    for column in SKEWED_FEATURES:
        if column in transformed:
            factor = RATE_FACTOR if column in RATE_FEATURES else 1
            transformed[column] = np.log1p(transformed[column] * factor)
    return pd.DataFrame(
        StandardScaler().fit_transform(transformed), columns=X.columns, index=X.index
    )
