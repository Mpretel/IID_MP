"""Detección de eventos atípicos multivariantes sobre las componentes principales."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

RANDOM_STATE = 42


def center_distance(scores: pd.DataFrame) -> pd.Series:
    """Distancia euclídea de cada evento al centro de las componentes.

    Las coordenadas del ACP ya están centradas (media 0 en cada componente),
    así que la distancia al centro es la norma del vector de coordenadas.
    """
    centered = scores - scores.mean()
    return pd.Series(np.linalg.norm(centered.to_numpy(), axis=1), index=scores.index, name="distancia_centro")


def tukey_upper_fence(values: pd.Series, k: float = 2.0) -> float:
    """Límite superior de Tukey: Q3 + k·IQR.

    Para una distancia (siempre >= 0) sólo importa el límite superior: el
    inferior, Q1 − k·IQR, queda por debajo de 0.
    """
    q1, q3 = values.quantile([0.25, 0.75])
    return float(q3 + k * (q3 - q1))


def isolation_forest(scores: pd.DataFrame, contamination: float = 0.01) -> tuple[pd.Series, pd.Series]:
    """Isolation Forest sobre las coordenadas de los eventos.

    Returns
    -------
    flag : pd.Series
        1 si el evento es atípico (la proporción ``contamination`` más aislada).
    score : pd.Series
        Puntaje de anomalía: mayor = se aísla con menos cortes al azar.
    """
    model = IsolationForest(n_estimators=100, contamination=contamination, random_state=RANDOM_STATE)
    model.fit(scores)
    flag = pd.Series((model.predict(scores) == -1).astype(int), index=scores.index, name="atipico_iforest")
    score = pd.Series(-model.score_samples(scores), index=scores.index, name="puntaje_iforest")
    return flag, score


# Columnas de la OBT que describen a cada atípico, con su nombre en la tabla exportada.
DESCRIPTIVE_COLUMNS = {
    "FechaEvento": "fecha",
    "Actor1Name": "actor_1",
    "Actor1Type1Code_Desc": "tipo_actor_1",
    "Actor2Name": "actor_2",
    "Actor2Type1Code_Desc": "tipo_actor_2",
    "EventRootCode_Desc": "tipo_evento",
    "EventCode_Desc": "evento",
    "ActionGeo_CountryCode_Desc": "pais",
    "ActionGeo_FullName": "lugar",
    "AvgTone": "tono",
    "GoldsteinScale": "goldstein",
    "NumMentions": "menciones",
    "NumSources": "fuentes",
    "SOURCEURL": "url",
}


def outlier_table(
    outliers: pd.DataFrame,
    obt: pd.DataFrame,
    age: pd.Series,
    sort_by: str = "puntaje_iforest",
) -> pd.DataFrame:
    """Tabla de atípicos legible: descripciones de la OBT, antigüedad y puntajes.

    ``outliers`` tiene los puntajes de los métodos, indexado por
    ``GLOBALEVENTID``; ``obt`` también tiene que estar indexada así.
    ``atipicos_misma_url`` cuenta cuántos atípicos salen de la misma nota.
    """
    table = obt.loc[outliers.index, list(DESCRIPTIVE_COLUMNS)].rename(columns=DESCRIPTIVE_COLUMNS)
    table.insert(table.columns.get_loc("url"), "antiguedad_dias", age.loc[outliers.index])
    table["distancia_centro"] = outliers["distancia_centro"]
    table["puntaje_iforest"] = outliers["puntaje_iforest"]
    table["atipicos_misma_url"] = table.groupby("url")["url"].transform("size")
    return table.sort_values(sort_by, ascending=False).reset_index()


def overlap_table(flag_a: pd.Series, flag_b: pd.Series, name_a: str, name_b: str) -> pd.DataFrame:
    """Tabla de 2 × 2 con cuántos eventos marca cada método y cuántos ambos."""
    table = pd.crosstab(
        flag_a.map({1: "atípico", 0: "normal"}).rename(name_a),
        flag_b.map({1: "atípico", 0: "normal"}).rename(name_b),
        margins=True,
        margins_name="total",
    )
    return table.loc[["atípico", "normal", "total"], ["atípico", "normal", "total"]]
