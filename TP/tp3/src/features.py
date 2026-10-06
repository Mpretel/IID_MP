"""Preparación de la matriz de datos: limpieza, cardinalidad e indicadoras."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    CATEGORICAL,
    CONTINUOUS,
    MIN_CATEGORY_SHARE,
    OTHER_LABEL,
)

# Métricas de cobertura del hecho -> variable continua en escala log.
_LOG_COLUMNS = {
    "num_menciones": "log_menciones",
    "num_fuentes": "log_fuentes",
    "num_articulos": "log_articulos",
}


def build_events(joined: pd.DataFrame) -> pd.DataFrame:
    """Prepara la tabla de eventos del análisis a partir del almacén.

    ``joined`` es el resultado de ``warehouse.ANALYSIS_QUERY``: una fila por
    evento con los atributos de las dimensiones ya resueltos. Acá sólo se
    convierte la fecha y se pasan las métricas de cobertura a escala
    ``log(1 + x)``: son conteos con cola larga a la derecha.
    """
    events = joined.assign(fecha=pd.to_datetime(joined["fecha"]))
    for column, log_column in _LOG_COLUMNS.items():
        events[log_column] = np.log1p(events[column])
    return events.drop(columns=list(_LOG_COLUMNS)).reset_index(drop=True)


def reduce_cardinality(
    events: pd.DataFrame,
    columns: list[str] = CATEGORICAL,
    min_share: float = MIN_CATEGORY_SHARE,
    other_label: str = OTHER_LABEL,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Agrupa en ``other_label`` las categorías con frecuencia < ``min_share``.

    Returns
    -------
    reduced : pd.DataFrame
        Copia de ``events`` con las columnas ``columns`` ya agrupadas.
    summary : pd.DataFrame
        Una fila por variable: categorías originales, categorías que se
        conservan, cuántas se agruparon y qué proporción de los eventos
        quedó en ``other_label``.
    """
    reduced = events.copy()
    rows = []
    for column in columns:
        shares = reduced[column].value_counts(normalize=True)
        rare = shares.index[shares < min_share]
        reduced[column] = reduced[column].where(~reduced[column].isin(rare), other_label)
        rows.append(
            {
                "variable": column,
                "categorias_originales": len(shares),
                "categorias_conservadas": len(shares) - len(rare),
                "categorias_agrupadas": len(rare),
                "proporcion_other": shares[rare].sum(),
            }
        )
    return reduced, pd.DataFrame(rows).set_index("variable")


def reference_category(values: pd.Series, other_label: str = OTHER_LABEL) -> str:
    """Categoría de referencia (la indicadora que se omite).

    ``other_label`` si la variable la tiene -es la menos interpretable-; si
    no, la categoría más frecuente.
    """
    if (values == other_label).any():
        return other_label
    return values.value_counts().index[0]


def encode_dummies(
    events: pd.DataFrame,
    columns: list[str] = CATEGORICAL,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Codifica ``columns`` como variables indicadoras (0/1).

    Una variable con *k* categorías se codifica con *k - 1* indicadoras: la
    de la categoría de referencia (ver :func:`reference_category`) se omite
    porque es combinación lineal de las demás (todas suman 1). Las columnas
    se llaman ``<variable>_<categoría>``.

    Returns
    -------
    dummies : pd.DataFrame
        Las indicadoras, con el mismo índice que ``events``.
    references : dict[str, str]
        Categoría de referencia de cada variable.
    """
    blocks = []
    references = {}
    for column in columns:
        reference = reference_category(events[column])
        references[column] = reference
        block = pd.get_dummies(events[column], prefix=column, prefix_sep="_", dtype="int8")
        blocks.append(block.drop(columns=f"{column}_{reference}"))
    return pd.concat(blocks, axis=1), references


def build_matrix(
    events: pd.DataFrame,
    dummies: pd.DataFrame,
    continuous: list[str] = CONTINUOUS,
) -> pd.DataFrame:
    """Matriz de datos: variables continuas + indicadoras, indexada por evento."""
    matrix = pd.concat([events[continuous], dummies], axis=1)
    matrix.index = events["evento_id"]
    return matrix
