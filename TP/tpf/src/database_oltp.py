"""Base transaccional (OLTP) normalizada en 3NF: data/database/sleep_oltp.sqlite.

Modelo:
    subject 1──N recording 1──N epoch N──1 sleep_stage
                                  │
                                  1
                                  │
                                  N
                             eeg_feature N──1 channel

Decisiones de normalización:
  - Edad y sexo dependen del sujeto, no del registro: guardarlos en `recording`
    crearía la dependencia transitiva recording -> sujeto -> edad; por eso existe `subject`.
  - Las etapas se guardan ya en AASM: el mapeo desde R&K se hace al preprocesar.
    Solo se cargan las 5 etapas puntuadas (W, N1, N2, N3, REM): las épocas MOVE y UNK
    se documentan en la tabla tidy, pero no se usan en ningún análisis.
  - start_sec = epoch_number * 30 no se guarda: dependería solo de parte de la
    clave candidata (recording_id, epoch_number). Se calcula en `v_epoch`.
  - Potencia total y relativa se derivan de las potencias absolutas
    (total = suma de bandas disjuntas, rel = abs/total). No se guardan; se
    calculan en `v_eeg_feature`.
  - Los outliers estadísticos dependen de toda la distribución, no de la fila:
    no son un atributo de la observación y se calculan en el ETL al almacén.
"""

from __future__ import annotations

import logging
import sqlite3

import numpy as np
import pandas as pd

from src import config

logger = logging.getLogger(__name__)

STORED_FEATURES = ["delta_abs", "theta_abs", "alpha_abs", "sigma_abs", "beta_abs",
                   "sample_entropy", "rms", "peak_to_peak"]

SCHEMA_SQL = f"""
CREATE TABLE subject (
    subject_id      INTEGER PRIMARY KEY,                      -- ID de Sleep-EDF (SC4ss..)
    age             INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    sex             TEXT    NOT NULL CHECK (sex IN ('F', 'M'))
);

CREATE TABLE recording (
    recording_id          TEXT    PRIMARY KEY,                -- p. ej. 'SC4001'
    subject_id            INTEGER NOT NULL REFERENCES subject (subject_id),
    night                 INTEGER NOT NULL CHECK (night IN (1, 2)),
    UNIQUE (subject_id, night)
);

CREATE TABLE channel (
    channel_id      INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE                   -- etiqueta del EDF
);

CREATE TABLE sleep_stage (
    stage_id        INTEGER PRIMARY KEY,
    stage_code      TEXT    NOT NULL UNIQUE                   -- W, N1, N2, N3, REM (stage_id sigue ese orden)
);

CREATE TABLE epoch (
    epoch_id        INTEGER PRIMARY KEY,
    recording_id    TEXT    NOT NULL REFERENCES recording (recording_id),
    epoch_number    INTEGER NOT NULL CHECK (epoch_number >= 0),   -- índice desde el inicio del EDF
    stage_id        INTEGER NOT NULL REFERENCES sleep_stage (stage_id),
    UNIQUE (recording_id, epoch_number)
);

CREATE TABLE eeg_feature (
    epoch_id         INTEGER NOT NULL REFERENCES epoch (epoch_id),
    channel_id       INTEGER NOT NULL REFERENCES channel (channel_id),
    -- Potencias absolutas [µV²] (NULL = no calculable)
    delta_abs        REAL CHECK (delta_abs >= 0),
    theta_abs        REAL CHECK (theta_abs >= 0),
    alpha_abs        REAL CHECK (alpha_abs >= 0),
    sigma_abs        REAL CHECK (sigma_abs >= 0),
    beta_abs         REAL CHECK (beta_abs >= 0),
    sample_entropy   REAL CHECK (sample_entropy >= 0),
    rms              REAL CHECK (rms >= 0),                    -- [µV]
    peak_to_peak     REAL CHECK (peak_to_peak >= 0),           -- [µV]
    is_artifact      INTEGER NOT NULL CHECK (is_artifact IN (0, 1)),  -- el motivo queda en la tabla tidy
    PRIMARY KEY (epoch_id, channel_id)
);

-- Índices para las FK más consultadas (las PK/UNIQUE ya están indexadas).
CREATE INDEX idx_recording_subject ON recording (subject_id);
CREATE INDEX idx_epoch_stage       ON epoch (stage_id);
CREATE INDEX idx_feature_channel   ON eeg_feature (channel_id);

-- Vistas con atributos derivados (no almacenados para respetar 3NF).
CREATE VIEW v_epoch AS
SELECT e.epoch_id, e.recording_id, e.epoch_number,
       e.epoch_number * {config.EPOCH_DURATION_S} AS start_sec,
       s.stage_code
FROM epoch e
JOIN sleep_stage s ON s.stage_id = e.stage_id;

CREATE VIEW v_eeg_feature AS
SELECT f.*,
       f.delta_abs + f.theta_abs + f.alpha_abs + f.sigma_abs + f.beta_abs AS total_power,
       f.delta_abs / (f.delta_abs + f.theta_abs + f.alpha_abs + f.sigma_abs + f.beta_abs) AS delta_rel,
       f.theta_abs / (f.delta_abs + f.theta_abs + f.alpha_abs + f.sigma_abs + f.beta_abs) AS theta_rel,
       f.alpha_abs / (f.delta_abs + f.theta_abs + f.alpha_abs + f.sigma_abs + f.beta_abs) AS alpha_rel,
       f.sigma_abs / (f.delta_abs + f.theta_abs + f.alpha_abs + f.sigma_abs + f.beta_abs) AS sigma_rel,
       f.beta_abs  / (f.delta_abs + f.theta_abs + f.alpha_abs + f.sigma_abs + f.beta_abs) AS beta_rel
FROM eeg_feature f;
"""


def connect() -> sqlite3.Connection:
    """Abre la base con foreign keys activadas (en SQLite están desactivadas por defecto)."""
    conn = sqlite3.connect(config.OLTP_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _records(df: pd.DataFrame) -> list[tuple]:
    """Filas como tuplas nativas de Python; NaN -> NULL."""
    clean = df.astype(object).where(df.notna(), None)
    return [tuple(v.item() if isinstance(v, np.generic) else v for v in row)
            for row in clean.itertuples(index=False)]


def _insert(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> None:
    cols = ", ".join(df.columns)
    marks = ", ".join("?" * len(df.columns))
    conn.executemany(f"INSERT INTO {table} ({cols}) VALUES ({marks})", _records(df))


def scored_rows(tidy: pd.DataFrame) -> pd.DataFrame:
    """Filas de la tabla tidy con etapa puntuada (W, N1, N2, N3, REM): las que se cargan en la base."""
    return tidy[tidy["sleep_stage"].isin(config.SCORED_STAGES)]


def build_oltp(tidy: pd.DataFrame, recordings: pd.DataFrame) -> None:
    """(Re)crea la base OLTP desde las tablas procesadas.

    La base se reconstruye completa en cada ejecución: es un artefacto derivado
    de data/processed, y reconstruir garantiza que no queden filas obsoletas.
    Solo se cargan las épocas con etapa puntuada (ver scored_rows).
    """
    tidy = scored_rows(tidy)
    config.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    config.OLTP_DB_PATH.unlink(missing_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA_SQL)

        subjects = (recordings[["subject", "age", "sex"]].drop_duplicates()
                    .rename(columns={"subject": "subject_id"}))
        if subjects["subject_id"].duplicated().any():
            raise ValueError("Un mismo sujeto tiene edad/sexo distintos entre noches.")
        _insert(conn, "subject", subjects)

        _insert(conn, "recording", recordings.rename(columns={"subject": "subject_id"})[[
            "recording_id", "subject_id", "night"]])

        _insert(conn, "channel", pd.DataFrame({"name": config.EEG_CHANNELS}))

        # Se insertan en el orden del sueño (W, N1, N2, N3, REM): stage_id 1..5 conserva ese orden.
        _insert(conn, "sleep_stage", pd.DataFrame({"stage_code": config.SCORED_STAGES}))
        stage_ids = dict(conn.execute("SELECT stage_code, stage_id FROM sleep_stage"))

        epochs = (tidy[["recording_id", "epoch_number", "sleep_stage"]]
                  .drop_duplicates(["recording_id", "epoch_number"]))
        _insert(conn, "epoch", epochs.assign(stage_id=epochs["sleep_stage"].astype(str).map(stage_ids))
                [["recording_id", "epoch_number", "stage_id"]])

        epoch_ids = pd.read_sql("SELECT epoch_id, recording_id, epoch_number FROM epoch", conn)
        channel_ids = dict(conn.execute("SELECT name, channel_id FROM channel"))
        feats = (tidy.merge(epoch_ids, on=["recording_id", "epoch_number"], how="left", validate="many_to_one")
                 .assign(channel_id=lambda d: d["channel"].astype(str).map(channel_ids),
                         is_artifact=lambda d: d["is_artifact"].astype(int)))
        _insert(conn, "eeg_feature",
                feats[["epoch_id", "channel_id"] + STORED_FEATURES + ["is_artifact"]])
    conn.close()
    logger.info("OLTP creada: %s", config.OLTP_DB_PATH.relative_to(config.PROJECT_ROOT).as_posix())


def table_counts() -> pd.Series:
    """Cantidad de filas por tabla."""
    with connect() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY rowid")]
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
    conn.close()
    return pd.Series(counts, name="rows")
