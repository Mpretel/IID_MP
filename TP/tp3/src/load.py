import pandas as pd

from src.database import conectar_db

def cargar_dim_actor(dim_actor):

    conexion = conectar_db()
    cursor = conexion.cursor()

    insertados = 0
    existentes = 0

    try:
        for actor in dim_actor.itertuples(index=False):

            nombre = actor.Nombre
            pais = actor.CountryCode
            tipo = actor.TypeCode

            # Convertir valores faltantes a None
            pais = None if pd.isna(pais) else pais
            tipo = None if pd.isna(tipo) else tipo

            # Buscar si el actor ya existe
            cursor.execute("""
                SELECT Actor_ID
                FROM Dim_Actor
                WHERE Nombre = ?
                  AND CountryCode IS ?
            """, (nombre, pais))

            resultado = cursor.fetchone()

            if resultado is not None:

                actor_id = resultado[0]
                existentes += 1

            else:

                # Insertar un nuevo actor
                cursor.execute("""
                    INSERT INTO Dim_Actor
                    (Nombre, CountryCode, TypeCode)
                    VALUES (?, ?, ?)
                """, (nombre, pais, tipo))

                actor_id = cursor.lastrowid
                insertados += 1

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()

    print("Actores insertados:", insertados)
    print("Actores existentes:", existentes)
    
def cargar_dim_tiempo(dim_tiempo):

    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        registros = list(
            dim_tiempo[[
                "Time_ID",
                "Fecha",
                "Dia",
                "Mes",
                "Anio",
                "Es_Fin_Semana"
            ]].itertuples(index=False, name=None)
        )

        cursor.executemany("""
            INSERT OR IGNORE INTO Dim_Tiempo
            (Time_ID, Fecha, Dia, Mes, Anio, Es_Fin_Semana)
            VALUES (?, ?, ?, ?, ?, ?)
        """, registros)

        insertados = cursor.rowcount

        conexion.commit()

        print("Fechas nuevas insertadas:", insertados)

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()
        
def cargar_dim_interaccion(dim_interaccion):

    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        registros = []

        for fila in dim_interaccion.itertuples(index=False):

            registros.append((
                fila.EventCode,
                None if pd.isna(fila.EventBaseCode)
                     else fila.EventBaseCode,
                None if pd.isna(fila.EventRootCode)
                     else fila.EventRootCode,
                None if pd.isna(fila.QuadClass)
                     else int(fila.QuadClass)
            ))

        cursor.executemany("""
            INSERT OR IGNORE INTO Dim_Interaccion
            (
                EventCode,
                EventBaseCode,
                EventRootCode,
                QuadClass
            )
            VALUES (?, ?, ?, ?)
        """, registros)

        insertados = cursor.rowcount

        conexion.commit()

        print("Interacciones nuevas insertadas:", insertados)

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()
        
def cargar_dim_geografia(dim_geografia):

    conexion = conectar_db()
    cursor = conexion.cursor()

    insertados = 0
    existentes = 0

    try:
        for geo in dim_geografia.itertuples(index=False):

            nombre = None if pd.isna(geo.FullName) else str(geo.FullName)
            pais = None if pd.isna(geo.CountryCode) else str(geo.CountryCode)
            region = None if pd.isna(geo.RegionCode) else str(geo.RegionCode)

            lat = None if pd.isna(geo.Latitude) else float(geo.Latitude)
            lon = None if pd.isna(geo.Longitude) else float(geo.Longitude)

            # Buscar ubicación existente
            cursor.execute("""
                SELECT Geo_ID
                FROM Dim_Geografia
                WHERE FullName IS ?
                  AND CountryCode IS ?
                  AND RegionCode IS ?
            """, (nombre, pais, region))

            resultado = cursor.fetchone()

            if resultado is not None:
                existentes += 1

            else:
                cursor.execute("""
                    INSERT INTO Dim_Geografia
                    (
                        FullName,
                        CountryCode,
                        RegionCode,
                        Latitude,
                        Longitude
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (nombre, pais, region, lat, lon))

                insertados += 1

        conexion.commit()

        print("Ubicaciones insertadas:", insertados)
        print("Ubicaciones existentes:", existentes)

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()
        
def cargar_fact_evento(fact_evento):

    conexion = conectar_db()

    columnas = [
        "GlobalEventID",
        "Time_ID",
        "Actor1_ID",
        "Actor2_ID",
        "EventCode",
        "Geo_ID",
        "IsRootEvent",
        "GoldsteinScale",
        "NumMentions",
        "NumSources",
        "NumArticles",
        "AvgTone",
        "DATEADDED",
        "SOURCEURL"
    ]

    try:
        cursor = conexion.cursor()

        registros = []

        for fila in fact_evento[columnas].itertuples(
            index=False,
            name=None
        ):
            # Convertir tipos pandas/numpy a tipos Python
            registro = tuple(
                None if pd.isna(valor)
                else valor.item() if hasattr(valor, "item")
                else valor
                for valor in fila
            )

            registros.append(registro)

        marcadores = ", ".join(["?"] * len(columnas))
        nombres = ", ".join(columnas)

        consulta = f"""
            INSERT OR IGNORE INTO Fact_Evento
            ({nombres})
            VALUES ({marcadores})
        """

        cursor.executemany(consulta, registros)

        insertados = cursor.rowcount

        conexion.commit()

        print("Eventos insertados:", insertados)
        print("Eventos ya existentes:", len(registros) - insertados)

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()