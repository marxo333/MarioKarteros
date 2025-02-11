import pandas as pd
import gspread
import matplotlib.pyplot as plt
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import json

# ✅ Cargar las credenciales desde Streamlit Secrets
archivo_json = json.loads(st.secrets["google_credentials"]["json"])

# ✅ Cargar datos desde Google Sheets
def cargar_datos_google_sheets(archivo_json, nombre_hoja):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credenciales = ServiceAccountCredentials.from_json_keyfile_dict(archivo_json, scope)
        cliente = gspread.authorize(credenciales)
        hoja = cliente.open(nombre_hoja).sheet1
        datos = hoja.get_all_records()
        df = pd.DataFrame(datos)
        df.columns = df.columns.str.strip()  # Eliminar espacios en los nombres de las columnas
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar datos de Google Sheets: {e}")
        return pd.DataFrame()

# ✅ Cálculo de estadísticas históricas
def calcular_estadisticas_historicas(df):
    df_historico = df.groupby('Jugador').agg(
        Puntos_Totales=('Puntos Totales', 'sum'),
        Carreras_Jugadas=('Numero de Carreras', 'sum'),
        Torneos_Jugados=('ID Torneo', 'nunique')
    ).reset_index()
    df_historico['% Puntos Obtenidos'] = (df_historico['Puntos_Totales'] / (df_historico['Carreras_Jugadas'] * 15)) * 100
    return df_historico

def coeficiente_dificultad_historico(df):
    df['Media Rivales'] = df.groupby('ID Torneo')['Puntos Totales'].transform('mean')
    df_historico = df.groupby('Jugador').agg(
        Puntos_Totales=('Puntos Totales', 'sum'),
        Media_Rivales=('Media Rivales', 'mean')
    ).reset_index()
    df_historico['Coeficiente Dificultad'] = df_historico['Puntos_Totales'] / df_historico['Media_Rivales']
    return df_historico[['Jugador', 'Coeficiente Dificultad']]

def calcular_racha_victorias_historico(df):
    df = df.copy()
    df['Ganó'] = df['Puesto Final'].astype(str).str.contains("1")
    rachas = df.groupby(['Jugador', 'ID Torneo'])['Ganó'].max().reset_index()
    rachas['Racha'] = rachas.groupby('Jugador')['Ganó'].cumsum()
    return rachas.groupby('Jugador').agg({'Racha': 'max'}).reset_index()

def indice_clutch_historico(df):
    clutch = df.groupby('Jugador')['Puntos Totales'].apply(lambda x: x.tail(3).mean()).reset_index()
    clutch.rename(columns={'Puntos Totales': 'Índice Clutch'}, inplace=True)
    return clutch

# ✅ Configuración
nombre_hoja = "Mariokarteros"
df = cargar_datos_google_sheets(archivo_json, nombre_hoja)

if not df.empty:
    df_historico = calcular_estadisticas_historicas(df)
    df_coef_dificultad = coeficiente_dificultad_historico(df)
    df_racha_victorias = calcular_racha_victorias_historico(df)
    df_clutch = indice_clutch_historico(df)

    df_final = df_historico.merge(df_coef_dificultad, on='Jugador')
    df_final = df_final.merge(df_racha_victorias, on='Jugador')
    df_final = df_final.merge(df_clutch, on='Jugador')

    # ✅ Web con Streamlit
    st.title("🏎️ Clasificación de Mario Kart")
    st.dataframe(df_final)

    st.subheader("📊 Gráficos de Rendimiento")

    # ✅ Matplotlib para gráficos dentro de Streamlit
    for columna, color, titulo in [
        ('Puntos_Totales', 'royalblue', 'Total de Puntos por Jugador'),
        ('% Puntos Obtenidos', 'green', 'Porcentaje de Puntos Obtenidos por Jugador'),
        ('Coeficiente Dificultad', 'red', 'Coeficiente de Dificultad por Jugador')
    ]:
        fig, ax = plt.subplots()
        ax.bar(df_final['Jugador'], df_final[columna], color=color)
        ax.set_xlabel('Jugador')
        ax.set_ylabel(columna.replace('_', ' '))
        ax.set_title(titulo)
        st.pyplot(fig)

    st.subheader("🔥 Resumen de Jugadores")
    st.write(df_final)
else:
    st.warning("⚠️ No se pudo cargar la información. Verifica la conexión con Google Sheets.")
