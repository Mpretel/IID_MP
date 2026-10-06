"""Países FIPS 10-4 de GDELT y su región geográfica.

GDELT geolocaliza los eventos con códigos de país FIPS 10-4
(``ActionGeo_CountryCode``), no ISO. Los nombres salen de la tabla de
GDELT (``FIPS.country.txt``); la región sigue la clasificación del Banco
Mundial (7 regiones), asignada a mano por código FIPS. Los códigos que no
son países (océanos, Antártida, zonas sin soberanía) quedan en
``NO_REGION``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from .config import FIPS_LOOKUP_TXT, FIPS_LOOKUP_URL

NO_REGION = "Sin región"

_REGION_CODES = {
    "Norteamérica": "US CA BD SB",
    "América Latina y Caribe": (
        "AC AR AA AV BF BB BH BL BR VI CJ CI CO CS CU DO DR EC ES FK FG GJ GP"
        " GT GY HA HO JM MB MX MH NT NU PM PA PE RQ SC ST RN VC TB NS TD TK UY"
        " VE VQ BQ SX IP"
    ),
    "Europa y Asia Central": (
        "AL AN AM AU AJ BO BE BK BU HR CY EZ LO DA EN FO FI FR GG GM GI GR GL"
        " GK HU IC EI IM IT JN JE KZ KV KG LG LS LH LU MK MD MN MJ NL NO PL PO"
        " RO RS SM RI SI SP SV SW SZ TI TU TX UP UK UZ VT AX DX"
    ),
    "Medio Oriente y Norte de África": (
        "AG BA DJ EG IR IZ IS JO KU LE LY MT MO MU QA SA SY TS AE YM GZ WE WI"
    ),
    "Asia del Sur": "AF BG BT IN MV NP PK CE IO",
    "África Subsahariana": (
        "AO BN BC UV BY CM CV CT CD CN CF CG IV GV EK ER WZ ET GB GA GH PU KE"
        " LT LI MA MI ML MR MP MF MZ WA NG NI RE RW SH TP SG SE SL SO SF OD SU"
        " TZ TO UG ZA ZI BS EU GO JU TE"
    ),
    "Asia Oriental y Pacífico": (
        "AQ AS AT BX BM CB CH KT CK CW CR FJ FP GQ HK HQ ID JA DQ JQ KR KQ LA"
        " MC MY RM FM MQ MG NR NC NZ NE NF KN CQ PS LQ PP PC RP PF PG WS SN BP"
        " KS TW TH TT TL TN TV NH VM WQ WF PJ FQ"
    ),
    NO_REGION: "AY BV HM FS OS UF UU NM",
}

# Código FIPS -> región.
FIPS_TO_REGION = {
    code: region for region, codes in _REGION_CODES.items() for code in codes.split()
}

# Códigos que GDELT usa en ``ActionGeo_CountryCode`` pero que no están en
# ``FIPS.country.txt``: ``RB`` es el código FIPS de Serbia desde 2006 (la
# tabla sólo trae el anterior, ``RI``); ``OC`` no figura en el estándar.
_EXTRA_COUNTRIES = {
    "RB": ("Serbia", "Europa y Asia Central"),
    "OC": ("OC (sin identificar)", NO_REGION),
}


def load_fips_lookup(
    txt_path: str | Path | None = FIPS_LOOKUP_TXT,
    url: str = FIPS_LOOKUP_URL,
) -> pd.DataFrame:
    """Tabla de países FIPS con nombre y región, indexada por código.

    Descarga ``FIPS.country.txt`` de GDELT la primera vez y lo guarda en
    ``txt_path`` (con ``None`` no se guarda). Falla si algún código de la
    tabla no tiene región asignada en ``FIPS_TO_REGION``.
    """
    txt_path = Path(txt_path) if txt_path is not None else None
    if txt_path is not None and txt_path.exists():
        text = txt_path.read_text(encoding="utf-8")
    else:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        text = response.text
        if txt_path is not None:
            txt_path.parent.mkdir(parents=True, exist_ok=True)
            txt_path.write_text(text, encoding="utf-8")

    rows = [line.split("\t") for line in text.splitlines() if line.strip()]
    lookup = pd.DataFrame(rows, columns=["codigo", "nombre"]).set_index("codigo")
    lookup["region"] = lookup.index.map(FIPS_TO_REGION)
    extra = pd.DataFrame.from_dict(_EXTRA_COUNTRIES, orient="index", columns=["nombre", "region"])
    lookup = pd.concat([lookup, extra.drop(index=lookup.index, errors="ignore")])

    missing = lookup.index[lookup["region"].isna()].tolist()
    if missing:
        raise ValueError(f"Códigos FIPS sin región asignada: {missing}")
    return lookup
