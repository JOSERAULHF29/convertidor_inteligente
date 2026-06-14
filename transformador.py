import pandas as pd
import re

def formatear_fecha(serie):
    serie = pd.to_datetime(serie, errors="coerce")

    # solo si existe AM/PM en español
    serie = serie.astype(str).str.lower()
    serie = serie.str.replace("a. m.", "AM", regex=False)
    serie = serie.str.replace("p. m.", "PM", regex=False)

    serie = pd.to_datetime(serie, errors="coerce")

    return serie.dt.strftime("%d/%m/%Y %H:%M")

def limpiar_nombre(c):
    return re.sub(r"\.\d+$", "", str(c)).strip()

def norm_col(c):
    return limpiar_nombre(c).lower().replace("\xa0", " ").strip()

def extraer_base_y_unidad(col):
    m = re.match(r"(.+?)\s*\((.+?)\)$", str(col))
    if m:
        return norm_col(m.group(1)), norm_col(m.group(2))
    return norm_col(col), ""

def procesar_jdlink(df, df_old):

    df_old.columns = [limpiar_nombre(c) for c in df_old.columns]

    mapeo = {
        "Utilización Trabajo": "Utilización En funcionamiento",
    }

    columnas_finales = []
    nombres_finales = []

    i = 0

    while i < len(df.columns):

        col_actual = str(df.columns[i])

        nombre_limpio = limpiar_nombre(col_actual)
        nombre_limpio = mapeo.get(nombre_limpio, nombre_limpio)

        tiene_unidad = (
            i + 1 < len(df.columns)
            and "unidad" in str(df.columns[i + 1]).lower()
        )

        if tiene_unidad:

            col_unidad = df.columns[i + 1]
            unidad = str(df[col_unidad].iloc[0]).strip()

            if unidad and unidad.lower() != "nan":
                nuevo_nombre = f"{nombre_limpio} ({unidad})"
            else:
                nuevo_nombre = nombre_limpio

            columnas_finales.append(col_actual)
            nombres_finales.append(nuevo_nombre)

            i += 2

        else:

            columnas_finales.append(col_actual)
            nombres_finales.append(nombre_limpio)

            i += 1

    df_final = df[columnas_finales].copy()
    df_final.columns = [limpiar_nombre(c) for c in nombres_finales]
    df_final = df_final.iloc[1:].reset_index(drop=True)

    old_keys = [
        (*extraer_base_y_unidad(c), c)
        for c in df_old.columns
    ]

    new_keys = [
        (*extraer_base_y_unidad(c), c)
        for c in df_final.columns
    ]

    cols_ordenadas = []

    for obase, ounit, original in old_keys:

        for nbase, nunit, ncol in new_keys:

            if obase == nbase and ounit == nunit:
                cols_ordenadas.append(ncol)
                break

    df_final_ordenado = df_final[cols_ordenadas].copy()
    df_final_ordenado = df_final_ordenado.iloc[:, :len(df_old.columns)]
    df_final_ordenado.columns = df_old.columns
    
    columnas_fecha = [c for c in df_final_ordenado.columns 
                  if c.lower().strip() in ["fecha de inicio", "fecha de terminación"]]

    for col in columnas_fecha:
     df_final_ordenado[col] = formatear_fecha(df_final_ordenado[col])

    return df_final_ordenado