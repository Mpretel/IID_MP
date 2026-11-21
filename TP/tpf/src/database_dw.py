"""Data Warehouse en esquema estrella: data/database/sleep_dw.sqlite.

    SQLite OLTP  --(ETL: extract SQL -> transform pandas -> load)-->  SQLite DW

Grano de FACT_EEG_EPOCH: una observación de features EEG correspondiente a
un epoch de 30 segundos, un canal, un sujeto y un registro.

        dim_recording ── fact_eeg_epoch ── dim_channel
                               │
                        dim_sleep_stage

Tres dimensiones, que forman el cubo etapa × grupo etario × canal. El sujeto no es
una dimensión aparte: cada registro pertenece a un único sujeto, así que sujeto y
grupo etario son una jerarquía dentro de dim_recording
(grupo etario -> sujeto -> registro).

A diferencia del OLTP, acá la redundancia es deliberada: se materializan la
potencia total, las relativas y el tiempo desde el inicio del sueño para que las
consultas analíticas sean simples (un JOIN por dimensión) y rápidas.
También se guarda la marca de outlier de Tukey (is_stat_outlier), para que el dashboard pueda
incluir o excluir esas épocas; las consultas del análisis las incluyen.
"""

from __future__ import annotations

import logging
import sqlite3

import pandas as pd

from src import config, database_oltp, quality
from src.database_oltp import _insert
from src.features import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE dim_recording (
    recording_key         INTEGER PRIMARY KEY,    -- surrogate key
    recording_id          TEXT    NOT NULL UNIQUE, -- clave natural (Sleep-EDF)
    age_group             TEXT    NOT NULL,       -- jerarquía: grupo etario -> sujeto -> registro
    subject_id            INTEGER NOT NULL,
    age                   INTEGER NOT NULL,
    sex                   TEXT    NOT NULL
);

CREATE TABLE dim_channel (
    channel_key   INTEGER PRIMARY KEY,
    channel_name  TEXT NOT NULL UNIQUE   -- Fpz-Cz, Pz-Oz (sin el prefijo 'EEG ' del EDF)
);

CREATE TABLE dim_sleep_stage (
    stage_key            INTEGER PRIMARY KEY,
    stage_code           TEXT    NOT NULL UNIQUE    -- W, N1, N2, N3, REM (stage_key sigue ese orden)
);

CREATE TABLE fact_eeg_epoch (
    recording_key           INTEGER NOT NULL REFERENCES dim_recording (recording_key),
    channel_key             INTEGER NOT NULL REFERENCES dim_channel (channel_key),
    stage_key               INTEGER NOT NULL REFERENCES dim_sleep_stage (stage_key),
    epoch_number            INTEGER NOT NULL,       -- dimensión degenerada
    hours_since_sleep_onset REAL    NOT NULL,       -- negativo = vigilia previa al sueño
    delta_abs REAL, theta_abs REAL, alpha_abs REAL, sigma_abs REAL, beta_abs REAL,
    delta_rel REAL, theta_rel REAL, alpha_rel REAL, sigma_rel REAL, beta_rel REAL,
    total_power      REAL,
    sample_entropy   REAL,
    rms              REAL,
    peak_to_peak     REAL,
    is_artifact      INTEGER NOT NULL,
    is_stat_outlier  INTEGER NOT NULL,     -- Tukey por registro × canal × etapa (solo informativo)
    PRIMARY KEY (recording_key, epoch_number, channel_key)   -- la clave es el grano
);

CREATE INDEX idx_fact_channel   ON fact_eeg_epoch (channel_key);
CREATE INDEX idx_fact_stage     ON fact_eeg_epoch (stage_key);
"""

# Extract: una consulta sobre el OLTP con las vistas que calculan atributos derivados.
OLTP_EXTRACT_SQL = """
SELECT r.subject_id, s.age, s.sex, r.recording_id,
       c.name AS channel,
       e.epoch_number, e.start_sec, e.stage_code AS stage,
       f.delta_abs, f.theta_abs, f.alpha_abs, f.sigma_abs, f.beta_abs,
       f.delta_rel, f.theta_rel, f.alpha_rel, f.sigma_rel, f.beta_rel, f.total_power,
       f.sample_entropy, f.rms, f.peak_to_peak,
       f.is_artifact
FROM v_eeg_feature f
JOIN v_epoch   e ON e.epoch_id   = f.epoch_id
JOIN channel   c ON c.channel_id = f.channel_id
JOIN recording r ON r.recording_id = e.recording_id
JOIN subject   s ON s.subject_id = r.subject_id
"""



def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DW_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def extract_from_oltp() -> pd.DataFrame:
    with database_oltp.connect() as conn:
        data = pd.read_sql(OLTP_EXTRACT_SQL, conn)
    conn.close()
    data["is_artifact"] = data["is_artifact"].astype(bool)
    return data


def _with_key(df: pd.DataFrame, key: str, order_by: list[str]) -> pd.DataFrame:
    """Asigna surrogate keys 1..n en un orden determinístico (reproducible)."""
    df = df.sort_values(order_by).reset_index(drop=True)
    df.insert(0, key, range(1, len(df) + 1))
    return df


def transform(data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Construye dimensiones y hechos a partir de la extracción del OLTP."""
    rec = data.drop_duplicates("recording_id")
    dim_recording = _with_key(pd.DataFrame({
        "recording_id": rec["recording_id"],
        "age_group": pd.cut(rec["age"], config.AGE_BINS, right=False, labels=config.AGE_LABELS).astype(str),
        "subject_id": rec["subject_id"], "age": rec["age"], "sex": rec["sex"],
    }), "recording_key", ["recording_id"])

    # En el almacén el canal se nombra sin el prefijo del EDF: "EEG Fpz-Cz" -> "Fpz-Cz".
    data = data.assign(channel=data["channel"].str.replace("EEG ", "", regex=False))
    dim_channel = _with_key(data[["channel"]].drop_duplicates().rename(columns={"channel": "channel_name"}),
                            "channel_key", ["channel_name"])

    # Todas las etapas (no solo las observadas), desde el catálogo del OLTP.
    with database_oltp.connect() as conn:
        stages = pd.read_sql("SELECT stage_id, stage_code FROM sleep_stage", conn)
    conn.close()
    # stage_key se asigna en el orden de stage_id (W, N1, N2, N3, REM): las consultas ordenan por la clave.
    dim_sleep_stage = _with_key(stages, "stage_key", ["stage_id"]).drop(columns="stage_id")

    # Hechos: marca de outlier de Tukey dentro de cada noche (misma regla que la tabla tidy).
    facts = quality.flag_statistical_outliers(data, group_cols=["recording_id", "channel", "stage"])
    # Tiempo desde el inicio del sueño (primera época de N1, N2, N3 o REM de cada noche).
    sleep_onset = (facts[facts["stage"].isin(["N1", "N2", "N3", "REM"])]
                   .groupby("recording_id")["start_sec"].min().rename("sleep_onset_sec"))
    facts = (facts
             .merge(sleep_onset, on="recording_id")
             .merge(dim_recording[["recording_key", "recording_id"]], on="recording_id")
             .merge(dim_channel[["channel_key", "channel_name"]], left_on="channel", right_on="channel_name")
             .merge(dim_sleep_stage[["stage_key", "stage_code"]], left_on="stage", right_on="stage_code"))
    if len(facts) != len(data):
        raise ValueError(f"El join con dimensiones cambió la cantidad de filas ({len(data)} -> {len(facts)}).")
    facts["hours_since_sleep_onset"] = (facts["start_sec"] - facts["sleep_onset_sec"]) / 3600
    facts[["is_artifact", "is_stat_outlier"]] = facts[["is_artifact", "is_stat_outlier"]].astype(int)
    fact_cols = (["recording_key", "channel_key", "stage_key", "epoch_number", "hours_since_sleep_onset"]
                 + FEATURE_COLUMNS + ["is_artifact", "is_stat_outlier"])
    fact = facts.sort_values(["recording_key", "epoch_number", "channel_key"])[fact_cols]

    return {"dim_recording": dim_recording, "dim_channel": dim_channel,
            "dim_sleep_stage": dim_sleep_stage, "fact_eeg_epoch": fact}


def load(tables: dict[str, pd.DataFrame]) -> None:
    """(Re)crea el DW y carga dimensiones y luego hechos (orden requerido por las FK)."""
    config.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    config.DW_DB_PATH.unlink(missing_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA_SQL)
        for name in ["dim_recording", "dim_channel", "dim_sleep_stage", "fact_eeg_epoch"]:
            _insert(conn, name, tables[name])
    conn.close()


def build_dw() -> dict[str, int]:
    """ETL completo OLTP -> DW. Devuelve la cantidad de filas por tabla."""
    tables = transform(extract_from_oltp())
    load(tables)
    logger.info("DW creado: %s", config.DW_DB_PATH.relative_to(config.PROJECT_ROOT).as_posix())
    return {name: len(df) for name, df in tables.items()}
