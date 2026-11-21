"""Consultas analíticas sobre el Data Warehouse (sleep_dw.sqlite).

Todas las consultas excluyen las épocas marcadas como artefacto.
El almacén solo tiene las 5 etapas puntuadas (W, N1, N2, N3, REM): las épocas sin
etapa (MOVE y UNK) no se cargan en las bases.

Los resultados son descriptivos: una diferencia de medias no implica
significancia estadística (no se hacen tests ni se modela la dependencia
entre epochs consecutivos del mismo sujeto).
"""

from __future__ import annotations

import sqlite3

import pandas as pd

from src import config

_FROM_STAR = """
FROM fact_eeg_epoch f
JOIN dim_recording   r  ON r.recording_key  = f.recording_key
JOIN dim_channel     c  ON c.channel_key    = f.channel_key
JOIN dim_sleep_stage st ON st.stage_key     = f.stage_key
"""
_ANALYSIS_FILTER = "WHERE f.is_artifact = 0"
_MEASURES = """COUNT(*) AS n, COUNT(DISTINCT r.subject_id) AS n_subjects,
               AVG(f.sample_entropy) AS sample_entropy, AVG(f.delta_rel) AS delta_rel, AVG(f.sigma_rel) AS sigma_rel"""

QUERIES: dict[str, str] = {
    # 1. Sample Entropy promedio por etapa (y canal: los canales no se mezclan).
    "sample_entropy_by_stage": f"""
        SELECT st.stage_code, c.channel_name AS channel,
               COUNT(f.sample_entropy) AS n, AVG(f.sample_entropy) AS mean_sample_entropy,
               MIN(f.sample_entropy) AS min_value, MAX(f.sample_entropy) AS max_value
        {_FROM_STAR} {_ANALYSIS_FILTER}
        GROUP BY st.stage_code, st.stage_key, c.channel_name
        ORDER BY st.stage_key, channel""",

    # 2. Potencia relativa de cada banda por etapa.
    "relative_band_power_by_stage": f"""
        SELECT st.stage_code, c.channel_name AS channel, COUNT(*) AS n,
               AVG(f.delta_rel) AS delta, AVG(f.theta_rel) AS theta, AVG(f.alpha_rel) AS alpha,
               AVG(f.sigma_rel) AS sigma, AVG(f.beta_rel) AS beta
        {_FROM_STAR} {_ANALYSIS_FILTER}
        GROUP BY st.stage_code, st.stage_key, c.channel_name
        ORDER BY st.stage_key, channel""",

    # 3. Cubo: una celda por etapa × grupo etario × canal.
    "cube": f"""
        SELECT st.stage_code, r.age_group, c.channel_name AS channel,
               {_MEASURES}
        {_FROM_STAR} {_ANALYSIS_FILTER}
        GROUP BY st.stage_code, st.stage_key, r.age_group, c.channel_name
        ORDER BY st.stage_key, MIN(r.age), channel""",

    # 4. El cubo con la etapa fija en N2, por grupo etario y canal. Responde la pregunta 2.
    "n2_by_age_group": f"""
        SELECT r.age_group, c.channel_name AS channel,
               {_MEASURES}
        {_FROM_STAR} {_ANALYSIS_FILTER} AND st.stage_code = 'N2'
        GROUP BY r.age_group, c.channel_name
        ORDER BY MIN(r.age), channel""",

    # 5. Dentro de N2, un valor por sujeto en lugar de por grupo etario. Responde la pregunta 2.
    "n2_by_subject": f"""
        SELECT r.age_group, r.subject_id, r.age, r.sex, c.channel_name AS channel,
               {_MEASURES}
        {_FROM_STAR} {_ANALYSIS_FILTER} AND st.stage_code = 'N2'
        GROUP BY r.age_group, r.subject_id, r.age, r.sex, c.channel_name
        ORDER BY r.age, channel""",
}

# Datos a nivel fila para gráficos de distribución, hipnograma y dashboard.
OBSERVATIONS_SQL = f"""
SELECT r.age_group, r.subject_id, r.age, r.sex, r.recording_id, c.channel_name AS channel,
       f.epoch_number, f.hours_since_sleep_onset,
       st.stage_code,
       f.delta_abs, f.theta_abs, f.alpha_abs, f.sigma_abs, f.beta_abs,
       f.delta_rel, f.theta_rel, f.alpha_rel, f.sigma_rel, f.beta_rel, f.total_power,
       f.sample_entropy, f.rms, f.peak_to_peak,
       f.is_artifact, f.is_stat_outlier
{_FROM_STAR}
ORDER BY r.recording_id, f.epoch_number, c.channel_name
"""


def run_query(name: str) -> pd.DataFrame:
    """Ejecuta una consulta nombrada de QUERIES y devuelve un DataFrame."""
    with sqlite3.connect(config.DW_DB_PATH) as conn:
        result = pd.read_sql(QUERIES[name], conn)
    conn.close()
    return result


def load_observations() -> pd.DataFrame:
    """Todas las observaciones (época x canal) con su contexto, desde el DW."""
    with sqlite3.connect(config.DW_DB_PATH) as conn:
        obs = pd.read_sql(OBSERVATIONS_SQL, conn)
    conn.close()
    obs[["is_artifact", "is_stat_outlier"]] = obs[["is_artifact", "is_stat_outlier"]].astype(bool)
    return obs
