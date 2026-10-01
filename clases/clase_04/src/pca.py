"""Análisis de componentes principales sobre variables estandarizadas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.feature_selection import f_classif
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


def rank_features_by_class(data: pd.DataFrame, classes: pd.Series) -> pd.Series:
    """Ordena las variables por cuánto separan a las clases (F de ANOVA).

    Devuelve el estadístico F de cada columna de ``data``, de mayor a menor.
    """
    f_values, _ = f_classif(data, classes)
    return pd.Series(f_values, index=data.columns, name="F").sort_values(
        ascending=False
    )
