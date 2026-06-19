import pandas as pd
import re


def formatear_fecha(serie):
    serie = pd.to_datetime(serie, errors="coerce")
    serie = serie.astype(str).str.lower()
    serie = serie.str.replace("a. m.", "AM", regex=False)
    serie = serie.str.replace("p. m.", "PM", regex=False)

    serie = pd.to_datetime(serie, errors="coerce", dayfirst=True)
    return serie.dt.strftime("%d/%m/%Y %H:%M")


def limpiar_nombre(c):
    return re.sub(r"\.\d+$", "", str(c)).strip()


def norm_col(c):
    return limpiar_nombre(c).lower().replace("\xa0", " ").strip()


def procesar_jdlink(df, df_old):
    # 1. Copiar nombres limpios del modelo original
    columnas_modelo = [limpiar_nombre(c) for c in df_old.columns]

    mapeo = {
        "utilización trabajo": "utilización en funcionamiento",
    }

    columnas_finales = []
    nombres_finales = []
    i = 0

    # 2. Reconstrucción y fusión de columnas con sus unidades
    while i < len(df.columns):
        col_actual = str(df.columns[i])
        nombre_limpio = limpiar_nombre(col_actual)
        nombre_limpio = mapeo.get(nombre_limpio.lower(), nombre_limpio)
        nombre_lower = nombre_limpio.lower().strip()

        tiene_unidad = i + 1 < len(df.columns) and "unidad" in str(
            df.columns[i + 1]
        ).lower()

        unidad = None
        if tiene_unidad:
            col_unidad = df.columns[i + 1]
            unidad = str(df[col_unidad].iloc[0]).strip().lower()

        # Normalizaciones específicas
        if "última latitud conocida" in nombre_lower:
            nombre_final = "Última latitud conocida"
        elif "última longitud conocida" in nombre_lower:
            nombre_final = "Última longitud conocida"
        elif "utilización (c&f) alta" in nombre_lower and unidad == "%":
            nombre_final = "Utilización (C&F) Alto (%)"
        elif "utilización (c&f) media" in nombre_lower and unidad == "%":
            nombre_final = "Utilización (C&F) Mediano (%)"
        elif "utilización (c&f) baja" in nombre_lower and unidad == "%":
            nombre_final = "Utilización (C&F) Bajo (%)"
        elif "utilización (c&f) contacto dado" in nombre_lower and unidad == "%":
            nombre_final = "Utilización (C&F) Llave conectada (%)"
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

    # Crear dataframe base ya sin las columnas de "unidad" intermedias
    df_intermedio = df[columnas_finales].copy()
    df_intermedio.columns = nombres_finales

    # =======================================================
    # ALINEACIÓN ULTRA-ESTRICTA: EVITAR REPETICIONES DE ÍNDICE
    # =======================================================
    cols_idx = []
    indices_usados = set()

    for col_mod in columnas_modelo:
        c_mod_norm = norm_col(col_mod)
        match_encontrado = False

        # Paso 1: Intentar buscar coincidencia exacta que NO haya sido usada
        for idx, col_nue in enumerate(df_intermedio.columns):
            if idx not in indices_usados and norm_col(col_nue) == c_mod_norm:
                cols_idx.append(idx)
                indices_usados.add(idx)
                match_encontrado = True
                break

        # Paso 2: Si no encuentra exacta, buscar coincidencia parcial que NO haya sido usada
        if not match_encontrado:
            for idx, col_nue in enumerate(df_intermedio.columns):
                if idx not in indices_usados and c_mod_norm in norm_col(
                    col_nue
                ):
                    cols_idx.append(idx)
                    indices_usados.add(idx)
                    match_encontrado = True
                    break

        # Paso 3: Respaldo de emergencia (Si falta la columna, rellenar temporalmente con NaN para no romper el orden)
        if not match_encontrado:
            # Añadimos un valor marcador para saber que esta columna no se cruzó
            cols_idx.append(-1)

    # Reconstrucción del DataFrame final respetando el orden y agregando columnas faltantes vacías si aplica
    columnas_salida = []
    for i, idx in enumerate(cols_idx):
        nombre_col_modelo = columnas_modelo[i]
        if idx != -1:
            # Trae la columna real de los datos nuevos
            col_datos = df_intermedio.iloc[:, idx].copy()
            col_datos.name = nombre_col_modelo
            columnas_salida.append(col_datos)
        else:
            # Crea la columna vacía en su lugar correspondiente si no vino en el Excel
            col_vacia = pd.Series([None] * len(df), name=nombre_col_modelo)
            columnas_salida.append(col_vacia)

    # Unimos todas las columnas detectadas una sola vez en el orden exacto del modelo
    df_final_ordenado = pd.concat(columnas_salida, axis=1)

    # ======================
    # FORMATEO DE FECHAS
    # ======================
    columnas_fecha = [
        c
        for c in df_final_ordenado.columns
        if norm_col(c) in ["fecha de inicio", "fecha de terminación"]
    ]

    for col in columnas_fecha:
        df_final_ordenado[col] = formatear_fecha(df_final_ordenado[col])

    return df_final_ordenado
