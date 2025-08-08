
import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# Imposta sfondo bianco e testo nero
st.markdown(
    """
    <style>
        html, body, [data-testid="stApp"] {
            background-color: white !important;
            color: black !important;
        }
        .stTextInput input, .stPasswordInput input, .stSelectbox, .stFileUploader, .stButton {
            color: black !important;
            background-color: white !important;
        }
        .stMarkdown, .stDataFrame, .stAlert {
            color: black !important;
        }
        .css-1d391kg {  /* Titolo */
            color: black !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

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
    "Assurance TIM": "assurance.xlsx",
    "Delivery Open Fiber": "deliveryopenfiber.xlsx",
    "Assurance Open Fiber": "assuranceopenfiber.xlsx"
}

report_choice = st.selectbox("Seleziona il report da aggiornare", list(report_options.keys()))
selected_file_path = report_options[report_choice]

# Mostra il nome corretto richiesto
st.info(f"⚠️ Il file da caricare deve essere chiamato esattamente: **{selected_file_path}**")

uploaded_file = st.file_uploader("Seleziona il file Excel (.xlsx) da caricare", type=["xlsx"])

if uploaded_file:
    uploaded_filename = uploaded_file.name
    st.write(f"📄 File selezionato: `{uploaded_filename}`")

    if st.button("Carica"):
        if uploaded_filename != selected_file_path:
            st.error(f"❌ Nome file non valido. Hai caricato '{uploaded_filename}', ma è richiesto '{selected_file_path}'.")
            st.stop()

        try:
            df_new = pd.read_excel(uploaded_file)
            df_new.to_excel(selected_file_path, index=False)
            st.success(f"✅ File '{selected_file_path}' aggiornato con successo!")
            st.dataframe(df_new.head(), use_container_width=True)
        except Exception as e:
            st.error(f"Errore durante l'upload del file: {e}")
