
import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.image("LogoEuroirte.jpg", width=150)
st.title("Gestione File Report - Euroirte s.r.l.")

# Autenticazione semplice
utenti_autorizzati = ["lbianco", "acapizzi", "gcassarino"]
password_corretta = "Euroirte111927"

username = st.text_input("Nome utente")
password = st.text_input("Password", type="password")

if username not in utenti_autorizzati or password != password_corretta:
    st.warning("Accesso riservato. Inserisci le credenziali corrette.")
    st.stop()

st.success(f"Benvenuto {username}! Seleziona il file da aggiornare.")

# Dizionario dei report disponibili
report_options = {
    "Delivery TIM": "delivery.xlsx",
    "Assurance TIM": "impulsiva.xlsx",
    "Delivery Open Fiber": "delivery_openfiber.xlsx",
    "Assurance Open Fiber": "assurance_openfiber.xlsx"
}

report_choice = st.selectbox("Seleziona il report da aggiornare", list(report_options.keys()))
selected_file_path = report_options[report_choice]

uploaded_file = st.file_uploader("Carica il nuovo file Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df_new = pd.read_excel(uploaded_file)
        df_new.to_excel(selected_file_path, index=False)
        st.success(f"File '{selected_file_path}' aggiornato con successo!")
        st.dataframe(df_new.head(), use_container_width=True)
    except Exception as e:
        st.error(f"Errore durante l'upload del file: {e}")
