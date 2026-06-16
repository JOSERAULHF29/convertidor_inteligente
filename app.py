import streamlit as st
import pandas as pd
from transformador import procesar_jdlink
from io import BytesIO
import os
import base64

# ==================================================
# CONFIGURACIÓN
# ==================================================
def img_to_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
img_base64 = img_to_base64("mejorada2.png")

st.set_page_config(
    page_title="Conversor Inteligente",
    page_icon="📊",
    layout="wide"
)

# ==================================================
# CACHE 1: LECTURA EXCEL
# ==================================================
@st.cache_data
def leer_excel(file):
    return pd.read_excel(file, engine="openpyxl")

# ==================================================
# CACHE 2: PROCESAMIENTO
# ==================================================
@st.cache_data
def procesar(df, df_old):
    return procesar_jdlink(df, df_old)

# ==================================================
# CSS
# ==================================================
st.markdown("""
<style>
.main { padding-top: 0rem; }
.block-container { padding-top: 1rem; }

.upload-card {
    background-color: #111827;
    border-radius: 15px;
    padding: 25px;
    border: 1px solid #2d3748;
    margin-top: 15px;
    margin-bottom: 20px;
}

.card-title {
    text-align:center;
    font-size:24px;
    font-weight:bold;
    margin-bottom:20px;
}

.footer {
    text-align:center;
    margin-top:40px;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:

    st.image("csc.png", use_container_width=True)

    st.markdown("""
<div style="
    border: 2px solid #444;
    border-radius: 10px;
    padding: 15px;
    background-color: #111111;
    color: #ffffff;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
">

 <b>REGLAS DEL SISTEMA</b>

<ul style="margin-top:10px;">
    <li>Solo archivos de Operations Center</li>
    <li>Debe contener columna: <b>"Unidad"</b></li>
    <li>No se procesan archivos con estructura diferente</li>
    <li>Asegúrate de subir el archivo correcto antes de procesar</li>
</ul>

</div>
""", unsafe_allow_html=True)

# ==================================================
# BANNER
# ==================================================
st.markdown(f"""
<img src="data:image/png;base64,{img_base64}" 
     style="width:100%; height:450px; object-fit:cover; border-radius:10px;">
""", unsafe_allow_html=True)

# ==================================================
# TITULO
# ==================================================
st.markdown("""
<h1 style="text-align:center;font-size:55px;font-weight:800;">
CONVERSOR INTELIGENTE
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<p style="text-align:center;font-size:22px;color:#9CA3AF;">
Transforma archivos de Operations Center para reportes automatizados
</p>
""", unsafe_allow_html=True)

# ==================================================
# UPLOAD
# ==================================================
st.markdown('<div class="upload-card">', unsafe_allow_html=True)

st.markdown('<div class="card-title">📂 Carga de Archivos</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📁 Archivo nuevo")

    archivo_nuevo = st.file_uploader(
        "",
        type=["xlsx"],
        key="nuevo"
    )
    st.caption("Archivo descargado del Operations Center que serán procesados y corregidos.")

with col2:
    st.markdown("### 📄 Archivo modelo")
    archivo_modelo = st.file_uploader(
        "",
        type=["xlsx"],
        key="modelo"
    )
    st.caption("Archivo base que contiene la estructura correcta. El archivo nuevo será adaptado a este formato.")
st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
# BOTÓN
# ==================================================
if archivo_nuevo and archivo_modelo:
    st.markdown("### 📌 Validación del sistema")
    st.warning(""" ⚠️ IMPORTANTE: El archivo debe contener la columna **"Unidad"** para poder ser procesado. Si no cumple esta condición, el sistema lo rechazará automáticamente. """)

    if st.button("🚀 PROCESAR ARCHIVO", use_container_width=True):

        try:

            with st.spinner("Procesando información..."):

                # =========================
                # LECTURA (CACHE 1)
                # =========================
                df = leer_excel(archivo_nuevo)
                df_old = leer_excel(archivo_modelo)

                # =========================
                # VALIDACIÓN
                # =========================
                if "unidad" not in [c.lower().strip() for c in df.columns]:
                    st.error("❌ Archivo inválido: falta columna 'Unidad'")
                    st.stop()

                # =========================
                # PROCESAMIENTO (CACHE 2)
                # =========================
                resultado = procesar(df, df_old)

                # =========================
                # EXPORT
                # =========================
                salida = BytesIO()
                resultado.to_excel(salida, index=False, engine="openpyxl")
                salida.seek(0)

            st.success("✅ Archivo generado correctamente")

            st.markdown("### 📊 Resumen")

            c1, c2 = st.columns(2)

            with c1:
                st.metric("Columnas finales", len(resultado.columns))

            with c2:
                st.metric("Registros", len(resultado))

            st.download_button(
                label="⬇️ Descargar Excel",
                data=salida,
                file_name="archivo_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Revise su datos -  Error: {str(e)}")

# ==================================================
# FOOTER
# ==================================================
st.markdown("---")

st.markdown("""
<div class="footer">

<h2>Convertimos datos en decisiones</h2>

<p style="font-size:18px;color:gray;">
Desarrollado por <b>Raul Huamani - Data & Analytics - Ipesa </b>
</p>

</div>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Ocultar menú superior (hamburguesa) */
#MainMenu {
    visibility: hidden;
}

/* Ocultar header superior */
header {
    visibility: hidden;
}

/* Ocultar footer inferior */
footer {
    visibility: hidden;
}

/* Ocultar barra de herramientas superior derecha (Streamlit toolbar) */
.stAppToolbar {
    display: none;
}

/* Ocultar botón "Manage app" (Streamlit Cloud) */
.stDeployButton {
    display: none;
}
</style>
""", unsafe_allow_html=True)
