from src.database import conectar_db


def crear_tablas():

    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Dim_Actor (
                Actor_ID INTEGER PRIMARY KEY,
                Nombre TEXT,
                CountryCode TEXT,
                TypeCode TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Dim_Tiempo (
                Time_ID INTEGER PRIMARY KEY,
                Fecha TEXT NOT NULL,
                Dia INTEGER,
                Mes INTEGER,
                Anio INTEGER,
                Es_Fin_Semana INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Dim_Interaccion (
                EventCode TEXT PRIMARY KEY,
                EventBaseCode TEXT,
                EventRootCode TEXT,
                QuadClass INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Dim_Geografia (
                Geo_ID INTEGER PRIMARY KEY,
                CountryCode TEXT,
                RegionCode TEXT,
                FullName TEXT,
                Latitude REAL,
                Longitude REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Fact_Evento (
                GlobalEventID INTEGER PRIMARY KEY,
                Time_ID INTEGER,
                Actor1_ID INTEGER,
                Actor2_ID INTEGER,
                EventCode TEXT,
                Geo_ID INTEGER,
                IsRootEvent INTEGER,
                GoldsteinScale REAL,
                NumMentions INTEGER,
                NumSources INTEGER,
                NumArticles INTEGER,
                AvgTone REAL,
                DATEADDED TEXT,
                SOURCEURL TEXT,

                FOREIGN KEY (Time_ID)
                    REFERENCES Dim_Tiempo(Time_ID),

                FOREIGN KEY (Actor1_ID)
                    REFERENCES Dim_Actor(Actor_ID),

                FOREIGN KEY (Actor2_ID)
                    REFERENCES Dim_Actor(Actor_ID),

                FOREIGN KEY (EventCode)
                    REFERENCES Dim_Interaccion(EventCode),

                FOREIGN KEY (Geo_ID)
                    REFERENCES Dim_Geografia(Geo_ID)
            )
        """)

        conexion.commit()

    finally:
        conexion.close()
    
def crear_dimensiones():

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Dim_Actor (
            Actor_ID INTEGER PRIMARY KEY,
            Nombre TEXT,
            CountryCode TEXT,
            TypeCode TEXT
        )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Dim_Tiempo (
        Time_ID INTEGER PRIMARY KEY,
        Fecha TEXT NOT NULL,
        Dia INTEGER,
        Mes INTEGER,
        Anio INTEGER,
        Es_Fin_Semana INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Dim_Interaccion (
        EventCode TEXT PRIMARY KEY,
        EventBaseCode TEXT,
        EventRootCode TEXT,
        QuadClass INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Dim_Geografia (
        Geo_ID INTEGER PRIMARY KEY,
        CountryCode TEXT,
        RegionCode TEXT,
        FullName TEXT,
        Latitude REAL,
        Longitude REAL
    )
    """)

    conexion.commit()
    conexion.close()
    
def crear_tabla_hechos():

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Fact_Evento (

            GlobalEventID INTEGER PRIMARY KEY,

            Time_ID INTEGER,
            Actor1_ID INTEGER,
            Actor2_ID INTEGER,
            EventCode TEXT,
            Geo_ID INTEGER,

            IsRootEvent INTEGER,
            GoldsteinScale REAL,
            NumMentions INTEGER,
            NumSources INTEGER,
            NumArticles INTEGER,
            AvgTone REAL,

            DATEADDED TEXT,
            SOURCEURL TEXT,

            FOREIGN KEY (Time_ID)
                REFERENCES Dim_Tiempo(Time_ID),

            FOREIGN KEY (Actor1_ID)
                REFERENCES Dim_Actor(Actor_ID),

            FOREIGN KEY (Actor2_ID)
                REFERENCES Dim_Actor(Actor_ID),

            FOREIGN KEY (EventCode)
                REFERENCES Dim_Interaccion(EventCode),

            FOREIGN KEY (Geo_ID)
                REFERENCES Dim_Geografia(Geo_ID)
        )
    """)

    conexion.commit()
    conexion.close()
    
def crear_vista_eventos():

    conexion = conectar_db()

    try:
        conexion.execute("""
            CREATE VIEW IF NOT EXISTS Vista_Eventos AS

            SELECT
                E.GlobalEventID,
                T.Fecha,
                A1.Nombre AS Actor1,
                A1.CountryCode AS PaisActor1,
                A2.Nombre AS Actor2,
                A2.CountryCode AS PaisActor2,
                I.EventCode,
                I.QuadClass,
                G.FullName AS Ubicacion,
                G.CountryCode AS PaisEvento,
                E.AvgTone,
                E.GoldsteinScale,
                E.NumMentions,
                E.NumArticles

            FROM Fact_Evento AS E

            LEFT JOIN Dim_Tiempo AS T
                ON E.Time_ID = T.Time_ID

            LEFT JOIN Dim_Actor AS A1
                ON E.Actor1_ID = A1.Actor_ID

            LEFT JOIN Dim_Actor AS A2
                ON E.Actor2_ID = A2.Actor_ID

            LEFT JOIN Dim_Interaccion AS I
                ON E.EventCode = I.EventCode

            LEFT JOIN Dim_Geografia AS G
                ON E.Geo_ID = G.Geo_ID
        """)

        conexion.commit()

    finally:
        conexion.close()