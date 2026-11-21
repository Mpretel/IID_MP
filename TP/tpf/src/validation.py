"""Validaciones automáticas del pipeline.

Cada check lanza ValidationError con un mensaje comprensible si falla y
devuelve una descripción breve si pasa, para mostrar en el notebook.

Qué se valida, siguiendo el recorrido de los datos (tabla tidy -> OLTP -> almacén):

validate_tidy: tabla de features, antes de cargarla en una base. Se valida que:
    - ningún par (registro, época, canal) aparezca dos veces;
    - cada época tenga los dos canales EEG;
    - en las filas sin artefacto, la potencia relativa esté entre 0 y 1 y las 5 bandas sumen 1;
    - is_artifact y artifact_reason coincidan: toda fila marcada tiene su motivo y ninguna
      sin marca lo tiene;
    - las filas sin artefacto no tengan features en NaN.

validate_oltp: base transaccional, después de construirla. Se valida que:
    - no haya claves foráneas rotas (PRAGMA foreign_key_check);
    - recording, epoch y eeg_feature tengan tantas filas como la tabla tidy con etapa puntuada
      (no se perdió ni se duplicó nada al cargar; MOVE y UNK no se cargan);
    - la vista v_eeg_feature, que recalcula la potencia relativa en SQL, dé lo mismo que la
      tabla tidy calculada en Python.

validate_dw: almacén, después del ETL. Se valida que:
    - no haya claves foráneas rotas;
    - la tabla de hechos tenga exactamente las mismas filas que eeg_feature del OLTP.

Lo que ya se valida en otra etapa no se repite acá:
    - archivos descargados (tamaño y SHA256): extract._ensure_file;
    - canales, frecuencia, unidades, etapas y duración de las épocas: preprocessing.validate_recording;
    - una edad y un sexo por sujeto: database_oltp.build_oltp;
    - el grano de la tabla de hechos (registro, época, canal): su clave primaria.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config
from src.features import BAND_NAMES, FEATURE_COLUMNS


class ValidationError(AssertionError):
    """Una validación del pipeline falló."""


def _check(condition: bool, ok_message: str, error_message: str) -> str:
    if not condition:
        raise ValidationError(error_message)
    return ok_message


REL_TOLERANCE = 1e-9  # error numérico admitido al comparar potencias relativas


def validate_tidy(tidy: pd.DataFrame) -> list[str]:
    """Checks de la tabla tidy (una fila por epoch x canal).

    Canales, etapas y duración de las épocas ya los valida preprocessing.validate_recording
    en cada registro, por eso no se repiten acá.
    """
    key = ["recording_id", "epoch_number", "channel"]
    dup = int(tidy.duplicated(key).sum())
    clean = tidy[~tidy["is_artifact"]]
    rel_sum = clean[[f"{b}_rel" for b in BAND_NAMES]].sum(axis=1)
    rel = clean[[f"{b}_rel" for b in BAND_NAMES]]
    per_epoch = tidy.groupby(["recording_id", "epoch_number"], observed=True)["channel"].nunique()
    reasons_ok = (tidy["is_artifact"] == tidy["artifact_reason"].notna()).all()
    return [
        _check(dup == 0, "Sin claves (registro, época, canal) duplicadas", f"{dup} claves duplicadas"),
        _check((per_epoch == len(config.EEG_CHANNELS)).all(), "Cada época tiene todos los canales",
               f"{int((per_epoch != len(config.EEG_CHANNELS)).sum())} epochs con canales faltantes"),
        _check(bool(np.allclose(rel_sum, 1, atol=REL_TOLERANCE)) and bool(((rel >= 0) & (rel <= 1)).all().all()),
               f"Potencia relativa en [0, 1] y suma 1 ± {REL_TOLERANCE} (sin artefactos)",
               f"Potencia relativa fuera de rango: suma entre {rel_sum.min():.4f} y {rel_sum.max():.4f}"),
        _check(reasons_ok, "is_artifact coherente con artifact_reason",
               "Hay filas con is_artifact y artifact_reason inconsistentes"),
        _check(tidy.loc[~tidy["is_artifact"], FEATURE_COLUMNS].notna().all().all(),
               "Sin features NaN en filas sin artefacto",
               "Hay features NaN en filas no marcadas como artefacto"),
    ]


def validate_oltp(tidy: pd.DataFrame) -> list[str]:
    """FK consistentes, conteos iguales a la tabla tidy y vistas derivadas correctas.

    Se compara con las filas de etapa puntuada, que son las que se cargan en la base.
    """
    from src.database_oltp import connect, scored_rows  # import local: evita dependencia circular

    tidy = scored_rows(tidy)
    with connect() as conn:
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        n_epoch = conn.execute("SELECT COUNT(*) FROM epoch").fetchone()[0]
        n_feature = conn.execute("SELECT COUNT(*) FROM eeg_feature").fetchone()[0]
        n_recording = conn.execute("SELECT COUNT(*) FROM recording").fetchone()[0]
        db_rel = pd.read_sql(
            "SELECT e.recording_id, e.epoch_number, c.name AS channel, f.delta_rel "
            "FROM v_eeg_feature f JOIN epoch e USING (epoch_id) JOIN channel c USING (channel_id)", conn)
    conn.close()

    expected_epochs = tidy[["recording_id", "epoch_number"]].drop_duplicates().shape[0]
    merged = tidy.assign(channel=tidy["channel"].astype(str)).merge(
        db_rel, on=["recording_id", "epoch_number", "channel"], suffixes=("", "_db"))
    max_diff = float((merged["delta_rel"] - merged["delta_rel_db"]).abs().max())
    return [
        _check(not fk_violations, "PRAGMA foreign_key_check sin violaciones",
               f"Violaciones de FK: {fk_violations[:5]}"),
        _check(n_recording == tidy["recording_id"].nunique(), f"recording: {n_recording} filas",
               f"recording tiene {n_recording} filas, la tidy {tidy['recording_id'].nunique()} registros"),
        _check(n_epoch == expected_epochs, f"epoch: {n_epoch} filas = épocas con etapa puntuada de la tidy",
               f"epoch tiene {n_epoch} filas, se esperaban {expected_epochs}"),
        _check(n_feature == len(tidy), f"eeg_feature: {n_feature} filas = filas con etapa puntuada de la tidy",
               f"eeg_feature tiene {n_feature} filas, la tidy {len(tidy)}"),
        _check(len(merged) == len(tidy) and max_diff < REL_TOLERANCE,
               f"Potencia relativa recalculada en la vista coincide (max |dif| = {max_diff:.1e})",
               f"La vista v_eeg_feature difiere de la tidy (max |dif| = {max_diff:.1e})"),
    ]


def validate_dw() -> list[str]:
    """FK del DW y conteo igual al OLTP.

    La coherencia de cada sujeto (una edad y un sexo) ya la valida database_oltp.build_oltp, y el grano
    (registro, época, canal) lo garantiza la clave primaria de fact_eeg_epoch.
    """
    from src import database_dw, database_oltp

    with database_oltp.connect() as conn:
        n_oltp = conn.execute("SELECT COUNT(*) FROM eeg_feature").fetchone()[0]
    conn.close()
    with database_dw.connect() as conn:
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        n_fact = conn.execute("SELECT COUNT(*) FROM fact_eeg_epoch").fetchone()[0]
    conn.close()

    return [
        _check(not fk_violations, "DW: PRAGMA foreign_key_check sin violaciones", f"Violaciones de FK en DW: {fk_violations[:5]}"),
        _check(n_fact == n_oltp, f"fact_eeg_epoch: {n_fact} filas = eeg_feature del OLTP",
               f"fact_eeg_epoch tiene {n_fact} filas y eeg_feature {n_oltp}"),
    ]
