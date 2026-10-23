"""Armado de la One Big Table (OBT): eventos con las descripciones de sus códigos.

El archivo de eventos de GDELT ya trae en una fila el evento, sus dos actores
y las tres geografías, pero con códigos (``042``, ``GOV``, ``US``...). La OBT
los desnormaliza: une a cada código su descripción, tomada de las tablas de
códigos de GDELT, que en un modelo estrella serían las dimensiones.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from .config import GEO_TYPE_LABELS, LOOKUP_FILES, LOOKUPS_DIR, LOOKUPS_URL, QUAD_CLASS_LABELS


def load_lookup(name: str, cache_dir: str | Path = LOOKUPS_DIR) -> pd.Series:
    """Tabla de códigos de GDELT como Serie código -> descripción.

    La descarga la primera vez y la guarda en ``cache_dir``. Todas son
    archivos de texto separados por tabs con dos columnas; todas tienen
    encabezado salvo ``FIPS.country.txt``.
    """
    path = Path(cache_dir) / LOOKUP_FILES[name]
    if not path.exists():
        response = requests.get(LOOKUPS_URL + LOOKUP_FILES[name], timeout=60)
        response.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
    has_header = name != "paises_fips"
    table = pd.read_csv(path, sep="\t", header=0 if has_header else None, dtype="string",
                        names=["codigo", "descripcion"], encoding="latin-1",
                        keep_default_na=False)
    return table.drop_duplicates("codigo").set_index("codigo")["descripcion"]


# Columna de códigos -> tabla de códigos con la que se describe.
_CODE_COLUMNS = {
    "eventos": ["EventCode", "EventBaseCode", "EventRootCode"],
    "paises_cameo": ["Actor1CountryCode", "Actor2CountryCode"],
    "tipos_actor": [f"Actor{a}Type{t}Code" for a in (1, 2) for t in (1, 2, 3)],
    "grupos_conocidos": ["Actor1KnownGroupCode", "Actor2KnownGroupCode"],
    "etnias": ["Actor1EthnicCode", "Actor2EthnicCode"],
    "religiones": [f"Actor{a}Religion{r}Code" for a in (1, 2) for r in (1, 2)],
    "paises_fips": ["Actor1Geo_CountryCode", "Actor2Geo_CountryCode", "ActionGeo_CountryCode"],
}


def build_obt(events: pd.DataFrame) -> pd.DataFrame:
    """Une a los eventos las descripciones de sus códigos y las fechas.

    Cada columna de código ``X`` suma una columna ``X_Desc`` al lado. Se
    agregan también la fecha del evento (``SQLDATE``) y el instante en que
    GDELT lo registró (``DATEADDED``) como fechas, y las etiquetas de
    ``QuadClass`` y de los tipos de geografía, que no tienen tabla de códigos.
    Los códigos que no figuran en su tabla quedan con descripción vacía.
    """
    obt = events.copy()
    descriptions = {}
    for lookup, columns in _CODE_COLUMNS.items():
        table = load_lookup(lookup)
        for column in columns:
            descriptions[f"{column}_Desc"] = obt[column].map(table).astype("string")
    descriptions["QuadClass_Desc"] = obt["QuadClass"].map(QUAD_CLASS_LABELS).astype("string")
    for geo in ("Actor1Geo", "Actor2Geo", "ActionGeo"):
        descriptions[f"{geo}_Type_Desc"] = obt[f"{geo}_Type"].map(GEO_TYPE_LABELS).astype("string")

    # Cada descripción va inmediatamente después de su código.
    columns = []
    for column in obt.columns:
        columns.append(column)
        if f"{column}_Desc" in descriptions:
            columns.append(f"{column}_Desc")
    obt = pd.concat([obt, pd.DataFrame(descriptions, index=obt.index)], axis=1)[columns]

    obt.insert(1, "FechaEvento", pd.to_datetime(obt["SQLDATE"], format="%Y%m%d", errors="coerce"))
    obt.insert(len(obt.columns) - 1, "FechaAgregado",
               pd.to_datetime(obt["DATEADDED"], format="%Y%m%d%H%M%S", errors="coerce"))
    return obt
