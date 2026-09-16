"""Constantes y rutas del proyecto."""

from pathlib import Path

# --------------------------------------------------------------------------
# Rutas del repositorio
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

RAW_CSV = DATA_RAW / "My Library.csv"
SQLITE_DB = DATA_PROCESSED / "zotero_library.db"
