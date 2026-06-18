'''
import pandas as pd
import re


def formatear_fecha(serie):
    serie = pd.to_datetime(serie, errors="coerce")

    serie = serie.astype(str).str.lower()
    serie = serie.str.replace("a. m.", "AM", regex=False)
    serie = serie.str.replace("p. m.", "PM", regex=False)

    serie = pd.to_datetime(serie, errors="coerce",dayfirst=True)

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
      "utilización trabajo": "utilización en funcionamiento",
    }

    columnas_finales = []
    nombres_finales = []

    i = 0

    while i < len(df.columns):

        col_actual = str(df.columns[i])

        nombre_limpio = limpiar_nombre(col_actual)
        nombre_limpio = mapeo.get(nombre_limpio.lower(), nombre_limpio)
        nombre_lower = nombre_limpio.lower().strip()

        tiene_unidad = (
            i + 1 < len(df.columns)
            and "unidad" in str(df.columns[i + 1]).lower()
        )

        unidad = None

        if tiene_unidad:
            col_unidad = df.columns[i + 1]
            unidad = str(df[col_unidad].iloc[0]).strip().lower()

        nombre_lower = nombre_limpio.lower()

        # =====================================================
        # 📍 LATITUD / LONGITUD (NO SE TOCAN)
        # =====================================================
        if "última latitud conocida" in nombre_lower:
             nombre_final = "Última latitud conocida"

        elif "última longitud conocida" in nombre_lower:
             nombre_final = "Última longitud conocida"

        # =====================================================
        # 📍 UTILIZACIÓN C&F SOLO SI UNIDAD = %
        # =====================================================
        elif "utilización (c&f) alta" in nombre_lower and unidad == "%":
            nombre_final = "Utilización (C&F) Alto (%)"

        elif "utilización (c&f) media" in nombre_lower and unidad == "%":
            nombre_final = "Utilización (C&F) Mediano (%)"

        elif "utilización (c&f) baja" in nombre_lower and unidad == "%":
            nombre_final = "Utilización (C&F) Bajo (%)"

        elif "utilización (c&f) contacto dado" in nombre_lower and unidad == "%":
            nombre_final = "Utilización (C&F) Llave conectada (%)"

        # =====================================================
        # 📍 RESTO DE COLUMNAS
        # =====================================================
        else:
            if unidad and unidad != "nan":
                nombre_final = f"{nombre_limpio} ({unidad})"
            else:
                nombre_final = nombre_limpio

        columnas_finales.append(col_actual)
        nombres_finales.append(nombre_final)

        if tiene_unidad:
            i += 2
        else:
            i += 1

    # =========================
    # DF FINAL
    # =========================
    df_final = df[columnas_finales].copy()
    df_final.columns = [limpiar_nombre(c) for c in nombres_finales]

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
    

    # =========================
    # FECHAS
    # =========================
    columnas_fecha = [
        c for c in df_final_ordenado.columns
        if c.lower().strip() in ["fecha de inicio", "fecha de terminación"]
    ]

    for col in columnas_fecha:
        df_final_ordenado[col] = formatear_fecha(df_final_ordenado[col])

    return df_final_ordenado
    '''


import pandas as pd
import re
import unicodedata


# =========================
# FECHAS
# =========================
def formatear_fecha(serie):
    serie = pd.to_datetime(serie, errors="coerce")

    serie = serie.astype(str).str.lower()
    serie = serie.str.replace("a. m.", "AM", regex=False)
    serie = serie.str.replace("p. m.", "PM", regex=False)

    serie = pd.to_datetime(serie, errors="coerce", dayfirst=True)

    return serie.dt.strftime("%d/%m/%Y %H:%M")


# =========================
# NORMALIZACIÓN FUERTE
# =========================
def norm_col(c):
    c = str(c)
    c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode("utf-8")
    c = c.lower()
    c = c.replace("\xa0", " ")
    c = re.sub(r"\s+", " ", c)
    c = re.sub(r"[^\w\s%()&]", "", c)  # mantiene & por C&F
    return c.strip()


def limpiar_nombre(c):
    return re.sub(r"\.\d+$", "", str(c)).strip()


def extraer_base_y_unidad(col):
    m = re.match(r"(.+?)\s*\((.+?)\)$", str(col))
    if m:
        return norm_col(m.group(1)), norm_col(m.group(2))
    return norm_col(col), ""


# =========================
# PROCESO PRINCIPAL
# =========================
def procesar_jdlink(df, df_old):

    # =========================
    # MODELO (FUENTE DE VERDAD)
    # =========================
    df_old.columns = [limpiar_nombre(c) for c in df_old.columns]

    mapeo = {
        "utilizacion trabajo": "utilizacion en funcionamiento",
    }

    # =========================
    # RENOMBRAR NUEVO DF
    # =========================
    columnas_finales = []
    nombres_finales = []

    i = 0

    while i < len(df.columns):

        col_actual = str(df.columns[i])

        nombre_limpio = limpiar_nombre(col_actual)
        nombre_limpio = mapeo.get(nombre_limpio.lower(), nombre_limpio)

        nombre_norm = norm_col(nombre_limpio)

        tiene_unidad = (
            i + 1 < len(df.columns)
            and "unidad" in str(df.columns[i + 1]).lower()
        )

        unidad = ""

        if tiene_unidad:
            col_unidad = df.columns[i + 1]
            unidad = str(df[col_unidad].iloc[0]).strip().lower()

        # =========================
        # CASOS ESPECIALES FIJOS
        # =========================
        if "ultima latitud conocida" in nombre_norm:
            nombre_final = "Última latitud conocida"

        elif "ultima longitud conocida" in nombre_norm:
            nombre_final = "Última longitud conocida"

        # =========================
        # UTILIZACIÓN C&F (ROBUSTO)
        # =========================
        elif (
            "utilizacion" in nombre_norm
            and "c" in nombre_norm
            and "f" in nombre_norm
            and "alta" in nombre_norm
            and unidad == "%"
        ):
            nombre_final = "Utilización (C&F) Alto (%)"

        elif (
            "utilizacion" in nombre_norm
            and "c" in nombre_norm
            and "f" in nombre_norm
            and "media" in nombre_norm
            and unidad == "%"
        ):
            nombre_final = "Utilización (C&F) Mediano (%)"

        elif (
            "utilizacion" in nombre_norm
            and "c" in nombre_norm
            and "f" in nombre_norm
            and "baja" in nombre_norm
            and unidad == "%"
        ):
            nombre_final = "Utilización (C&F) Bajo (%)"

        elif (
            "utilizacion" in nombre_norm
            and "c" in nombre_norm
            and "f" in nombre_norm
            and "contacto" in nombre_norm
            and unidad == "%"
        ):
            nombre_final = "Utilización (C&F) Llave conectada (%)"

        # =========================
        # RESTO
        # =========================
        else:
            if unidad and unidad != "nan":
                nombre_final = f"{nombre_limpio} ({unidad})"
            else:
                nombre_final = nombre_limpio

        columnas_finales.append(col_actual)
        nombres_finales.append(nombre_final)

        i += 2 if tiene_unidad else 1

    # =========================
    # DF FINAL
    # =========================
    df_final = df[columnas_finales].copy()
    df_final.columns = [limpiar_nombre(c) for c in nombres_finales]

    # =========================
    # KEYS
    # =========================
    old_keys = [(extraer_base_y_unidad(c)[0], c) for c in df_old.columns]
    new_keys = [(extraer_base_y_unidad(c)[0], c) for c in df_final.columns]

    # =========================
    # MATCH 1:1 SIN DUPLICADOS
    # =========================
    used_new = [False] * len(new_keys)
    cols_ordenadas = []

    for obase, _ in old_keys:

        for i, (nbase, ncol) in enumerate(new_keys):

            if used_new[i]:
                continue

            if obase == nbase:
                cols_ordenadas.append(ncol)
                used_new[i] = True
                break

    # =========================
    # RESULTADO FINAL
    # =========================
    df_final_ordenado = df_final[cols_ordenadas].copy()

    # =========================
    # FECHAS
    # =========================
    columnas_fecha = [
        c for c in df_final_ordenado.columns
        if norm_col(c) in ["fecha de inicio", "fecha de terminacion"]
    ]

    for col in columnas_fecha:
        df_final_ordenado[col] = formatear_fecha(df_final_ordenado[col])

    return df_final_ordenado
