"""Selección de variables y armado de la tabla de análisis."""

from __future__ import annotations

import pandas as pd

ID_COLUMN = "GLOBALEVENTID"
AGE_COLUMN = "AntiguedadDias"

NUMERIC = ["GoldsteinScale", "AvgTone", "NumMentions", "NumSources", "IsRootEvent", AGE_COLUMN]
CATEGORICAL = ["EventRootCode", "Actor1Type1Code", "Actor2Type1Code", "ActionGeo_CountryCode", "ActionGeo_Type"]

# Categorías explícitas para los nulos.
NO_ACTOR = "SIN_ACTOR"  # el evento no tiene ese actor
NO_TYPE = "SIN_TIPO"    # el actor existe, pero CAMEO no le asignó un tipo
NO_GEO = "SIN_GEO"      # el evento no tiene geografía

# Columnas excluidas del análisis, agrupadas por motivo. Se recorren en orden:
# cada columna queda con el primer motivo que le corresponde.
_EXCLUDED = [
    ("Identificador (se usa como índice)", [ID_COLUMN]),
    ("Fecha (la antigüedad la resume)", ["FechaEvento", "SQLDATE", "MonthYear", "Year", "FractionDate",
                                         "DATEADDED", "FechaAgregado"]),
    ("URL", ["SOURCEURL"]),
    ("Texto libre", ["Actor1Name", "Actor2Name", "Actor1Geo_FullName", "Actor2Geo_FullName",
                     "ActionGeo_FullName"]),
    ("Descripción de un código (redundante)", "_Desc"),
    ("Identificador geográfico (miles de valores)", ["Geo_FeatureID", "Geo_ADM1Code", "Geo_ADM2Code"]),
    ("Coordenada geográfica (la geografía entra con el país)", ["Geo_Lat", "Geo_Long"]),
    ("Código compuesto de actor (redundante con país y tipo)", ["Actor1Code", "Actor2Code"]),
    ("Nivel detallado de la jerarquía CAMEO (se usa la raíz)", ["EventCode", "EventBaseCode"]),
    ("Se deduce de otra variable (QuadClass de EventRootCode)", ["QuadClass"]),
    ("Muy correlacionada con otra (NumArticles ~ NumMentions)", ["NumArticles"]),
    ("Casi todos sus valores nulos (> 97%)", ["Type2Code", "Type3Code", "KnownGroupCode", "EthnicCode",
                                              "Religion1Code", "Religion2Code"]),
    ("Redundante con el país de la acción", ["Actor1CountryCode", "Actor2CountryCode",
                                             "Actor1Geo_CountryCode", "Actor2Geo_CountryCode"]),
    ("Redundante con la geografía de la acción", ["Actor1Geo_Type", "Actor2Geo_Type"]),
]


def _excluded_reason(column: str) -> str | None:
    for reason, patterns in _EXCLUDED:
        if isinstance(patterns, str):
            if column.endswith(patterns):
                return reason
        elif any(column == p or column.endswith(p) for p in patterns):
            return reason
    return None


def column_roles(columns: list[str]) -> pd.DataFrame:
    """Rol de cada columna de la OBT (numérica, categórica o excluida) y su motivo."""
    rows = []
    for column in columns:
        if column in NUMERIC:
            rows.append((column, "numérica", "Describe al evento"))
        elif column in CATEGORICAL:
            rows.append((column, "categórica", "Describe al evento"))
        else:
            rows.append((column, "excluida", _excluded_reason(column) or "Sin clasificar"))
    if AGE_COLUMN not in columns:
        rows.append((AGE_COLUMN, "numérica", "Derivada: FechaAgregado − FechaEvento, en días"))
    return pd.DataFrame(rows, columns=["columna", "rol", "motivo"]).set_index("columna")


def build_analysis_table(obt: pd.DataFrame) -> pd.DataFrame:
    """Tabla de análisis: numéricas y categóricas, indexada por ``GLOBALEVENTID``.

    - Descarta los eventos con ``AvgTone`` nulo (ceros exactos, ver la
      limpieza) y con ``GoldsteinScale`` nulo: GDELT asigna Goldstein según
      el código CAMEO, y esos eventos tienen un código que no existe en el
      manual, así que no hay de dónde imputarlo.
    - Agrega la antigüedad de la noticia: días entre la fecha del evento y
      el día en que GDELT lo registró.
    - Reemplaza los nulos de las categóricas por una categoría explícita:
      ``SIN_ACTOR`` / ``SIN_TIPO`` en los tipos de actor y ``SIN_GEO`` en la
      geografía de la acción.
    """
    events = obt.dropna(subset=["AvgTone", "GoldsteinScale"]).copy()
    events[AGE_COLUMN] = (events["FechaAgregado"].dt.normalize() - events["FechaEvento"]).dt.days

    for actor in ("Actor1", "Actor2"):
        type_column = f"{actor}Type1Code"
        events[type_column] = (
            events[type_column].fillna(NO_TYPE).where(events[f"{actor}Code"].notna(), NO_ACTOR)
        )
    events["ActionGeo_CountryCode"] = events["ActionGeo_CountryCode"].fillna(NO_GEO)
    events["ActionGeo_Type"] = events["ActionGeo_Type"].astype("string").fillna(NO_GEO)

    table = events.set_index(ID_COLUMN)[NUMERIC + CATEGORICAL]
    table[CATEGORICAL] = table[CATEGORICAL].astype("string")
    return table


OTHER_LABEL = "OTHER"


def reduce_cardinality(
    table: pd.DataFrame,
    columns: list[str] = CATEGORICAL,
    threshold: float = 0.05,
    other_label: str = OTHER_LABEL,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Agrupa en ``other_label`` las categorías con frecuencia menor a ``threshold``.

    La frecuencia se calcula sobre todas las filas de ``table``, con las
    categorías de nulos incluidas.

    Returns
    -------
    reduced : pd.DataFrame
        Copia de ``table`` con las categorías marginales agrupadas.
    summary : pd.DataFrame
        Por columna: cardinalidad antes y después (``OTHER`` incluida), el %
        de filas que quedó en ``OTHER`` y las categorías que se conservaron.
    """
    reduced = table.copy()
    rows = {}
    for column in columns:
        shares = table[column].value_counts(normalize=True)
        kept = shares.index[shares >= threshold]
        reduced[column] = table[column].where(table[column].isin(kept), other_label)
        rows[column] = {
            "categorías antes": len(shares),
            "categorías después": reduced[column].nunique(),
            "% filas en OTHER": (reduced[column] == other_label).mean() * 100,
            "categorías conservadas": ", ".join(kept),
        }
    summary = pd.DataFrame.from_dict(rows, orient="index")
    summary.index.name = "columna"
    return reduced, summary


def encode_dummies(
    table: pd.DataFrame,
    columns: list[str] = CATEGORICAL,
    reference: str = OTHER_LABEL,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Codifica ``columns`` como indicadoras 0/1, con *k − 1* por variable.

    Se omite la indicadora de ``reference`` (por defecto ``OTHER``): las
    indicadoras de una variable suman 1, así que una es combinación lineal de
    las demás. Cada indicadora se llama ``<variable>_<categoría>``.

    Returns
    -------
    dummies : pd.DataFrame
        Las indicadoras, con el mismo índice que ``table``.
    summary : pd.DataFrame
        Por variable: categorías, indicadoras generadas y categoría de referencia.
    """
    blocks, rows = [], {}
    for column in columns:
        block = pd.get_dummies(table[column], prefix=column, prefix_sep="_", dtype="int8")
        reference_column = f"{column}_{reference}"
        if reference_column not in block:
            raise ValueError(f"{column} no tiene la categoría de referencia {reference!r}")
        blocks.append(block.drop(columns=reference_column))
        rows[column] = {
            "categorías": block.shape[1],
            "indicadoras": block.shape[1] - 1,
            "categoría de referencia": reference,
        }
    summary = pd.DataFrame.from_dict(rows, orient="index")
    summary.index.name = "variable"
    return pd.concat(blocks, axis=1), summary


def build_matrix(table: pd.DataFrame, dummies: pd.DataFrame, numeric: list[str] = NUMERIC) -> pd.DataFrame:
    """Matriz de datos: numéricas + indicadoras, con el índice de ``table`` (GLOBALEVENTID)."""
    matrix = pd.concat([table[numeric].astype("float64"), dummies], axis=1)
    matrix.index.name = ID_COLUMN
    return matrix


def cardinality(table: pd.DataFrame, columns: list[str] = CATEGORICAL, threshold: float = 0.05) -> pd.DataFrame:
    """Cardinalidad de cada categórica, con las categorías de nulos incluidas.

    Las proporciones se calculan sobre todos los eventos de ``table``.
    """
    rows = {}
    for column in columns:
        shares = table[column].value_counts(normalize=True)
        rows[column] = {
            "categorías": len(shares),
            f"categorías >= {threshold:.0%}": int((shares >= threshold).sum()),
            f"% en categorías < {threshold:.0%}": shares[shares < threshold].sum() * 100,
            "categoría más frecuente": shares.index[0],
            "% más frecuente": shares.iloc[0] * 100,
        }
    result = pd.DataFrame.from_dict(rows, orient="index")
    result.index.name = "columna"
    return result
