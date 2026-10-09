import pandas as pd

def transformar_actores(df):

    # Extraer los actores de la primera posición
    actor1 = df[[
        "Actor1Name",
        "Actor1CountryCode",
        "Actor1Type1Code"
    ]].copy()

    actor1.columns = [
        "Nombre",
        "CountryCode",
        "TypeCode"
    ]

    # Extraer los actores de la segunda posición
    actor2 = df[[
        "Actor2Name",
        "Actor2CountryCode",
        "Actor2Type1Code"
    ]].copy()

    actor2.columns = [
        "Nombre",
        "CountryCode",
        "TypeCode"
    ]

    # Unificar ambas listas
    actores = pd.concat(
        [actor1, actor2],
        ignore_index=True
    )

    # Eliminar registros sin nombre de actor
    actores = actores.dropna(subset=["Nombre"])

    # Normalizar campos de texto
    for columna in ["Nombre", "CountryCode", "TypeCode"]:
        actores[columna] = (
            actores[columna]
            .astype("string")
            .str.strip()
        )

    # Eliminar nombres vacíos
    actores["Nombre"] = actores["Nombre"].replace("", pd.NA)

    # Eliminar registros sin nombre
    actores = actores.dropna(subset=["Nombre"])

    # Priorizar registros con TypeCode informado
    actores = actores.sort_values(
        by="TypeCode",
        na_position="last"
    )

    # Identificar actores por nombre y país
    actores = actores.drop_duplicates(
        subset=["Nombre", "CountryCode"],
        keep="first"
    )

    actores = actores.reset_index(drop=True)

    return actores

def asociar_actores(df, dim_actor_db):

    # Copiar los eventos originales
    eventos = df.copy()

    # Normalizar las columnas que se usarán como claves
    for columna in [
        "Actor1Name",
        "Actor1CountryCode",
        "Actor2Name",
        "Actor2CountryCode"
    ]:
        eventos[columna] = (
            eventos[columna]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Primer JOIN: Actor1
    eventos = eventos.merge(
        dim_actor_db[
            ["Actor_ID", "Nombre", "CountryCode"]
        ],
        how="left",
        left_on=[
            "Actor1Name",
            "Actor1CountryCode"
        ],
        right_on=[
            "Nombre",
            "CountryCode"
        ],
        validate="many_to_one"
    )

    eventos = eventos.rename(
        columns={"Actor_ID": "Actor1_ID"}
    )

    eventos = eventos.drop(
        columns=["Nombre", "CountryCode"]
    )

    # Segundo JOIN: Actor2
    eventos = eventos.merge(
        dim_actor_db[
            ["Actor_ID", "Nombre", "CountryCode"]
        ],
        how="left",
        left_on=[
            "Actor2Name",
            "Actor2CountryCode"
        ],
        right_on=[
            "Nombre",
            "CountryCode"
        ],
        validate="many_to_one"
    )

    eventos = eventos.rename(
        columns={"Actor_ID": "Actor2_ID"}
    )

    eventos = eventos.drop(
        columns=["Nombre", "CountryCode"]
    )

    return eventos

def transformar_tiempo(df):

    # Obtener las fechas únicas
    fechas = df[["SQLDATE"]].drop_duplicates().copy()

    # Convertir SQLDATE a fecha
    fechas["Fecha"] = pd.to_datetime(
        fechas["SQLDATE"].astype("string"),
        format="%Y%m%d",
        errors="raise"
    )

    # Extraer los componentes
    fechas["Dia"] = fechas["Fecha"].dt.day
    fechas["Mes"] = fechas["Fecha"].dt.month
    fechas["Anio"] = fechas["Fecha"].dt.year

    # Lunes = 0, ..., domingo = 6
    fechas["Es_Fin_Semana"] = (
        fechas["Fecha"].dt.dayofweek >= 5
    ).astype(int)

    # Crear la clave primaria
    fechas = fechas.rename(
        columns={"SQLDATE": "Time_ID"}
    )

    # Guardar la fecha como texto ISO
    fechas["Fecha"] = fechas["Fecha"].dt.strftime(
        "%Y-%m-%d"
    )

    return fechas.reset_index(drop=True)

def asociar_tiempo(eventos):

    eventos = eventos.copy()

    eventos["Time_ID"] = eventos["SQLDATE"]

    return eventos

def transformar_interacciones(df):

    columnas = [
        "EventCode",
        "EventBaseCode",
        "EventRootCode",
        "QuadClass"
    ]

    interacciones = df[columnas].copy()

    # Conservar los códigos como texto
    for columna in [
        "EventCode",
        "EventBaseCode",
        "EventRootCode"
    ]:
        interacciones[columna] = (
            interacciones[columna]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Convertir QuadClass a entero nullable
    interacciones["QuadClass"] = pd.to_numeric(
        interacciones["QuadClass"],
        errors="coerce"
    ).astype("Int64")

    # No podemos identificar interacciones sin EventCode
    interacciones = interacciones.dropna(
        subset=["EventCode"]
    )

    # Conservar una fila por código de evento
    interacciones = interacciones.drop_duplicates(
        subset=["EventCode"]
    )

    return interacciones.reset_index(drop=True)

def asociar_interaccion(eventos):

    eventos = eventos.copy()

    eventos["EventCode"] = (
        eventos["EventCode"]
        .astype("string")
        .str.strip()
    )

    return eventos

def transformar_geografia(df):

    columnas = {
        "ActionGeo_FullName": "FullName",
        "ActionGeo_CountryCode": "CountryCode",
        "ActionGeo_ADM1Code": "RegionCode",
        "ActionGeo_Lat": "Latitude",
        "ActionGeo_Long": "Longitude"
    }

    geografia = df[list(columnas)].rename(
        columns=columnas
    ).copy()

    # Normalizar campos de texto
    for columna in ["FullName", "CountryCode", "RegionCode"]:
        geografia[columna] = (
            geografia[columna]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Eliminar ubicaciones sin información identificable
    geografia = geografia.dropna(
        subset=["FullName", "CountryCode", "RegionCode"],
        how="all"
    )

    # Convertir coordenadas a números
    for columna in ["Latitude", "Longitude"]:
        geografia[columna] = pd.to_numeric(
            geografia[columna],
            errors="coerce"
        )

    # Una fila por combinación geográfica
    geografia = geografia.drop_duplicates(
        subset=["FullName", "CountryCode", "RegionCode"]
    )

    return geografia.reset_index(drop=True)

def asociar_geografia(eventos, dim_geografia_db):

    eventos = eventos.copy()

    columnas = {
        "ActionGeo_FullName": "FullName",
        "ActionGeo_CountryCode": "CountryCode",
        "ActionGeo_ADM1Code": "RegionCode"
    }

    # Normalizar claves del lado de los eventos
    for columna in columnas:
        eventos[columna] = (
            eventos[columna]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Normalizar claves del lado de la dimensión
    geo = dim_geografia_db[
        ["Geo_ID", "FullName", "CountryCode", "RegionCode"]
    ].copy()

    for columna in ["FullName", "CountryCode", "RegionCode"]:
        geo[columna] = (
            geo[columna]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Evitar asignar una ubicación cuando no existe
    # ninguna información geográfica
    sin_ubicacion = eventos[
        list(columnas)
    ].isna().all(axis=1)

    eventos = eventos.merge(
        geo,
        how="left",
        left_on=list(columnas),
        right_on=list(columnas.values()),
        validate="many_to_one"
    )

    eventos.loc[sin_ubicacion, "Geo_ID"] = pd.NA

    eventos = eventos.drop(
        columns=["FullName", "CountryCode", "RegionCode"]
    )

    return eventos

def transformar_hechos(eventos):

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

    hechos = eventos[columnas].copy()

    # Identificadores enteros
    columnas_enteras = [
        "GlobalEventID",
        "Time_ID",
        "Actor1_ID",
        "Actor2_ID",
        "Geo_ID",
        "IsRootEvent",
        "NumMentions",
        "NumSources",
        "NumArticles"
    ]

    for columna in columnas_enteras:
        hechos[columna] = pd.to_numeric(
            hechos[columna],
            errors="coerce"
        ).astype("Int64")

    # Medidas continuas
    for columna in ["GoldsteinScale", "AvgTone"]:
        hechos[columna] = pd.to_numeric(
            hechos[columna],
            errors="coerce"
        )

    # Código de interacción como texto
    hechos["EventCode"] = (
        hechos["EventCode"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    # Campos de texto
    for columna in ["DATEADDED", "SOURCEURL"]:
        hechos[columna] = (
            hechos[columna]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # La clave primaria no puede faltar
    hechos = hechos.dropna(
        subset=["GlobalEventID"]
    )

    # Una fila por evento
    hechos = hechos.drop_duplicates(
        subset=["GlobalEventID"]
    )

    return hechos.reset_index(drop=True)