"""Puntajes de anomalía: métodos del notebook de clase, propuestos y de PyOD.

Cada función devuelve un puntaje por registro, donde un valor más alto indica
un registro más anómalo. Los umbrales se aplican aparte (``flag_top`` y las
reglas de ``class_methods``).
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from pyod.models.abod import ABOD
from pyod.models.cof import COF
from pyod.models.copod import COPOD
from pyod.models.ecod import ECOD
from pyod.models.hbos import HBOS
from pyod.models.loda import LODA
from pyod.models.sod import SOD
from scipy.stats import zscore
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors

from .config import CONTAMINATION, RANDOM_STATE, RISK_DIRECTION


def flag_top(score: np.ndarray, rate: float = CONTAMINATION) -> np.ndarray:
    """Marca como anomalía la proporción ``rate`` de registros con mayor puntaje."""
    return (score >= np.quantile(score, 1 - rate)).astype(int)


# --------------------------------------------------------------------------
# Puntajes
# --------------------------------------------------------------------------
def center_distance(Z: pd.DataFrame) -> np.ndarray:
    """Distancia euclídea de cada registro al vector de medias."""
    return np.linalg.norm(Z - Z.mean(axis=0), axis=1)


def risk_contributions(Z: pd.DataFrame, directions: dict[str, int] = RISK_DIRECTION) -> pd.DataFrame:
    """Desvío de riesgo de cada registro en cada variable (siempre >= 0).

    Para cada variable con dirección +1 sólo cuentan los z positivos, con -1
    sólo los negativos (cambiados de signo), y con 0 cuenta el desvío en
    cualquier sentido. Los desvíos "hacia lo sano" quedan en 0.

    ``Z`` tiene que estar estandarizada (media 0) y tener las columnas de
    ``directions``.
    """
    return pd.DataFrame(
        {
            column: Z[column].abs() if sign == 0 else np.clip(sign * Z[column], 0, None)
            for column, sign in directions.items()
        },
        index=Z.index,
    )


def directional_distance(Z: pd.DataFrame, directions: dict[str, int] = RISK_DIRECTION) -> np.ndarray:
    """Distancia al centro contando sólo los desvíos en la dirección de riesgo.

    La distancia euclídea castiga cualquier desvío del centro, también los
    que van "hacia lo sano" (p. ej. más variabilidad que el promedio). Ésta
    es la norma euclídea de los desvíos de riesgo (:func:`risk_contributions`).
    """
    return np.linalg.norm(risk_contributions(Z, directions).to_numpy(), axis=1)


# Detectores de PyOD, con sus parámetros por defecto.
PYOD_MODELS = {
    # Distribución acumulada empírica de cada variable (Li et al., TKDE 2022).
    "ECOD": lambda: ECOD(),
    # Cópula empírica: misma idea que ECOD, con la dependencia entre variables
    # resumida por la cópula (Li et al., ICDM 2020).
    "COPOD": lambda: COPOD(),
    # Histograma por variable; asume independencia entre variables.
    "HBOS": lambda: HBOS(),
    # Varianza de los ángulos hacia los k vecinos (versión rápida, k = 10).
    "ABOD": lambda: ABOD(),
    # Desvío en el subespacio de ejes relevantes de sus vecinos compartidos.
    "SOD": lambda: SOD(),
    # Factor de conectividad: densidad medida sobre el camino a sus vecinos.
    "COF": lambda: COF(),
    # Ensamble de histogramas sobre proyecciones aleatorias.
    "LODA": lambda: LODA(random_state=RANDOM_STATE),
}


def pyod_score(name: str, X: pd.DataFrame) -> np.ndarray:
    """Puntaje de un detector de ``PYOD_MODELS`` (mayor = más anómalo).

    ABOD da ``NaN`` en los registros duplicados: con dos puntos idénticos, el
    vector entre ellos es nulo y el ángulo no está definido. Un registro con
    un duplicado exacto no está aislado, así que recibe el puntaje mínimo.
    """
    # SOD calcula varianzas sobre subespacios con muy pocos puntos y numpy
    # avisa "Degrees of freedom <= 0"; no afecta al puntaje.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        score = PYOD_MODELS[name]().fit(X.to_numpy(dtype=float)).decision_scores_
    return np.where(np.isnan(score), np.nanmin(score), score)


def kmeans_distance(Z: pd.DataFrame, k: int = 10) -> np.ndarray:
    """Distancia de cada registro al centroide de su grupo en k-means."""
    model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(Z)
    return np.linalg.norm(Z.to_numpy() - model.cluster_centers_[model.labels_], axis=1)


def knn_distance(Z: pd.DataFrame, k: int = 10) -> np.ndarray:
    """Distancia media a los ``k`` vecinos más cercanos."""
    distances, _ = NearestNeighbors(n_neighbors=k + 1).fit(Z).kneighbors(Z)
    return distances[:, 1:].mean(axis=1)


def lof_score(Z: pd.DataFrame, k: int = 10) -> np.ndarray:
    """Local Outlier Factor (valores mayores a 1: menos denso que sus vecinos)."""
    return -LocalOutlierFactor(n_neighbors=k).fit(Z).negative_outlier_factor_


def isolation_score(Z: pd.DataFrame, n_estimators: int = 100) -> np.ndarray:
    """Puntaje de Isolation Forest (mayor = se aísla con menos cortes)."""
    model = IsolationForest(n_estimators=n_estimators, random_state=RANDOM_STATE).fit(Z)
    return -model.score_samples(Z)


# --------------------------------------------------------------------------
# Métodos del notebook de clase, con sus umbrales originales
# --------------------------------------------------------------------------
def class_methods(Z: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray | None, str]]:
    """Reproduce los métodos de ``Cardiotocography outliers.ipynb``.

    Returns
    -------
    dict
        Nombre del método -> (predicción 0/1, puntaje o ``None``, umbral usado).
        DBSCAN no da un puntaje continuo, sólo la etiqueta de ruido.
    """
    distance = center_distance(Z)
    q1, q3 = np.percentile(distance, [25, 75])
    tukey_low, tukey_high = q1 - 2 * (q3 - q1), q3 + 2 * (q3 - q1)

    kmeans = kmeans_distance(Z)
    knn = knn_distance(Z)
    lof = LocalOutlierFactor(n_neighbors=10, contamination=CONTAMINATION)
    lof_pred = (lof.fit_predict(Z) == -1).astype(int)
    forest = IsolationForest(n_estimators=100, contamination=CONTAMINATION, random_state=RANDOM_STATE).fit(Z)
    dbscan = DBSCAN(eps=5, min_samples=5).fit_predict(Z)

    return {
        "Z-score de la distancia al centro": (
            (zscore(distance) > 3).astype(int), distance, "z > 3"),
        "Tukey fences sobre la distancia al centro": (
            ((distance < tukey_low) | (distance > tukey_high)).astype(int), distance, "Q3 + 2·IQR"),
        "k-means (k = 10), distancia al centroide": (
            (kmeans > np.percentile(kmeans, 99)).astype(int), kmeans, "percentil 99"),
        "k-NN (k = 10), distancia media": (
            (knn > np.percentile(knn, 99)).astype(int), knn, "percentil 99"),
        "DBSCAN (eps = 5, min_samples = 5)": (
            (dbscan == -1).astype(int), None, "puntos de ruido"),
        "LOF (k = 10)": (
            lof_pred, -lof.negative_outlier_factor_, "contaminación 5%"),
        "Isolation Forest": (
            (forest.predict(Z) == -1).astype(int), -forest.score_samples(Z), "contaminación 5%"),
    }
