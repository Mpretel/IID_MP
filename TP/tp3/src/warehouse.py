"""Almacén de datos en SQLite: esquema estrella a nivel evento.

Extiende el modelo dimensional simplificado del TP2 con lo que pide el TP3:
los dos actores (``dim_tipo_actor``, usada dos veces), el tipo de
interacción (``dim_cameo``), la región del evento (``dim_geografia``), el
tono y el impacto de Goldstein (métricas de ``fact_evento``).

El grano de la tabla de hechos es el evento (una fila por
``GLOBALEVENTID``), y no un agregado, porque el análisis multivariante
trabaja sobre las observaciones individuales.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .config import (
    ACTOR_TYPE_TO_CATEGORY,
    CAMEO_ROOT_LABELS,
    NO_ACTOR,
    NO_TYPE,
    QUAD_CLASS_LABELS,
    WAREHOUSE_DB,
)
from .regions import NO_REGION

SCHEMA = """
CREATE TABLE dim_tiempo (
    fecha_key        INTEGER PRIMARY KEY,  -- YYYYMMDD
    fecha            TEXT    NOT NULL,     -- ISO 8601
    anio             INTEGER NOT NULL,
    trimestre        INTEGER NOT NULL,
    mes              INTEGER NOT NULL,
    dia              INTEGER NOT NULL,
    dia_semana       INTEGER NOT NULL,     -- 1 = lunes ... 7 = domingo
    es_fin_de_semana INTEGER NOT NULL      -- 0 / 1
);

CREATE TABLE dim_geografia (
    geo_id      INTEGER PRIMARY KEY,
    pais_cod    TEXT NOT NULL UNIQUE,      -- FIPS 10-4 (ActionGeo_CountryCode)
    pais_nombre TEXT NOT NULL,
    region      TEXT NOT NULL              -- Banco Mundial
);

CREATE TABLE dim_tipo_actor (
    tipo_actor_id INTEGER PRIMARY KEY,
    tipo_cod      TEXT NOT NULL UNIQUE,    -- Actor*Type1Code, SIN_TIPO o SIN_ACTOR
    categoria     TEXT NOT NULL            -- agrupación para el análisis
);

CREATE TABLE dim_cameo (
    cameo_cod       TEXT PRIMARY KEY,      -- EventCode
    base_cod        TEXT NOT NULL,         -- EventBaseCode
    raiz_cod        TEXT NOT NULL,         -- EventRootCode
    raiz_desc       TEXT NOT NULL,
    quad_class      INTEGER NOT NULL,
    quad_class_desc TEXT NOT NULL
);

CREATE TABLE fact_evento (
    evento_id        INTEGER PRIMARY KEY,  -- GLOBALEVENTID
    fecha_key        INTEGER NOT NULL REFERENCES dim_tiempo (fecha_key),
    geo_id           INTEGER REFERENCES dim_geografia (geo_id),  -- NULL: sin país
    actor1_tipo_id   INTEGER NOT NULL REFERENCES dim_tipo_actor (tipo_actor_id),
    actor2_tipo_id   INTEGER NOT NULL REFERENCES dim_tipo_actor (tipo_actor_id),
    cameo_cod        TEXT    NOT NULL REFERENCES dim_cameo (cameo_cod),
    escala_goldstein REAL,
    tono_promedio    REAL,
    num_menciones    INTEGER NOT NULL,
    num_fuentes      INTEGER NOT NULL,
    num_articulos    INTEGER NOT NULL
);
"""

# Consulta que arma la tabla de eventos del análisis: el hecho con los
# atributos de sus dimensiones ya resueltos. El JOIN interno con
# dim_geografia descarta los eventos sin país de la acción.
ANALYSIS_QUERY = """
SELECT
    f.evento_id,
    t.fecha,
    g.pais_cod         AS pais,
    g.pais_nombre,
    g.region,
    a1.categoria       AS actor1_categoria,
    a2.categoria       AS actor2_categoria,
    c.raiz_cod         AS interaccion,
    f.escala_goldstein AS goldstein,
    f.tono_promedio    AS tono,
    f.num_menciones,
    f.num_fuentes,
    f.num_articulos
FROM fact_evento AS f
JOIN dim_tiempo     AS t  ON t.fecha_key      = f.fecha_key
JOIN dim_geografia  AS g  ON g.geo_id         = f.geo_id
JOIN dim_tipo_actor AS a1 ON a1.tipo_actor_id = f.actor1_tipo_id
JOIN dim_tipo_actor AS a2 ON a2.tipo_actor_id = f.actor2_tipo_id
JOIN dim_cameo      AS c  ON c.cameo_cod      = f.cameo_cod
WHERE f.escala_goldstein IS NOT NULL
  AND f.tono_promedio IS NOT NULL
ORDER BY f.evento_id
"""


def _actor_type_code(code: pd.Series, type_code: pd.Series) -> pd.Series:
    """Tipo CAMEO del actor, distinguiendo actor ausente de actor sin tipo."""
    return type_code.fillna(NO_TYPE).where(code.notna(), NO_ACTOR).astype(str)


def build_tables(raw: pd.DataFrame, fips_lookup: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Arma las dimensiones y la tabla de hechos a partir de los eventos crudos.

    Las claves sustitutas (``geo_id``, ``tipo_actor_id``) se numeran desde 1
    en orden alfabético del código natural.
    """
    dates = pd.to_datetime(raw["SQLDATE"].drop_duplicates(), format="%Y%m%d").sort_values()
    dim_tiempo = pd.DataFrame(
        {
            "fecha_key": dates.dt.strftime("%Y%m%d").astype(int),
            "fecha": dates.dt.strftime("%Y-%m-%d"),
            "anio": dates.dt.year,
            "trimestre": dates.dt.quarter,
            "mes": dates.dt.month,
            "dia": dates.dt.day,
            "dia_semana": dates.dt.dayofweek + 1,
            "es_fin_de_semana": (dates.dt.dayofweek >= 5).astype(int),
        }
    )

    countries = pd.Series(sorted(raw["ActionGeo_CountryCode"].dropna().unique()), dtype=str)
    dim_geografia = pd.DataFrame(
        {
            "geo_id": range(1, len(countries) + 1),
            "pais_cod": countries,
            "pais_nombre": countries.map(fips_lookup["nombre"]).fillna(countries),
            "region": countries.map(fips_lookup["region"]).fillna(NO_REGION),
        }
    )

    actor1 = _actor_type_code(raw["Actor1Code"], raw["Actor1Type1Code"])
    actor2 = _actor_type_code(raw["Actor2Code"], raw["Actor2Type1Code"])
    types = pd.Series(sorted(set(actor1) | set(actor2)), dtype=str)
    dim_tipo_actor = pd.DataFrame(
        {
            "tipo_actor_id": range(1, len(types) + 1),
            "tipo_cod": types,
            # Un tipo sin categoría asignada conserva su código.
            "categoria": types.map(ACTOR_TYPE_TO_CATEGORY).fillna(types),
        }
    )

    cameo = (
        raw[["EventCode", "EventBaseCode", "EventRootCode", "QuadClass"]]
        .drop_duplicates("EventCode")
        .sort_values("EventCode")
    )
    dim_cameo = pd.DataFrame(
        {
            "cameo_cod": cameo["EventCode"].astype(str),
            "base_cod": cameo["EventBaseCode"].astype(str),
            "raiz_cod": cameo["EventRootCode"].astype(str),
            "raiz_desc": cameo["EventRootCode"].map(CAMEO_ROOT_LABELS).astype(str),
            "quad_class": cameo["QuadClass"].astype(int),
            "quad_class_desc": cameo["QuadClass"].map(QUAD_CLASS_LABELS).astype(str),
        }
    )

    geo_ids = dim_geografia.set_index("pais_cod")["geo_id"]
    type_ids = dim_tipo_actor.set_index("tipo_cod")["tipo_actor_id"]
    fact_evento = pd.DataFrame(
        {
            "evento_id": raw["GLOBALEVENTID"],
            "fecha_key": raw["SQLDATE"].astype(int),
            "geo_id": raw["ActionGeo_CountryCode"].map(geo_ids).astype("Int64"),
            "actor1_tipo_id": actor1.map(type_ids),
            "actor2_tipo_id": actor2.map(type_ids),
            "cameo_cod": raw["EventCode"].astype(str),
            "escala_goldstein": raw["GoldsteinScale"],
            "tono_promedio": raw["AvgTone"],
            "num_menciones": raw["NumMentions"],
            "num_fuentes": raw["NumSources"],
            "num_articulos": raw["NumArticles"],
        }
    )

    return {
        "dim_tiempo": dim_tiempo,
        "dim_geografia": dim_geografia,
        "dim_tipo_actor": dim_tipo_actor,
        "dim_cameo": dim_cameo,
        "fact_evento": fact_evento,
    }


def load_warehouse(
    raw: pd.DataFrame,
    fips_lookup: pd.DataFrame,
    db_path: str | Path = WAREHOUSE_DB,
) -> dict[str, int]:
    """Crea el almacén SQLite desde cero y lo carga.

    Borra la base si ya existía, crea el esquema (``SCHEMA``) y carga las
    dimensiones antes que el hecho, con las claves foráneas activadas: si
    algún hecho apunta a una fila inexistente de una dimensión, la carga
    falla.

    Returns
    -------
    dict[str, int]
        Cantidad de filas cargadas en cada tabla.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)

    tables = build_tables(raw, fips_lookup)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        for name, table in tables.items():
            table.to_sql(name, conn, if_exists="append", index=False)
    return {name: len(table) for name, table in tables.items()}


def query(sql: str, db_path: str | Path = WAREHOUSE_DB) -> pd.DataFrame:
    """Ejecuta una consulta sobre el almacén y devuelve el resultado."""
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(sql, conn)


def read_table(name: str, db_path: str | Path = WAREHOUSE_DB) -> pd.DataFrame:
    """Lee una tabla completa del almacén."""
    return query(f"SELECT * FROM {name}", db_path)


def merge_analysis_frame(db_path: str | Path = WAREHOUSE_DB) -> pd.DataFrame:
    """Lo mismo que ``ANALYSIS_QUERY``, pero con ``pd.merge`` sobre las tablas leídas.

    ``dim_tipo_actor`` se une dos veces (una por cada actor): es una
    dimensión de rol múltiple.
    """
    fact = read_table("fact_evento", db_path)
    actor_type = read_table("dim_tipo_actor", db_path)[["tipo_actor_id", "categoria"]]

    merged = (
        fact.dropna(subset=["escala_goldstein", "tono_promedio"])
        .merge(read_table("dim_tiempo", db_path)[["fecha_key", "fecha"]], on="fecha_key")
        .merge(read_table("dim_geografia", db_path), on="geo_id", how="inner")
        .merge(actor_type.add_prefix("a1_"), left_on="actor1_tipo_id", right_on="a1_tipo_actor_id")
        .merge(actor_type.add_prefix("a2_"), left_on="actor2_tipo_id", right_on="a2_tipo_actor_id")
        .merge(read_table("dim_cameo", db_path)[["cameo_cod", "raiz_cod"]], on="cameo_cod")
    )
    return (
        merged.rename(
            columns={
                "pais_cod": "pais",
                "a1_categoria": "actor1_categoria",
                "a2_categoria": "actor2_categoria",
                "raiz_cod": "interaccion",
                "escala_goldstein": "goldstein",
                "tono_promedio": "tono",
            }
        )[
            [
                "evento_id", "fecha", "pais", "pais_nombre", "region",
                "actor1_categoria", "actor2_categoria", "interaccion",
                "goldstein", "tono", "num_menciones", "num_fuentes", "num_articulos",
            ]
        ]
        .sort_values("evento_id")
        .reset_index(drop=True)
    )
