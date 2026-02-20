import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Monitor de Lechería", layout="wide")

@st.cache_data(ttl=600) # Esto hace que la app sea más rápida y no sature a Google
def load_data():
    try:
        # 1. Configuración de credenciales
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
        client = gspread.authorize(creds)
        
        # 2. Abrir la hoja (Asegúrate de que el nombre sea IDÉNTICO al de tu Google Sheet)
        # Si sigue fallando, puedes usar el ID de la URL: client.open_by_key("TU_ID_AQUÍ")
        sheet = client.open("Datos Lechería").sheet1
        
        # 3. Obtener registros y limpiar
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # LIMPIEZA CRÍTICA: Eliminar espacios invisibles en los nombres de las columnas
        df.columns = df.columns.str.strip()
        
        # ELIMINAR FILAS VACÍAS: Google Sheets a veces devuelve filas en blanco al final
        df = df[df['Nombre Vaca'] != ""].copy()
        
        # 4. Conversión de Tipos de Datos
        # Convertimos la fecha al formato correcto (Día/Mes/Año como en tu imagen)
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        
        # Convertimos litros a números (por si hay una coma o un espacio)
        df['Cantidad litros'] = pd.to_numeric(df['Cantidad litros'], errors='coerce')
        
        return df
    except Exception as e:
        # Si hay un error, lo mostramos de forma clara
        st.error(f"Error técnico en la carga: {e}")
        return None

# --- INICIO DE LA INTERFAZ ---
df = load_data()

if df is not None:
    st.title("🥛 Monitor de Producción Lechera")
    st.info(f"Datos actualizados al: {df['Fecha'].max().strftime('%d/%m/%Y') if not df.empty else 'N/A'}")

    # --- KPI's PRINCIPALES ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total = df['Cantidad litros'].sum()
        st.metric("Total Acumulado", f"{total:,.1f} Lts")
    
    with col2:
        promedio = df['Cantidad litros'].mean()
        st.metric("Promedio Lts/Vaca", f"{promedio:,.2f} Lts")
        
    with col3:
        n_vacas = df['Nombre Vaca'].nunique()
        st.metric("Vacas en Ordeño", n_vacas)

    st.divider()

    # --- GRÁFICOS ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("📈 Producción por Fecha")
        # Agrupamos por fecha para ver el total del hato por día
        df_diario = df.groupby('Fecha')['Cantidad litros'].sum().reset_index()
        fig_evolucion = px.area(df_diario, x='Fecha', y='Cantidad litros', 
                                title="Evolución Total del Hato",
                                color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig_evolucion, use_container_width=True)

    with c2:
        st.subheader("🐮 Top Productoras")
        top_vacas = df.groupby('Nombre Vaca')['Cantidad litros'].sum().nlargest(10).reset_index()
        fig_barras = px.bar(top_vacas, x='Cantidad litros', y='Nombre Vaca', 
                            orientation='h', color='Cantidad litros',
                            color_continuous_scale='Viridis')
        st.plotly_chart(fig_barras, use_container_width=True)

    # --- TABLA DE DATOS ---
    with st.expander("Ver todos los registros"):
        st.dataframe(df.sort_values('Fecha', ascending=False), use_container_width=True)

else:
    st.warning("No se pudo cargar la información. Revisa que tu archivo 'credenciales.json' esté en la carpeta.")