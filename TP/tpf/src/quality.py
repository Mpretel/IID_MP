"""Control de calidad: artefactos de señal y outliers estadísticos.

Distinción metodológica central:
  - ARTEFACTO DE SEÑAL: el registro no refleja actividad cerebral (electrodo
    suelto -> señal plana, saturación del conversor -> señal recortada,
    valores no finitos). Se detecta con criterios *físicos* sobre la señal y se
    marca con `is_artifact` / `artifact_reason`. Las filas se CONSERVAN.
  - OUTLIER ESTADÍSTICO: valor extremo respecto de la distribución
    (regla de Tukey, 1.5·IQR). Puede ser fisiología real (p. ej. ondas lentas
    de gran amplitud en N3), por eso es solo informativo y NUNCA elimina filas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config

ARTIFACT_NON_FINITE = "non_finite"
ARTIFACT_FLAT = "flat_signal"
ARTIFACT_CLIPPED = "clipped"

# Para potencias (fuertemente asimétricas a la derecha) la regla de Tukey se
# aplica sobre log10; en escala lineal casi toda la cola superior sería "outlier".
_LOG_SCALE_SUFFIXES = ("_abs", "total_power")
IQR_FEATURES = ["delta_abs", "total_power", "delta_rel", "alpha_rel",
                "sample_entropy", "rms", "peak_to_peak"]
IQR_FACTOR = 1.5


def flag_artifacts(epochs_uv: np.ndarray, n_clipped: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Marca artefactos por (epoch, canal) a partir de la señal filtrada en µV.

    `n_clipped` son las muestras saturadas de cada (epoch, canal), contadas sobre
    la señal sin filtrar (ver count_clipped_samples).

    Criterios (umbrales en config):
      - non_finite: algún valor NaN/inf;
      - flat_signal: desvío estándar < ARTIFACT_MIN_STD_UV (electrodo desconectado);
      - clipped: al menos ARTIFACT_MIN_CLIPPED_SAMPLES muestras en el límite
        físico del EDF. Un umbral de pico a pico no sirve: el rango físico
        (como máximo ±248 µV) recorta la señal antes de alcanzarlo.

    Devuelve (is_artifact bool, artifact_reason str) de forma (n_epochs, n_canales).
    Si se cumplen varios criterios, los motivos se concatenan con ';'.
    """
    finite = np.isfinite(epochs_uv).all(axis=-1)
    with np.errstate(invalid="ignore"):
        checks = {
            ARTIFACT_NON_FINITE: ~finite,
            ARTIFACT_FLAT: finite & (np.std(epochs_uv, axis=-1) < config.ARTIFACT_MIN_STD_UV),
            ARTIFACT_CLIPPED: finite & (n_clipped >= config.ARTIFACT_MIN_CLIPPED_SAMPLES),
        }
    reasons = np.full(finite.shape, "", dtype=object)
    for name, mask in checks.items():
        reasons[mask] = np.where(reasons[mask] == "", name, reasons[mask] + ";" + name)
    is_artifact = reasons != ""
    reasons[~is_artifact] = None
    return is_artifact, reasons


def flag_statistical_outliers(features: pd.DataFrame,
                              group_cols: list[str] = ["recording_id", "channel", "stage"]) -> pd.DataFrame:
    """Agrega `outlier_features`: lista de features fuera de [Q1 - 1.5·IQR, Q3 + 1.5·IQR].

    Se calcula dentro de cada grupo registro × canal × etapa: las distribuciones
    difieren legítimamente entre etapas (N3 tiene más delta que REM por definición)
    y entre noches. Con una referencia entre registros, la regla marca personas o
    ganancias del equipo, no epochs raros. Excluye artefactos del cálculo de
    cuartiles. Solo informativo.
    """
    flags = pd.DataFrame(False, index=features.index, columns=IQR_FEATURES)
    clean = ~features["is_artifact"]
    for col in IQR_FEATURES:
        values = features[col]
        if col.endswith(_LOG_SCALE_SUFFIXES):
            values = np.log10(values.where(values > 0))
        # Cuartiles por grupo usando solo filas limpias; luego se asignan a todas las filas del grupo.
        quartiles = (values[clean]
                     .groupby([features.loc[clean, c] for c in group_cols])
                     .quantile([0.25, 0.75]).unstack())
        quartiles.columns = ["q1", "q3"]
        bounds = features[group_cols].join(quartiles, on=group_cols)
        iqr = bounds["q3"] - bounds["q1"]
        flags[col] = (values < bounds["q1"] - IQR_FACTOR * iqr) | (values > bounds["q3"] + IQR_FACTOR * iqr)
    out = features.copy()
    out["outlier_features"] = flags.apply(lambda row: ";".join(flags.columns[row]) or None, axis=1)
    out["is_stat_outlier"] = out["outlier_features"].notna()
    return out


def count_clipped_samples(epochs_uv: np.ndarray, low_uv: float, high_uv: float, tolerance_uv: float) -> np.ndarray:
    """Cuenta, por epoch, las muestras en el límite físico del EDF (saturación del conversor).

    `epochs_uv` debe ser la señal SIN filtrar de un canal, (n_epochs, n_muestras): el filtro
    redondea las mesetas. `tolerance_uv` es un paso de cuantización.
    """
    return ((epochs_uv >= high_uv - tolerance_uv) | (epochs_uv <= low_uv + tolerance_uv)).sum(axis=-1)


# ---------------------------------------------------------------------------
# Resumen de los outliers de Tukey (tabla y datos del gráfico del notebook)
# ---------------------------------------------------------------------------
def _plain(tidy: pd.DataFrame) -> pd.DataFrame:
    """Copia con claves de texto, para agrupar sin combinaciones vacías de categorías."""
    return tidy.astype({"sleep_stage": str, "channel": str, "recording_id": str})


def tukey_rate_by_metric(tidy: pd.DataFrame) -> pd.DataFrame:
    """% de épocas marcadas por Tukey en cada variable (filas) y etapa (columnas).

    Usa las marcas del pipeline (`outlier_features`), que se calculan dentro de cada
    registro × canal × etapa. Excluye artefactos y épocas sin etapa.
    """
    data = _plain(tidy[~tidy["is_artifact"] & tidy["sleep_stage"].isin(config.SCORED_STAGES)])
    flags = (data["outlier_features"].fillna("").str.get_dummies(sep=";")
             .reindex(columns=IQR_FEATURES, fill_value=0))
    rates = 100 * flags.groupby(data["sleep_stage"]).mean().T
    return rates[config.SCORED_STAGES].round(1)


def tukey_view(tidy: pd.DataFrame, recording_id: str, channel: str) -> pd.DataFrame:
    """Valores y límites de Tukey de un registro y canal, en formato largo (una fila por época y variable).

    Los límites se recalculan como en flag_statistical_outliers (por etapa, con log10
    en las potencias absolutas y la total, sin artefactos), solo para dibujarlos. Si una época
    está marcada se toma de `outlier_features`, la marca real del pipeline.
    """
    data = _plain(tidy)
    data = data[(data["recording_id"] == recording_id) & (data["channel"] == channel)
                & ~data["is_artifact"] & data["sleep_stage"].isin(config.SCORED_STAGES)]
    marked = data["outlier_features"].fillna("").str.split(";")
    parts = []
    for metric in IQR_FEATURES:
        log = metric.endswith(_LOG_SCALE_SUFFIXES)
        values = np.log10(data[metric]) if log else data[metric]
        part = pd.DataFrame({"epoch_number": data["epoch_number"], "stage": data["sleep_stage"],
                             "metric": metric, "log10": log, "value": values,
                             "is_outlier": marked.map(lambda names: metric in names)})
        grouped = part.groupby("stage")["value"]
        part["q1"], part["median"], part["q3"] = (grouped.transform(lambda s, q=q: s.quantile(q)) for q in (0.25, 0.5, 0.75))
        iqr = part["q3"] - part["q1"]
        part["low"], part["high"] = part["q1"] - IQR_FACTOR * iqr, part["q3"] + IQR_FACTOR * iqr
        parts.append(part)
    return pd.concat(parts, ignore_index=True)
