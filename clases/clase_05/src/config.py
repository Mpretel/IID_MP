"""Constantes y rutas del proyecto."""

from pathlib import Path

# --------------------------------------------------------------------------
# Rutas del repositorio
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

RAW_CSV = DATA_RAW / "cardiotocography.csv"
COMPARISON_CSV = DATA_PROCESSED / "comparacion_metodos.csv"

# CSV del dataset en UCI (el mismo que descarga ``ucimlrepo``).
DATA_URL = "https://archive.ics.uci.edu/static/public/193/data.csv"

# --------------------------------------------------------------------------
# Variables del dataset
# --------------------------------------------------------------------------
# Las 21 variables medidas sobre cada cardiotocograma (CTG).
FEATURES = [
    "LB", "AC", "FM", "UC", "DL", "DS", "DP", "ASTV", "MSTV", "ALTV", "MLTV",
    "Width", "Min", "Max", "Nmax", "Nzeros", "Mode", "Mean", "Median",
    "Variance", "Tendency",
]

# Estado fetal según los obstetras: 1 = normal, 2 = sospechoso, 3 = patológico.
# Se considera anomalía todo CTG no normal (NSP > 1).
TARGET = "NSP"

# Variables expresadas como eventos por segundo (aceleraciones, movimientos,
# contracciones y desaceleraciones). Se pasan a eventos cada 1000 s antes del
# logaritmo: con valores del orden de 0,001, log(1 + x) sería casi x.
RATE_FEATURES = ["AC", "FM", "UC", "DL", "DS", "DP"]
RATE_FACTOR = 1000

# Variables con cola larga a la derecha, que entran en escala log(1 + x).
SKEWED_FEATURES = RATE_FEATURES + ["MSTV", "ALTV", "MLTV", "Nzeros", "Variance"]

# Variables con interpretación clínica directa del bienestar fetal: frecuencia
# basal, aceleraciones, desaceleraciones y variabilidad de corto y largo plazo.
CLINICAL_FEATURES = ["LB", "AC", "DL", "DS", "DP", "ASTV", "MSTV", "ALTV"]

# Dirección de riesgo de cada variable clínica, según el criterio clínico (no
# según las etiquetas): +1 = valores altos son de riesgo, -1 = valores bajos
# son de riesgo, 0 = cualquier desvío de la frecuencia basal es de riesgo.
RISK_DIRECTION = {
    "LB": 0,     # taquicardia o bradicardia
    "AC": -1,    # ausencia de aceleraciones
    "DL": 1,     # desaceleraciones leves
    "DS": 1,     # desaceleraciones severas
    "DP": 1,     # desaceleraciones prolongadas
    "ASTV": 1,   # % de tiempo con variabilidad de corto plazo anormal
    "MSTV": -1,  # variabilidad de corto plazo reducida
    "ALTV": 1,   # % de tiempo con variabilidad de largo plazo anormal
}

# --------------------------------------------------------------------------
# Umbrales
# --------------------------------------------------------------------------
# Proporción de registros que se marcan como anomalías al comparar métodos
# con el mismo umbral (la que usa el notebook de clase en LOF e Isolation
# Forest).
CONTAMINATION = 0.05

RANDOM_STATE = 42

# --------------------------------------------------------------------------
# Estilo de los gráficos (el mismo de la clase 04)
# --------------------------------------------------------------------------
FIGURES_DIR = DATA_PROCESSED / "figures"

# Colores categóricos en orden fijo: azul, naranja, aqua.
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
