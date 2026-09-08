"""Métricas de complejidad / entropía sobre épocas de EEG.

Se usa ``antropy``, que implementa las métricas estándar en la literatura de
complejidad de EEG de sueño.
"""

from __future__ import annotations

import antropy as ant
import numpy as np
import pandas as pd

from .config import STAGE_ORDER


def epoch_complexity(signal: np.ndarray, sfreq: float) -> dict[str, float]:
    """Calcula las métricas de complejidad para una época de EEG (vector 1D).

    Parameters
    ----------
    signal : np.ndarray
        Señal de la época, en muestras.
    sfreq : float
        Frecuencia de muestreo en Hz (necesaria para la entropía espectral).
    """
    return {
        "perm_entropy": ant.perm_entropy(signal, normalize=True),
        "sample_entropy": ant.sample_entropy(signal),
        "higuchi_fd": ant.higuchi_fd(signal),
        "spectral_entropy": ant.spectral_entropy(
            signal, sf=sfreq, method="welch", normalize=True
        ),
    }


def complexity_dataframe(epochs, channel: str | None = None) -> pd.DataFrame:
    """DataFrame con una fila por época: etapa de sueño + métricas de complejidad.

    Parameters
    ----------
    epochs : mne.Epochs
        Salida de :func:`src.preprocessing.make_epochs`.
    channel : str, optional
        Canal a analizar. Si es ``None`` se usa el primero (el pipeline deja
        un único canal EEG).
    """
    sfreq = epochs.info["sfreq"]
    ch_idx = 0 if channel is None else epochs.ch_names.index(channel)
    data = epochs.get_data(copy=False)[:, ch_idx, :]

    id_to_stage = {code: name for name, code in epochs.event_id.items()}

    rows = []
    for signal, code in zip(data, epochs.events[:, -1]):
        row = {"etapa": id_to_stage[code]}
        row.update(epoch_complexity(signal, sfreq))
        rows.append(row)

    return pd.DataFrame(rows)


def summarize_by_stage(df: pd.DataFrame) -> pd.DataFrame:
    """Complejidad promedio por etapa de sueño, en orden fisiológico.

    Típicamente se observa mayor complejidad en vigilia/REM y menor en sueño
    profundo (N3).
    """
    resumen = df.groupby("etapa").mean(numeric_only=True)
    orden = [s for s in STAGE_ORDER if s in resumen.index]
    return resumen.reindex(orden)
