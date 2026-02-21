import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Lechería Real-Time", layout="wide", page_icon="🥛")

@st.cache_data(ttl=60) # Se actualiza cada minuto para tiempo real
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # 1. INTENTO DE CONEXIÓN (Nube vs Local)
        if "gcp_service_account" in st.secrets:
            # Para el celular (Streamlit Cloud)
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            # Para tu computadora
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
        
        client = gspread.authorize(creds)
        
        # 2. APERTURA DE LA HOJA
        # Asegúrate de que el nombre sea exacto como en tu Drive
        sheet = client.open("Datos Lechería").sheet1
        
        # 3. PROCESAMIENTO LIMPIO
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # Limpieza de columnas (Soluciona el KeyError y los espacios)
        df.columns = df.columns.str.strip()
        
        # Conversión de tipos basada en tus datos
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        df['Cantidad litros'] = pd.to_numeric(df['Cantidad litros'], errors='coerce')
        df['Nombre Vaca'] = df['Nombre Vaca'].str.strip().str.capitalize()
        
        return df.dropna(subset=['Cantidad litros', 'Nombre Vaca'])

    except Exception as e:
        # Aquí capturamos el error real y no el <Response [200]>
        st.error(f"Error en la carga: {e}")
        return None

# --- INTERFAZ DEL DASHBOARD ---
df = load_data()

if df is not None and not df.empty:
    st.title("🥛 Monitor de Producción Real-Time")
    
    # KPIs Estilo App Móvil
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Litros", f"{df['Cantidad litros'].sum():,.1f}")
    m2.metric("Promedio/Vaca", f"{df['Cantidad litros'].mean():,.2f}")
    m3.metric("Último Registro", df['Fecha'].max().strftime('%d/%m/%Y'))

    st.divider()

    # Gráfico de Tendencia (Evolución diaria)
    st.subheader("📈 Evolución del Hato")
    df_diario = df.groupby('Fecha')['Cantidad litros'].sum().reset_index()
    fig_evol = px.line(df_diario, x='Fecha', y='Cantidad litros', markers=True, template="plotly_dark")
    st.plotly_chart(fig_evol, use_container_width=True)

    # Comparativa de Vacas
    st.subheader("🐮 Producción por Vaca")
    fig_bar = px.bar(df, x='Nombre Vaca', y='Cantidad litros', color='Nombre Vaca', barmode='group')
    st.plotly_chart(fig_bar, use_container_width=True)

    # Tabla de control para el celular
    with st.expander("Ver registros completos"):
        st.dataframe(df.sort_values('Fecha', ascending=False), use_container_width=True)
else:
    st.warning("Esperando datos... Asegúrate de que la hoja 'Registro de Producción Lechera' tenga información.")


