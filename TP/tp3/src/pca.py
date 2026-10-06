"""Análisis de componentes principales sobre variables estandarizadas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import chi2
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


@dataclass
class PCAResult:
    """Resultado de un PCA.

    Attributes
    ----------
    scores : pd.DataFrame
        Coordenadas de cada observación en las componentes (``PC1``, ``PC2``...).
    eigenvalues : np.ndarray
        Autovalores: varianza de cada componente.
    var_exp : np.ndarray
        Proporción de varianza explicada por cada componente.
    loadings : pd.DataFrame
        Autovectores escalados por la raíz del autovalor: la correlación entre
        cada variable original (filas) y cada componente (columnas).
    """

    scores: pd.DataFrame
    eigenvalues: np.ndarray
    var_exp: np.ndarray
    loadings: pd.DataFrame

    @property
    def cum_var_exp(self) -> np.ndarray:
        return np.cumsum(self.var_exp)

    def variance_table(self) -> pd.DataFrame:
        """Tabla de autovalores y varianza explicada por componente."""
        return pd.DataFrame(
            {
                "autovalor": self.eigenvalues,
                "var_explicada": self.var_exp,
                "var_acumulada": self.cum_var_exp,
            },
            index=self.scores.columns,
        )


def run_pca(data: pd.DataFrame) -> PCAResult:
    """Corre un PCA sobre las columnas de ``data``, estandarizadas (z-score).

    Estandarizar equivale a diagonalizar la matriz de correlación en lugar de
    la de covarianza, así ninguna variable domina por su escala.
    """
    scaled = StandardScaler().fit_transform(data)
    pca = PCA()
    scores = pca.fit_transform(scaled)

    components = [f"PC{i + 1}" for i in range(pca.n_components_)]
    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    return PCAResult(
        scores=pd.DataFrame(scores, columns=components, index=data.index),
        eigenvalues=pca.explained_variance_,
        var_exp=pca.explained_variance_ratio_,
        loadings=pd.DataFrame(loadings, index=data.columns, columns=components),
    )


def parallel_analysis(
    data: pd.DataFrame,
    groups: pd.Series,
    n_iter: int = 20,
    quantile: float = 0.95,
    seed: int = 0,
) -> pd.DataFrame:
    """Análisis paralelo de Horn: autovalores esperados sin asociación entre variables.

    En cada iteración se permutan las filas de cada variable original por
    separado, lo que destruye la asociación entre variables pero conserva la
    distribución de cada una. ``groups`` indica a qué variable original
    pertenece cada columna de ``data``: las indicadoras de una misma
    categórica se permutan juntas, para conservar su estructura mecánica
    (son excluyentes y casi suman 1). Así el nulo incluye esa parte de la
    varianza, que no es asociación entre variables.

    Returns
    -------
    pd.DataFrame
        Por componente: el autovalor de los datos, la media y el cuantil
        ``quantile`` de los autovalores nulos, y el exceso del autovalor de
        los datos sobre ese cuantil.
    """
    values = data.to_numpy(dtype=float)
    blocks = [np.flatnonzero((groups == g).to_numpy()) for g in groups.unique()]
    rng = np.random.default_rng(seed)

    null = np.empty((n_iter, values.shape[1]))
    for i in range(n_iter):
        permuted = np.empty_like(values)
        for columns in blocks:
            permuted[:, columns] = values[rng.permutation(len(values))][:, columns]
        corr = np.corrcoef(permuted, rowvar=False)
        null[i] = np.sort(np.linalg.eigvalsh(corr))[::-1]

    eigenvalues = np.sort(np.linalg.eigvalsh(np.corrcoef(values, rowvar=False)))[::-1]
    threshold = np.quantile(null, quantile, axis=0)
    return pd.DataFrame(
        {
            "autovalor": eigenvalues,
            "nulo_media": null.mean(axis=0),
            f"nulo_p{quantile * 100:.0f}": threshold,
            "exceso": eigenvalues - threshold,
        },
        index=[f"PC{i + 1}" for i in range(len(eigenvalues))],
    )


def retention_criteria(result: PCAResult, parallel: pd.DataFrame) -> pd.Series:
    """Cantidad de componentes que retiene cada criterio habitual."""
    return pd.Series(
        {
            "Kaiser (autovalor > 1)": int((result.eigenvalues > 1).sum()),
            "70% de varianza acumulada": int(np.argmax(result.cum_var_exp >= 0.70) + 1),
            "80% de varianza acumulada": int(np.argmax(result.cum_var_exp >= 0.80) + 1),
            "Análisis paralelo (autovalor > nulo)": int(np.argmin(parallel["exceso"].to_numpy() > 0)),
        },
        name="componentes",
    )


def multivariate_outliers(
    result: PCAResult,
    n_components: int,
    alpha: float = 0.001,
) -> tuple[pd.Series, float]:
    """Distancia de Mahalanobis al cuadrado de cada observación en las primeras componentes.

    En el espacio de las componentes la distancia de Mahalanobis es la suma
    de los scores al cuadrado divididos por su autovalor. Bajo normalidad
    sigue una chi-cuadrado con ``n_components`` grados de libertad: es
    outlier la observación que supera el cuantil ``1 - alpha``.

    Returns
    -------
    d2 : pd.Series
        Distancia al cuadrado de cada observación.
    threshold : float
        Umbral de la chi-cuadrado.
    """
    scores = result.scores.iloc[:, :n_components]
    d2 = (scores**2 / result.eigenvalues[:n_components]).sum(axis=1).rename("d2")
    return d2, float(chi2.ppf(1 - alpha, n_components))
