"""PCA con estandarización y loadings interpretables."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


@dataclass
class ResultadoPCA:
    scores: pd.DataFrame
    loadings: pd.DataFrame  # Correlaciones entre variables originales y PCs
    coeficientes: pd.DataFrame  # Eigenvectores (componentes de sklearn)
    eigenvalues: np.ndarray
    var_exp: np.ndarray
    var_acum: np.ndarray
    medias: pd.Series
    escalas: pd.Series
    columnas_descartadas: list
    modelo: PCA

    def variance_table(self):
        return pd.DataFrame({
            'autovalor': self.eigenvalues,
            'varianza_explicada': self.var_exp,
            'varianza_acumulada': self.var_acum,
        }, index=self.scores.columns).rename_axis('componente')


def estandarizar_datos(datos):
    """Devuelve (DataFrame z-score, scaler); elimina columnas constantes."""
    if datos.empty or len(datos) < 2:
        raise ValueError('Se necesitan al menos dos observaciones')
    if not all(pd.api.types.is_numeric_dtype(t) for t in datos.dtypes):
        raise TypeError('La matriz debe contener solo variables numéricas')
    valores = datos.to_numpy(dtype=float)
    if not np.isfinite(valores).all():
        raise ValueError('La matriz contiene NaN o infinitos')
    variables = datos.loc[:, datos.nunique(dropna=False) > 1]
    if variables.empty:
        raise ValueError('Todas las variables son constantes')
    scaler = StandardScaler()
    z = pd.DataFrame(scaler.fit_transform(variables), index=datos.index,
                     columns=variables.columns)
    return z, scaler


def run_pca(datos, n_components=None):
    """Estandariza y ajusta PCA. Por defecto calcula todas las PCs posibles."""
    z, scaler = estandarizar_datos(datos)
    modelo = PCA(n_components=n_components)
    puntuaciones = modelo.fit_transform(z)
    nombres = [f'PC{i}' for i in range(1, puntuaciones.shape[1] + 1)]
    scores = pd.DataFrame(puntuaciones, index=datos.index, columns=nombres)
    coef = pd.DataFrame(modelo.components_.T, index=z.columns, columns=nombres)
    # Corr(X_estandarizada, PC) = eigenvector * sqrt(autovalor)
    loadings = coef.mul(np.sqrt(modelo.explained_variance_), axis=1)
    return ResultadoPCA(
        scores=scores, loadings=loadings, coeficientes=coef,
        eigenvalues=modelo.explained_variance_,
        var_exp=modelo.explained_variance_ratio_,
        var_acum=np.cumsum(modelo.explained_variance_ratio_),
        medias=pd.Series(scaler.mean_, index=z.columns),
        escalas=pd.Series(scaler.scale_, index=z.columns),
        columnas_descartadas=list(datos.columns.difference(z.columns)),
        modelo=modelo,
    )


def principales_loadings(resultado, componente='PC1', n=10):
    """Variables más asociadas a una componente, ordenadas por magnitud."""
    serie = resultado.loadings[componente]
    return serie.loc[serie.abs().sort_values(ascending=False).index].head(n)


def observaciones_extremas(resultado, n=10):
    """Eventos más alejados del origen en el plano PC1-PC2."""
    if resultado.scores.shape[1] < 2:
        raise ValueError('El PCA necesita al menos dos componentes')
    tabla = resultado.scores[['PC1', 'PC2']].copy()
    tabla['distancia_origen'] = np.hypot(tabla.PC1, tabla.PC2)
    return tabla.nlargest(n, 'distancia_origen')
