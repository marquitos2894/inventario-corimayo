import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN SUPABASE ---
SUPABASE_URL = "https://tubzodlpqoougoojpuhz.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR1YnpvZGxwcW9vdWdvb2pwdWh6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgwNzk2MTgsImV4cCI6MjA3MzY1NTYxOH0.ltHYvuAZI5zz-8OniYMetzp8jqC9rwyZ89SDdPvHb8k"
TABLE_NAME = "mainstock"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# --- Función para traer todos los datos ---
@st.cache_data(show_spinner=False)
def fetch_all_data():
    batch_size = 1000
    offset = 0
    all_data = []
    while True:
        res = supabase.table(TABLE_NAME).select("*").range(offset, offset + batch_size - 1).execute()
        if not res.data:
            break
        all_data.extend(res.data)
        offset += batch_size
    return pd.DataFrame(all_data)

# --- FUNCIÓN PARA DESCARGAR EXCEL ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
        workbook = writer.book
        worksheet = writer.sheets['Inventario']
        # Ajuste de ancho de columnas
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(idx, idx, max_len)
        # Encabezados en negrita
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    return output.getvalue()

# --- APP STREAMLIT ---
st.title("📦Inventario Almacén Corimayo")

df = fetch_all_data()
st.success(f"Total registros cargados: {len(df)}")


# --- FILTRO DE BÚSQUEDA ---
search = st.text_input("Buscar por descripción o código:")
if search:
    df = df[df["DESCRIPCION"].str.contains(search, case=False, na=False) |
            df["CODIGO"].astype(str).str.contains(search)]
st.dataframe(df, use_container_width=True)

# --- BOTÓN DESCARGAR ---
st.download_button(
    label="📥 Descargar en Excel",
    data=to_excel(df),
    file_name="Inventario_Corimayo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

res = supabase.table("control_actualizacion").select("fecha_actualizacion").eq("tabla", "mainstock").execute()
if res.data:
    fecha_str = pd.to_datetime(res.data[0]["fecha_actualizacion"]).strftime("%d/%m/%Y %H:%M:%S")
    st.markdown(f"🕒 **Última actualización de la base:** {fecha_str}")
else:
    st.markdown("⚠️ No hay registro de la última actualización aún.")
