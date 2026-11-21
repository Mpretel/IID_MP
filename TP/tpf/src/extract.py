"""Etapa EXTRACT: descarga Sleep-EDF Expanded desde PhysioNet.

Flujo:
    1) De PhysioNet se descarga SHA256SUMS.txt: catálogo de registros
    2) Selección de registros, luego descarga PSG + Hypnogram
    3) Validación (tamaño + SHA256)
    4) Se almacena en data/raw/

Los archivos ya presentes y válidos no se vuelven a descargar.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from src import bids, config

logger = logging.getLogger(__name__)

# SC4ssNEx-PSG.edf  /  SC4ssNxx-Hypnogram.edf  (ss = sujeto, N = noche)
# Ejemplo: SC4041E0-PSG.edf       -> subject=04, night=1, suffix=E0, kind=PSG
#          SC4041EC-Hypnogram.edf -> subject=04, night=1, suffix=EC, kind=Hypnogram
# El sufijo difiere entre PSG e hipnograma: por eso se emparejan por (sujeto, noche).
_SC_FILE_PATTERN = re.compile(
    r"^SC4(?P<subject>\d{2})(?P<night>\d)(?P<suffix>[A-Z0-9]{2})-(?P<kind>PSG|Hypnogram)\.edf$"
)


# ---------------------------------------------------------------------------
# Utilidades de red y archivos
# ---------------------------------------------------------------------------
def _download_to_path(relpath: str, dest: Path) -> str:
    """Descarga un archivo del dataset y lo guarda en `dest`. Devuelve la URL desde la que se bajó.

    - Prueba primero el servidor de AWS y, si falla, el de PhysioNet; en cada uno hasta
      DOWNLOAD_RETRIES intentos, esperando un poco más entre cada uno.
    - Escribe en un archivo temporal `.part` y solo al terminar le pone el nombre final:
      si la descarga se corta, nunca queda un archivo incompleto con el nombre correcto.
    - Si todos los intentos fallan, corta con un error.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for base_url in config.PHYSIONET_MIRROR_URLS:
        url = base_url + relpath
        for attempt in range(1, config.DOWNLOAD_RETRIES + 1):
            try:
                with urllib.request.urlopen(url, timeout=config.DOWNLOAD_TIMEOUT_S) as resp, open(tmp, "wb") as fh:
                    while chunk := resp.read(1 << 20):
                        fh.write(chunk)
                tmp.replace(dest)
                return url
            except OSError as exc:
                logger.warning("Intento %d/%d falló para %s: %s", attempt, config.DOWNLOAD_RETRIES, url, exc)
                tmp.unlink(missing_ok=True)
                time.sleep(2 * attempt)
    raise RuntimeError(f"No se pudo descargar {relpath} desde ningún mirror.")


def sha256_of(path: Path) -> str:
    """Calcula el hash SHA256 de un archivo leyendo por bloques."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()

# Validación de archivos: existen, tienen tamaño mínimo y SHA256 correcto.
def _is_valid_file(path: Path, expected_sha256: str, min_size: int) -> bool:
    return path.exists() and path.stat().st_size >= min_size and sha256_of(path) == expected_sha256


# ---------------------------------------------------------------------------
# Catálogo de registros
# ---------------------------------------------------------------------------
def fetch_checksums() -> pd.DataFrame:
    """Devuelve la lista oficial de archivos del dataset con el hash de cada uno.

    SHA256SUMS.txt lo publica PhysioNet y tiene una línea por archivo:
        414a4be8...ec sleep-cassette/SC4512EW-Hypnogram.edf
    Es el punto de partida del Extract: de acá salen qué archivos existen y contra
    qué hash se verifica cada descarga.

    Resultado: DataFrame con columnas [sha256, relpath].
    """
    path = config.RAW_DIR / config.CHECKSUMS_FILENAME
    # Se descarga solo si no está en disco.
    if not path.exists():
        _download_to_path(config.CHECKSUMS_FILENAME, path)
    # Cada línea se corta en el primer espacio: hash | ruta. Se saltean las líneas vacías.
    rows = [line.split(maxsplit=1) for line in path.read_text().splitlines() if line.strip()]
    return pd.DataFrame(rows, columns=["sha256", "relpath"])


def build_catalog(checksums: pd.DataFrame) -> pd.DataFrame:
    """Construye el catálogo de registros SC emparejando PSG e hipnograma por sujeto y noche.

    El sufijo del hipnograma (p. ej. 'EC', 'EH') difiere del del PSG ('E0'),
    por eso el emparejamiento se hace por (subject, night) y no por nombre.

    Ejemplo: de estas dos líneas de SHA256SUMS.txt
        2b40a18a...  sleep-cassette/SC4001E0-PSG.edf
        a4cf6769...  sleep-cassette/SC4001EC-Hypnogram.edf
    sale una sola fila del catálogo:
        subject=0, night=1, recording_id=SC4001,
        relpath_psg=sleep-cassette/SC4001E0-PSG.edf,       sha256_psg=2b40a18a...,
        relpath_hyp=sleep-cassette/SC4001EC-Hypnogram.edf, sha256_hyp=a4cf6769...
    Los archivos de otros estudios (ST7...) y los auxiliares (RECORDS, *.xls) se ignoran.
    """
    rows = []
    prefix = config.PHYSIONET_SUBSET + "/"
    for sha, relpath in checksums.itertuples(index=False):
        match = _SC_FILE_PATTERN.match(relpath.removeprefix(prefix))
        if match:
            rows.append({
                "subject": int(match["subject"]),
                "night": int(match["night"]),
                "kind": match["kind"],
                "relpath": relpath,
                "sha256": sha,
            })
    files = pd.DataFrame(rows)

    psg = files[files.kind == "PSG"].drop(columns="kind")
    hyp = files[files.kind == "Hypnogram"].drop(columns="kind")
    # Cada PSG se une con el hipnograma del mismo sujeto y noche (en sleep-cassette todos tienen par).
    catalog = psg.merge(hyp, on=["subject", "night"], suffixes=("_psg", "_hyp"))
    catalog["recording_id"] = catalog["relpath_psg"].str.extract(r"(SC4\d{3})", expand=False)
    return catalog.sort_values(["subject", "night"]).reset_index(drop=True)


def select_subjects(subjects_per_group: int) -> list[int]:
    """Muestra estratificada: `subjects_per_group` mujeres y hombres por grupo etario (regla en config.py)."""
    catalog = build_catalog(fetch_checksums())
    complete = catalog.groupby("subject")["night"].nunique().loc[lambda n: n == len(config.NIGHTS)].index
    download_subjects_metadata()
    meta = bids.load_subjects_metadata().drop_duplicates("subject")
    meta = meta[meta["subject"].isin(complete)].sort_values("subject")
    meta["group"] = pd.cut(meta["age"], config.AGE_BINS, right=False, labels=config.AGE_LABELS).astype(str)
    available = meta.groupby(["group", "sex"]).size().min()
    if subjects_per_group > available:
        raise ValueError(f"Hay como máximo {available} sujetos por grupo etario y sexo.")

    chosen: list[int] = []

    def count(group: str, sex: str) -> int:
        return int((meta["subject"].isin(chosen) & (meta["group"] == group) & (meta["sex"] == sex)).sum())

    # 1. Por sexo: el sujeto más cercano a cada cuantil de edad, sin pasarse del cupo de su grupo.
    for sex, d in meta.groupby("sex"):
        for q in np.quantile(d["age"], [0.1, 0.3, 0.5, 0.7, 0.9]):
            free = d[~d["subject"].isin(chosen)]
            for row in free.assign(dist=(free["age"] - q).abs()).sort_values(["dist", "subject"]).itertuples():
                if count(row.group, sex) < subjects_per_group:
                    chosen.append(int(row.subject))
                    break
    # 2. Cada grupo y sexo se completa con la edad más alejada de las ya elegidas en ese grupo.
    for (group, sex), d in meta.groupby(["group", "sex"]):
        while count(group, sex) < subjects_per_group:
            have = d.loc[d["subject"].isin(chosen), "age"].to_numpy()
            free = d[~d["subject"].isin(chosen)]
            gap = free["age"].map(lambda age: np.abs(have - age).min() if len(have) else 0)
            pick = free.assign(gap=gap).sort_values(["gap", "subject"], ascending=[False, True]).iloc[0]
            chosen.append(int(pick["subject"]))
    return sorted(chosen)


def select_records(catalog: pd.DataFrame, subject_ids: list[int]) -> pd.DataFrame:
    """Registros de los sujetos elegidos, en las noches de config.NIGHTS."""
    subset = catalog[catalog["night"].isin(config.NIGHTS)]
    missing = set(subject_ids) - set(subset["subject"])
    if missing:
        raise ValueError(f"Sujetos no disponibles en {config.PHYSIONET_SUBSET}: {sorted(missing)}")
    return subset[subset["subject"].isin(subject_ids)].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Descarga
# ---------------------------------------------------------------------------
def _ensure_file(relpath: str, sha256: str, min_size: int) -> tuple[Path, str, str | None]:
    """Garantiza que el archivo exista y sea válido. Devuelve (ruta, estado, url usada)."""
    dest = config.RAW_DIR / relpath
    if _is_valid_file(dest, sha256, min_size):
        return dest, "cached", None
    url = _download_to_path(relpath, dest)
    if not _is_valid_file(dest, sha256, min_size):
        raise RuntimeError(
            f"{dest.name}: la descarga no pasó la validación (tamaño >= {min_size} B y SHA256 oficial)."
        )
    return dest, "downloaded", url


def download_records(records: pd.DataFrame) -> pd.DataFrame:
    """Descarga PSG + hipnograma de cada registro y escribe/actualiza el manifest."""
    entries = []
    for rec in records.itertuples(index=False):
        for kind, relpath, sha, min_size in [
            ("PSG", rec.relpath_psg, rec.sha256_psg, config.MIN_PSG_SIZE_BYTES),
            ("Hypnogram", rec.relpath_hyp, rec.sha256_hyp, config.MIN_HYPNOGRAM_SIZE_BYTES),
        ]:
            path, status, url = _ensure_file(relpath, sha, min_size)
            # Solo se informa lo que implicó trabajo; lo que ya estaba en caché va a DEBUG.
            (logger.debug if status == "cached" else logger.info)("%-9s %-24s %s", kind, path.name, status)
            entries.append({
                "recording_id": rec.recording_id,
                "subject": rec.subject,
                "night": rec.night,
                "kind": kind,
                "file": path.relative_to(config.PROJECT_ROOT).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha,
                "status": status,
                "source_url": url,
                "checked_at": pd.Timestamp.now(tz=config.TIMEZONE).isoformat(timespec="seconds"),
            })
    manifest = pd.DataFrame(entries)
    _update_manifest(manifest)
    status = manifest["status"].value_counts()
    logger.info("Archivos: %d (%d en caché, %d descargados)", len(manifest),
                status.get("cached", 0), status.get("downloaded", 0))
    return manifest


def _update_manifest(new: pd.DataFrame) -> None:
    """Agrega las entradas nuevas al manifest histórico (una fila por archivo, la más reciente).

    Si un archivo se reutiliza ('cached'), se conserva la URL de la descarga original.
    """
    path = config.DOWNLOAD_MANIFEST_PATH
    if path.exists():
        old = pd.read_csv(path)
        previous_url = new["file"].map(old.set_index("file")["source_url"])
        new = new.assign(source_url=new["source_url"].where(new["source_url"].notna(), previous_url))
        new = pd.concat([old, new]).drop_duplicates("file", keep="last")
    new.sort_values("file").to_csv(path, index=False)


def download_subjects_metadata() -> Path:
    """Descarga SC-subjects.xls (edad y sexo de cada sujeto) si no existe."""
    dest = config.RAW_DIR / config.SUBJECTS_METADATA_FILENAME
    if not dest.exists():
        _download_to_path(config.SUBJECTS_METADATA_FILENAME, dest)
    return dest

def run_extract(subject_ids: list[int]) -> pd.DataFrame:
    """Punto de entrada de la etapa Extract. Devuelve el manifest de esta ejecución.

    Pasos (entre paréntesis, los números con la configuración actual):

        fetch_checksums             lista oficial de PhysioNet: archivo + hash (398 archivos)
              ↓
        build_catalog               empareja PSG e hipnograma de cada noche (153 registros, 78 sujetos)
              ↓
        select_records              se queda con los sujetos pedidos y las noches de
                                    config.NIGHTS (18 sujetos × 2 noches = 36 registros)
              ↓
        download_subjects_metadata  baja SC-subjects.xls (edad y sexo de cada sujeto)
              ↓
        download_records            descarga y verifica 36 PSG + 36 hipnogramas → manifest (72 filas)

    Lo que ya está en disco y pasa la verificación (tamaño + SHA256) no se vuelve a descargar.
    """
    catalog = build_catalog(fetch_checksums())
    records = select_records(catalog, subject_ids)
    logger.info("Registros seleccionados: %d (%d sujetos)", len(records), records["subject"].nunique())
    download_subjects_metadata()
    return download_records(records)
