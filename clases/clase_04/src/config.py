"""Constantes y rutas del proyecto."""

from pathlib import Path

# --------------------------------------------------------------------------
# Rutas del repositorio
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = DATA_PROCESSED / "figures"

RAW_CSV = DATA_RAW / "wine.csv"
PCA_SCORES_CSV = DATA_PROCESSED / "wine_pca_scores.csv"

# --------------------------------------------------------------------------
# Variables del dataset
# --------------------------------------------------------------------------
# Columna con el cultivar (la clase) de cada vino.
TARGET = "cultivar"
CLASS_NAMES = ["class_0", "class_1", "class_2"]

# Las 13 variables químicas continuas, con su etiqueta para los gráficos.
# sklearn llama a la anteúltima "od280/od315_of_diluted_wines"; se renombra
# para que sea un identificador cómodo.
FEATURE_LABELS = {
    "alcohol": "Alcohol",
    "malic_acid": "Ácido málico",
    "ash": "Cenizas",
    "alcalinity_of_ash": "Alcalinidad de las cenizas",
    "magnesium": "Magnesio",
    "total_phenols": "Fenoles totales",
    "flavanoids": "Flavonoides",
    "nonflavanoid_phenols": "Fenoles no flavonoides",
    "proanthocyanins": "Proantocianidinas",
    "color_intensity": "Intensidad de color",
    "hue": "Matiz",
    "od280_od315": "OD280/OD315 de vinos diluidos",
    "proline": "Prolina",
}
FEATURES = list(FEATURE_LABELS)

# Variables indicadoras del cultivar: con 3 clases alcanzan 2 (class_2 queda
# como categoría de referencia).
DUMMY_COLUMNS = ["x_class_0", "x_class_1"]

# Subconjunto de columnas sobre el que se calculan covarianzas, correlaciones
# y el PCA.
ANALYSIS_COLUMNS = FEATURES + DUMMY_COLUMNS

# --------------------------------------------------------------------------
# Estilo de los gráficos
# --------------------------------------------------------------------------
# Un color fijo por cultivar, el mismo en todos los gráficos.
PALETTE = {"class_0": "#2a78d6", "class_1": "#eb6834", "class_2": "#1baf7a"}

# Escala divergente para correlaciones: azul (negativa) - gris - rojo (positiva).
DIVERGING_COLORS = ["#104281", "#2a78d6", "#f0efec", "#e34948", "#8f1f1f"]

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
