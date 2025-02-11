import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import streamlit as st
import pandas as pd

# Conectar con Google Sheets
archivo_json = json.loads(st.secrets["google_credentials"]["json"])
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    credenciales = ServiceAccountCredentials.from_json_keyfile_dict(archivo_json, scope)
    cliente = gspread.authorize(credenciales)
    hoja = cliente.open("Mariokarteros").sheet1
    datos = hoja.get_all_records()
    df = pd.DataFrame(datos)
    st.success("✅ Conexión exitosa con Google Sheets")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Error al conectar con Google Sheets:\n\n{e}")
