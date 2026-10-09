from src.database import conectar_db


def cargar_datos_prueba():

    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        # 1. Actores
        actores = [
            (1, "Gobierno Argentina", "ARG", "GOV"),
            (2, "Gobierno Brasil", "BRA", "GOV"),
            (3, "Organización Internacional", "USA", "IGO")
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO Dim_Actor
            (Actor_ID, Nombre, CountryCode, TypeCode)
            VALUES (?, ?, ?, ?)
        """, actores)

        # 2. Tiempo
        fechas = [
            (20261006, "2026-10-06", 6, 10, 2026, 0),
            (20261007, "2026-10-07", 7, 10, 2026, 0),
            (20261008, "2026-10-08", 8, 10, 2026, 0)
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO Dim_Tiempo
            (Time_ID, Fecha, Dia, Mes, Anio, Es_Fin_Semana)
            VALUES (?, ?, ?, ?, ?, ?)
        """, fechas)

        # 3. Interacciones
        interacciones = [
            ("042", "042", "04", 1),
            ("051", "051", "05", 1),
            ("036", "036", "03", 1)
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO Dim_Interaccion
            (EventCode, EventBaseCode, EventRootCode, QuadClass)
            VALUES (?, ?, ?, ?)
        """, interacciones)

        # 4. Geografía
        ubicaciones = [
            (1, "ARG", "AR", "Buenos Aires, Argentina",
             -34.6037, -58.3816),
            (2, "BRA", "BR", "Brasília, Brasil",
             -15.7939, -47.8828)
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO Dim_Geografia
            (Geo_ID, CountryCode, RegionCode,
             FullName, Latitude, Longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ubicaciones)

        # 5. Tabla de hechos
        eventos = [
            (1001, 20261006, 1, 2, "042", 1, -2.5, 3.0),
            (1002, 20261007, 1, 3, "051", 1,  3.2, 5.0),
            (1003, 20261008, 2, 3, "036", 2,  1.8, 2.0)
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO Fact_Evento
            (GlobalEventID, Time_ID, Actor1_ID, Actor2_ID,
             EventCode, Geo_ID, AvgTone, GoldsteinScale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, eventos)

        conexion.commit()
        print("Datos de prueba cargados correctamente")

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()