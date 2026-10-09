import sqlite3
from pathlib import Path

# Directorio principal del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Ubicación de la base de datos
DB_PATH = BASE_DIR / "data" / "gdelt.db"


def conectar_db():
    """Crea una conexión a la base de datos SQLite."""
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion