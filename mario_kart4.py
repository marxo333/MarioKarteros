import pandas as pd
import gspread
import matplotlib.pyplot as plt
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import json

# Conectar con Google Sheets
archivo_json = json.loads(st.secrets["google_credentials"]["json"])
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Cargar datos desde Google Sheets
def cargar_datos_google_sheets(archivo_json, nombre_hoja):
    try:
        credenciales = ServiceAccountCredentials.from_json_keyfile_dict(archivo_json, scope)
        cliente = gspread.authorize(credenciales)
        hoja = cliente.open(nombre_hoja).sheet1
        datos = hoja.get_all_records()
        df = pd.DataFrame(datos)

        # Eliminar espacios en los nombres de las columnas
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar datos de Google Sheets:\n\n{e}")
        return pd.DataFrame()

# Funciones para métricas

def calcular_estadisticas_historicas(df):
    # Calcular torneos jugados correctamente
    torneos_jugados = df.groupby('Jugador')['ID Torneo'].nunique()

    # Calcular carreras jugadas correctamente
    carreras_jugadas = df.groupby(['Jugador', 'ID Torneo'])['Numero de Carreras'].mean().groupby('Jugador').sum()

    # Sumar los puntos de todos los torneos
    puntos_totales = df.groupby('Jugador')['Puntos Totales'].sum()

    # Torneos ganados
    torneos_ganados = df[df['Puesto Final'] == 1].groupby('Jugador')['ID Torneo'].nunique()

    # Calcular % de puntos obtenidos
    max_puntos = carreras_jugadas * 15
    porcentaje_puntos = (puntos_totales / max_puntos) * 100

    # Promedio de puntos por torneo
    promedio_puntos_torneo = puntos_totales / torneos_jugados

    df_historico = pd.DataFrame({
        'Torneos_Jugados': torneos_jugados,
        'Torneos_Ganados': torneos_ganados,
        'Carreras_Jugadas': carreras_jugadas,
        'Puntos_Totales': puntos_totales,
        '% Puntos Obtenidos': porcentaje_puntos,
        'Promedio Puntos por Torneo': promedio_puntos_torneo
    }).fillna(0).reset_index()

    return df_historico

def coeficiente_dificultad_historico(df):
    df['Media Rivales'] = df.groupby('ID Torneo')['Puntos Totales'].transform('mean')
    df_historico = df.groupby('Jugador').agg(Puntos_Totales=('Puntos Totales', 'sum'), Media_Rivales=('Media Rivales', 'mean')).reset_index()
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

# Configuración
nombre_hoja = "Mariokarteros"
df = cargar_datos_google_sheets(archivo_json, nombre_hoja)

# Debug: Mostrar los primeros datos cargados
st.subheader("🔍 Datos crudos desde Google Sheets")
st.write(df.head())
st.write("Columnas disponibles:", df.columns.tolist())

if not df.empty:
    df_historico = calcular_estadisticas_historicas(df)
    df_coef_dificultad = coeficiente_dificultad_historico(df)
    df_racha_victorias = calcular_racha_victorias_historico(df)
    df_clutch = indice_clutch_historico(df)

    df_final = df_historico.merge(df_coef_dificultad, on='Jugador', how='left')
    df_final = df_final.merge(df_racha_victorias, on='Jugador', how='left')
    df_final = df_final.merge(df_clutch, on='Jugador', how='left')

    # Reordenar columnas para mayor claridad
    columnas_ordenadas = [
        'Jugador', 'Torneos_Jugados', 'Torneos_Ganados', 'Carreras_Jugadas',
        'Puntos_Totales', 'Promedio Puntos por Torneo', '% Puntos Obtenidos',
        'Coeficiente Dificultad', 'Racha', 'Índice Clutch'
    ]
    df_final = df_final[columnas_ordenadas]

    # Web con Streamlit
    st.title("🏎️ Clasificación de Mario Kart")
    st.dataframe(df_final)

    st.subheader("📊 Gráficos de Rendimiento")

    # Matplotlib para gráficos dentro de Streamlit
    fig, ax = plt.subplots()
    ax.bar(df_final['Jugador'], df_final['Puntos_Totales'], color='royalblue')
    ax.set_xlabel('Jugador')
    ax.set_ylabel('Puntos Totales')
    ax.set_title('Total de Puntos por Jugador')
    st.pyplot(fig)

    fig, ax = plt.subplots()
    ax.bar(df_final['Jugador'], df_final['% Puntos Obtenidos'], color='green')
    ax.set_xlabel('Jugador')
    ax.set_ylabel('% de Puntos Obtenidos')
    ax.set_title('Porcentaje de Puntos Obtenidos por Jugador')
    st.pyplot(fig)

    fig, ax = plt.subplots()
    ax.bar(df_final['Jugador'], df_final['Coeficiente Dificultad'], color='red')
    ax.set_xlabel('Jugador')
    ax.set_ylabel('Coeficiente de Dificultad')
    ax.set_title('Coeficiente de Dificultad por Jugador')
    st.pyplot(fig)

    st.subheader("🔥 Resumen de Jugadores")
    st.write(df_final)
else:
    st.warning("⚠️ No se pudo cargar la información. Verifica la conexión con Google Sheets.")
