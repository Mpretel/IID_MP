import pandas as pd

from src.database import conectar_db


def ejecutar_consulta(consulta, parametros=None):

    conexion = conectar_db()

    try:
        resultado = pd.read_sql_query(
            consulta,
            conexion,
            params=parametros
        )

        return resultado

    finally:
        conexion.close()