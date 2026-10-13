"""Métricas de detección contra la etiqueta de los obstetras (NSP)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score


def evaluate(y_true: pd.Series, y_pred: np.ndarray, score: np.ndarray | None = None) -> dict[str, float]:
    """Matriz de confusión, precisión, recall y ROC-AUC de un método.

    El ROC-AUC mide qué tan bien el puntaje ordena las anomalías por encima
    de los normales, sin depender del umbral: 0,5 es un orden al azar y 1 es
    perfecto. Si el método no tiene puntaje continuo (DBSCAN), queda en NaN.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        "Marcados": int(tp + fp),
        "TP": int(tp),
        "FP": int(fp),
        "FN": int(fn),
        "Precisión": tp / (tp + fp) if tp + fp else np.nan,
        "Recall": tp / (tp + fn) if tp + fn else np.nan,
        "ROC-AUC": roc_auc_score(y_true, score) if score is not None else np.nan,
    }
