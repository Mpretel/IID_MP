"""Constantes y rutas del proyecto."""

from pathlib import Path

# --------------------------------------------------------------------------
# Rutas del repositorio
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# --------------------------------------------------------------------------
# Parámetros de EEG y segmentación
# --------------------------------------------------------------------------
# Canal EEG estándar del dataset Sleep-EDF.
EEG_CHANNEL = "EEG Fpz-Cz"

# Cada época de sueño dura 30 s por convención (AASM).
EPOCH_DURATION = 30.0

# Mapeo de las anotaciones originales del hipnograma a un set reducido de
# etapas AASM (los estadios 3 y 4 se fusionan en N3).
STAGE_MAPPING = {
    "Sleep stage W": "W",
    "Sleep stage 1": "N1",
    "Sleep stage 2": "N2",
    "Sleep stage 3": "N3",
    "Sleep stage 4": "N3",
    "Sleep stage R": "REM",
}

# Orden fisiológico de las etapas (vigilia -> sueño profundo -> REM).
STAGE_ORDER = ["W", "N1", "N2", "N3", "REM"]

# Id numérico estable por etapa, usado para construir los eventos de MNE.
STAGE_IDS = {stage: i for i, stage in enumerate(STAGE_ORDER)}
