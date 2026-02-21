import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import os

st.set_page_config(page_title="Monitor Lechería Pro", layout="wide")

def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # LÓGICA HÍBRIDA DE SEGURIDAD
        if "gcp_service_account" in st.secrets:
            # Si estamos en la NUBE (Streamlit Cloud)
            creds_info = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        elif os.path.exists("credenciales.json"):
            # Si estamos en LOCAL (Tu computadora)
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
        else:
            st.error("❌ No se encontraron credenciales (ni en la nube ni local).")
            return None

        client = gspread.authorize(creds)
        # Asegúrate de que el nombre coincida con tu Drive
        sheet = client.open("Registro de Producción Lechera").sheet1
        
        df = pd.DataFrame(sheet.get_all_records())
        
        # Limpieza de columnas
        df.columns = df.columns.str.strip()
        df = df[df['Nombre Vaca'] != ""].copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        df['Cantidad litros'] = pd.to_numeric(df['Cantidad litros'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- RENDERIZADO DE LA APP ---
df = load_data()

if df is not None:
    st.title("🥛 Monitor de Producción Real-Time")
    
    # KPIs Rápidos
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Litros", f"{df['Cantidad litros'].sum():,.1f}")
    c2.metric("Promedio/Vaca", f"{df['Cantidad litros'].mean():,.2f}")
    c3.metric("Última Fecha", df['Fecha'].max().strftime('%d/%m/%Y'))

    # Gráfico de Evolución
    fig = px.line(df, x='Fecha', y='Cantidad litros', color='Nombre Vaca', markers=True)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📋 Registros en la Hoja de Cálculo")
    st.dataframe(df.sort_values(by='Fecha', ascending=False), use_container_width=True)
