"""Descripción multivariante: vectores de medias, distancias y correlaciones."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

from .config import CAMEO_ROOT_LABELS, CATEGORICAL, CONTINUOUS_LABELS, COUNTRY, TOP_COUNTRIES

GLOBAL = "Global"

_PREFIX_LABELS = {
    "actor1_categoria_": "Actor 1: ",
    "actor2_categoria_": "Actor 2: ",
    "interaccion_": "Interacción: ",
    "region_": "Región: ",
}


def variable_label(column: str) -> str:
    """Etiqueta legible de una columna de la matriz de datos."""
    if column in CONTINUOUS_LABELS:
        return CONTINUOUS_LABELS[column]
    for prefix, label in _PREFIX_LABELS.items():
        if column.startswith(prefix):
            category = column.removeprefix(prefix)
            if prefix == "interaccion_":
                category = f"{category} {CAMEO_ROOT_LABELS.get(category, '')}".strip()
            return label + category
    return column


def source_variable(column: str) -> str:
    """Variable de la que sale una columna (la categórica, si es una indicadora)."""
    return next((v for v in CATEGORICAL if column.startswith(f"{v}_")), column)


def profile_columns(matrix: pd.DataFrame) -> list[str]:
    """Columnas del perfil del evento: todas menos las indicadoras de región.

    La región es función del país (cada país está en una sola región). Al
    comparar países, sus indicadoras sólo repiten la partición en regiones,
    y dentro de un país son constantes (su correlación no está definida).
    """
    return [c for c in matrix.columns if source_variable(c) != "region"]


def top_countries(events: pd.DataFrame, n: int = TOP_COUNTRIES) -> pd.Series:
    """Los ``n`` países con más eventos: código -> nombre."""
    codes = events[COUNTRY].value_counts().index[:n]
    names = events.drop_duplicates(COUNTRY).set_index(COUNTRY)["pais_nombre"]
    return names.loc[codes]


def mean_vectors(
    matrix: pd.DataFrame,
    countries: pd.Series,
    selected: pd.Series,
) -> pd.DataFrame:
    """Vector de medias global y de cada país de ``selected`` (código -> nombre).

    ``countries`` es el país de cada fila de ``matrix``. Devuelve una fila por
    vector (``Global`` primero, luego los países) y una columna por variable.
    La media de una indicadora es la proporción de eventos de esa categoría.
    """
    by_country = matrix.groupby(countries.to_numpy()).mean().loc[selected.index]
    by_country.index = selected.to_numpy()
    means = pd.concat([matrix.mean().rename(GLOBAL).to_frame().T, by_country])
    means.index.name = "vector"
    return means


def standardize_means(means: pd.DataFrame, matrix: pd.DataFrame) -> pd.DataFrame:
    """Expresa cada media en desvíos estándar globales respecto de la media global.

    Sin esto, la distancia la dominan las variables de mayor escala (el tono
    y Goldstein varían en unidades; las proporciones, en centésimas).
    """
    return (means - matrix.mean()) / matrix.std()


def distance_matrix(
    means: pd.DataFrame,
    matrix: pd.DataFrame,
    metric: str = "euclidean",
) -> pd.DataFrame:
    """Distancias entre todos los vectores de medias (global y países).

    - ``"euclidean"``: euclídea sobre las medias estandarizadas
      (:func:`standardize_means`), es decir, en desvíos estándar globales.
    - ``"mahalanobis"``: usa la covarianza global de las observaciones, así
      que además descuenta la redundancia entre variables correlacionadas
      (p. ej. menciones y artículos, que miden casi lo mismo).
    """
    if metric == "euclidean":
        values = standardize_means(means, matrix).to_numpy()
        distances = cdist(values, values, metric="euclidean")
    elif metric == "mahalanobis":
        inverse = np.linalg.pinv(np.cov(matrix.to_numpy(dtype=float), rowvar=False))
        values = means.to_numpy(dtype=float)
        distances = cdist(values, values, metric="mahalanobis", VI=inverse)
    else:
        raise ValueError(f"Métrica desconocida: {metric}")
    return pd.DataFrame(distances, index=means.index, columns=means.index)


def country_correlations(
    matrix: pd.DataFrame,
    countries: pd.Series,
    selected: pd.Series,
) -> dict[str, pd.DataFrame]:
    """Matriz de correlación de Pearson de cada país de ``selected``, por nombre."""
    return {
        name: matrix[(countries == code).to_numpy()].corr() for code, name in selected.items()
    }


def correlation_pairs(corr: pd.DataFrame) -> pd.DataFrame:
    """Pares de variables de una matriz de correlación, de mayor a menor |r|.

    Se excluyen los pares de indicadoras de una misma variable categórica:
    son mutuamente excluyentes (un evento tiene una sola categoría), así que
    su correlación es negativa por construcción y no dice nada de los datos.
    """
    upper = np.triu(np.ones(corr.shape, dtype=bool), k=1)
    pairs = corr.where(upper).stack().rename("r").reset_index()
    pairs.columns = ["variable_1", "variable_2", "r"]
    source_1 = pairs["variable_1"].map(source_variable)
    source_2 = pairs["variable_2"].map(source_variable)
    pairs = pairs[~((source_1 == source_2) & source_1.isin(CATEGORICAL))]
    order = pairs["r"].abs().sort_values(ascending=False).index
    return pairs.loc[order].reset_index(drop=True)


def pairs_by_country(
    pairs: pd.DataFrame,
    global_corr: pd.DataFrame,
    correlations: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Correlación de cada par de ``pairs`` a nivel global y en cada país.

    Una fila por par (``variable_1 ~ variable_2``, con etiquetas legibles) y
    una columna por vector (``Global`` y luego los países).
    """
    matrices = {GLOBAL: global_corr, **correlations}
    table = pd.DataFrame(
        {
            name: [corr.loc[a, b] for a, b in zip(pairs["variable_1"], pairs["variable_2"])]
            for name, corr in matrices.items()
        }
    )
    table.index = pairs["variable_1"].map(variable_label) + " ~ " + pairs["variable_2"].map(variable_label)
    return table


def correlation_distance(correlations: dict[str, pd.DataFrame], global_corr: pd.DataFrame) -> pd.Series:
    """Cuánto difiere la matriz de correlación de cada país de la global.

    Raíz del promedio de las diferencias al cuadrado entre correlaciones
    (triángulo inferior, sin la diagonal): una diferencia "típica" de *r*.
    """
    lower = np.tril(np.ones(global_corr.shape, dtype=bool), k=-1)
    return pd.Series(
        {
            name: float(np.sqrt(np.mean((corr.to_numpy() - global_corr.to_numpy())[lower] ** 2)))
            for name, corr in correlations.items()
        },
        name="diferencia_rms",
    ).sort_values()
