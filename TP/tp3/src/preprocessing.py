"""Preparación de eventos GDELT para análisis multivariante."""
import pandas as pd

VARIABLES_CATEGORICAS = ('PaisActor1', 'PaisActor2', 'EventCode', 'PaisEvento')
VARIABLES_NUMERICAS = ('AvgTone', 'GoldsteinScale')


def seleccionar_variables(eventos):
    """Conserva las columnas de interés sin modificar el DataFrame de entrada."""
    columnas = list(VARIABLES_CATEGORICAS + VARIABLES_NUMERICAS)
    faltantes = set(columnas) - set(eventos.columns)
    if faltantes:
        raise ValueError(f'Faltan columnas: {sorted(faltantes)}')
    return eventos.loc[:, columnas].copy()


def agrupar_categorias(df, umbral=0.05):
    """Reemplaza categorías con frecuencia estrictamente menor al umbral por OTHER."""
    if not 0 <= umbral <= 1:
        raise ValueError('umbral debe estar entre 0 y 1')
    resultado = df.copy()
    for columna in VARIABLES_CATEGORICAS:
        valores = resultado[columna].astype('string').fillna('UNKNOWN')
        valores = valores.str.strip().replace('', 'UNKNOWN')
        frecuencia = valores.value_counts(normalize=True)
        frecuentes = frecuencia[frecuencia >= umbral].index
        resultado[columna] = valores.where(valores.isin(frecuentes), 'OTHER').astype(str)
    return resultado


def generar_dummies(df, drop_first=False):
    """One-hot encoding. Por defecto conserva todas las categorías."""
    return pd.get_dummies(df, columns=list(VARIABLES_CATEGORICAS),
                          dtype=int, drop_first=drop_first)


def limpiar_variables_numericas(df):
    """Convierte variables numéricas y descarta filas sin valores válidos."""
    resultado = df.copy()
    for columna in VARIABLES_NUMERICAS:
        resultado[columna] = pd.to_numeric(resultado[columna], errors='coerce')
    return resultado.dropna(subset=list(VARIABLES_NUMERICAS)).copy()


def preparar_datos(eventos, umbral=0.05, drop_first=False):
    """Devuelve (categorías agrupadas, matriz numérica) con índices alineados.

    Las filas con valores numéricos inválidos se descartan ANTES de calcular
    frecuencias; los índices originales se conservan para asociar países.
    """
    df = limpiar_variables_numericas(seleccionar_variables(eventos))
    df = agrupar_categorias(df, umbral=umbral)
    matriz = generar_dummies(df, drop_first=drop_first)
    return df, matriz
