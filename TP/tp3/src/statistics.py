"""Estadística descriptiva, distancias y correlaciones para GDELT."""
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform


def _validar_matriz(datos):
    if datos.empty:
        raise ValueError('La matriz de datos está vacía')
    if not all(pd.api.types.is_numeric_dtype(t) for t in datos.dtypes):
        raise TypeError('Todas las columnas deben ser numéricas')
    if not np.isfinite(datos.to_numpy(dtype=float)).all():
        raise ValueError('La matriz contiene NaN o infinitos')


def resumen_global(datos):
    """Media, desvío estándar muestral y cantidad de eventos por variable."""
    _validar_matriz(datos)
    return pd.DataFrame({'media': datos.mean(), 'desvio': datos.std(),
                         'n': datos.count()})


def vector_medias(datos):
    _validar_matriz(datos)
    return datos.mean()


def matriz_covarianza(datos):
    _validar_matriz(datos)
    return datos.cov()


def matriz_correlacion(datos):
    _validar_matriz(datos)
    return datos.corr()


def medias_por_pais(datos, paises, minimo_eventos=1, excluir_unknown=False):
    """Media de cada variable por país del evento; devuelve (medias, conteos).

    paises: Serie alineada por índice con datos, típicamente
    eventos.loc[datos.index, 'PaisEvento'].
    """
    _validar_matriz(datos)
    if minimo_eventos < 1:
        raise ValueError('minimo_eventos debe ser >= 1')
    if not datos.index.is_unique or not paises.index.is_unique:
        raise ValueError('Los índices deben ser únicos para alinear eventos')
    pais = paises.reindex(datos.index).astype('string').fillna('UNKNOWN')
    pais = pais.str.strip().replace('', 'UNKNOWN')
    if excluir_unknown:
        mascara = pais != 'UNKNOWN'
        datos, pais = datos.loc[mascara], pais.loc[mascara]
    conteos = pais.value_counts().rename('n_eventos')
    validos = conteos[conteos >= minimo_eventos].index
    medias = datos.groupby(pais).mean().reindex(validos)
    return medias, conteos.loc[validos]


def distancias_entre_paises(medias, metrica='euclidean', estandarizar=False):
    """Distancias entre vectores medios de países.

    estandarizar=True estandariza cada columna ENTRE países (no entre eventos).
    Para distancias comparables es recomendable utilizar la matriz de eventos
    estandarizada ANTES de calcular las medias por país.
    """
    _validar_matriz(medias)
    if len(medias) < 2:
        raise ValueError('Se necesitan al menos dos países')
    valores = medias.astype(float)
    if estandarizar:
        desvios = valores.std(ddof=0).replace(0, 1)
        valores = (valores - valores.mean()) / desvios
    d = squareform(pdist(valores.to_numpy(), metric=metrica))
    return pd.DataFrame(d, index=medias.index, columns=medias.index)


def correlaciones_por_pais(datos, paises, minimo_eventos=30):
    """Diccionario país -> matriz de correlación para grupos suficientes."""
    _validar_matriz(datos)
    if not datos.index.is_unique or not paises.index.is_unique:
        raise ValueError('Los índices deben ser únicos')
    pais = paises.reindex(datos.index).astype('string').fillna('UNKNOWN')
    return {str(nombre): grupo.corr() for nombre, grupo in datos.groupby(pais)
            if len(grupo) >= minimo_eventos}
