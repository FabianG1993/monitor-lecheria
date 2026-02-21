import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Monitor de Lechería", layout="wide")

def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Forzamos la ruta al archivo local que ya vimos que existe
    ruta_credenciales = "credenciales.json"
    
    try:
        # Verificación de seguridad
        if not os.path.exists(ruta_credenciales):
            st.error(f"No se encuentra el archivo {ruta_credenciales} en {os.getcwd()}")
            return None
            
        creds = ServiceAccountCredentials.from_json_keyfile_name(ruta_credenciales, scope)
        client = gspread.authorize(creds)
        
        # 2. Abrir la hoja (Asegúrate que el nombre en Google Drive sea este exacto)
        # Si el nombre es distinto, cámbialo aquí:
        nombre_hoja = "Datos Lechería" 
        sheet = client.open(nombre_hoja).sheet1
        
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # --- LIMPIEZA DE DATOS (Basada en tus imágenes) ---
        df.columns = df.columns.str.strip() # Soluciona el error de la imagen image_a6d124.png
        df = df[df['Nombre Vaca'] != ""].copy()
        
        # Conversión de tipos
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        df['Cantidad litros'] = pd.to_numeric(df['Cantidad litros'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None

# --- INTERFAZ VISUAL ---
st.title("🥛 Monitor de Producción Lechera")
df = load_data()

if df is not None:
    # Filtros
    vacas = sorted(df['Nombre Vaca'].unique())
    seleccion = st.sidebar.multiselect("Seleccionar Vacas:", vacas, default=vacas)
    df_f = df[df['Nombre Vaca'].isin(seleccion)]

    # KPIs Rápidos
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Litros", f"{df_f['Cantidad litros'].sum():,.1f}")
    c2.metric("Promedio/Vaca", f"{df_f['Cantidad litros'].mean():,.2f}")
    c3.metric("Última Fecha", df_f['Fecha'].max().strftime('%d/%m/%Y'))

    # Gráfico de producción
    fig = px.line(df_f, x='Fecha', y='Cantidad litros', color='Nombre Vaca', markers=True,
                 title="Evolución de Producción por Vaca")
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de datos
    st.subheader("Registros recientes")
    st.dataframe(df_f.sort_values(by='Fecha', ascending=False), use_container_width=True)