"""Análisis de componentes principales sobre variables estandarizadas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


@dataclass
class PCAResult:
    """Resultado de un ACP.

    Attributes
    ----------
    scores : pd.DataFrame
        Coordenadas de cada evento en las componentes (``PC1``, ``PC2``...).
    eigenvalues : np.ndarray
        Autovalores: varianza de cada componente.
    var_exp : np.ndarray
        Proporción de la varianza total explicada por cada componente.
    loadings : pd.DataFrame
        Correlación entre cada variable (filas) y cada componente (columnas):
        el autovector escalado por la raíz de su autovalor.
    """

    scores: pd.DataFrame
    eigenvalues: np.ndarray
    var_exp: np.ndarray
    loadings: pd.DataFrame

    @property
    def cum_var_exp(self) -> np.ndarray:
        return np.cumsum(self.var_exp)

    def variance_table(self) -> pd.DataFrame:
        """Autovalor y varianza explicada (individual y acumulada) por componente."""
        return pd.DataFrame(
            {
                "autovalor": self.eigenvalues,
                "% varianza": self.var_exp * 100,
                "% varianza acumulada": self.cum_var_exp * 100,
            },
            index=pd.Index(self.scores.columns, name="componente"),
        )


def run_pca(data: pd.DataFrame) -> PCAResult:
    """Estandariza las columnas de ``data`` (z-score) y ajusta un ACP con todas las componentes.

    Estandarizar equivale a diagonalizar la matriz de correlación: cada
    variable aporta varianza 1, así que ninguna domina por su escala.
    """
    scaled = StandardScaler().fit_transform(data)
    pca = PCA().fit(scaled)
    components = [f"PC{i + 1}" for i in range(pca.n_components_)]
    return PCAResult(
        scores=pd.DataFrame(pca.transform(scaled), index=data.index, columns=components),
        eigenvalues=pca.explained_variance_,
        var_exp=pca.explained_variance_ratio_,
        loadings=pd.DataFrame(
            pca.components_.T * np.sqrt(pca.explained_variance_), index=data.columns, columns=components
        ),
    )


def elbow(eigenvalues: np.ndarray) -> int:
    """Componente donde está el codo del scree plot (contando desde 1).

    Es el punto de la curva de autovalores más alejado de la recta que une
    el primer autovalor con el último: hasta ahí la curva cae rápido, y a
    partir de ahí se aplana.
    """
    n = len(eigenvalues)
    x = np.arange(1, n + 1)
    x1, y1, x2, y2 = 1, eigenvalues[0], n, eigenvalues[-1]
    distance = np.abs((y2 - y1) * x - (x2 - x1) * eigenvalues + x2 * y1 - y2 * x1)
    return int(np.argmax(distance) + 1)


def retention_criteria(result: PCAResult, thresholds: tuple[float, ...] = (0.80, 0.90)) -> pd.DataFrame:
    """Cantidad de componentes que retiene cada criterio y la varianza que explican."""
    counts = {
        "Kaiser (autovalor > 1)": int((result.eigenvalues > 1).sum()),
        "Codo del scree plot": elbow(result.eigenvalues),
        **{
            f"{threshold:.0%} de varianza acumulada": int(np.argmax(result.cum_var_exp >= threshold) + 1)
            for threshold in thresholds
        },
    }
    table = pd.DataFrame({"componentes": counts})
    table["% varianza explicada"] = [result.cum_var_exp[k - 1] * 100 for k in table["componentes"]]
    table.index.name = "criterio"
    return table
