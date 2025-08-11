
import streamlit as st
import pandas as pd
import base64
import requests

st.set_page_config(layout="wide")

# --- STILE ---
st.markdown("""
<style>
html, body, [data-testid="stApp"] {
    background-color: white !important;
    color: black !important;
}
h1, h2, h3, h4, h5, h6, p, span, div, label {
    color: black !important;
}
div[data-baseweb="radio"] label {
    color: black !important;
    font-weight: 600 !important;
}
input, textarea, select {
    background-color: white !important;
    color: black !important;
}
button[kind="primary"], button[kind="secondary"], .stButton > button {
    background-color: white !important;
    color: black !important;
    border: 1px solid #999 !important;
    border-radius: 6px;
}
button[kind="primary"]:hover, button[kind="secondary"]:hover, .stButton > button:hover {
    background-color: #f0f0f0 !important;
    color: black !important;
}
.css-1d391kg, .stDataFrame, .css-1m3z7sd {
    color: black !important;
    background-color: white !important;
}
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE UPLOAD GITHUB ---
def upload_to_github(repo, path_in_repo, file_data, commit_message):
    token = st.secrets["github_token"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    get_url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    get_resp = requests.get(get_url, headers=headers)

    if get_resp.status_code == 200:
        sha = get_resp.json()["sha"]
    else:
        st.error(f"❌ Errore nel recupero SHA: {get_resp.json().get('message', '')}")
        return False

    encoded_content = base64.b64encode(file_data).decode('utf-8')

    data = {
        "message": commit_message,
        "content": encoded_content,
        "sha": sha,
        "branch": "main"
    }

    put_resp = requests.put(get_url, headers=headers, json=data)


    return put_resp.status_code in [200, 201]

# --- HEADER ---
st.image("LogoEuroirte.jpg", width=180)
st.link_button("🏠 Torna alla Home", url="https://homeeuroirte.streamlit.app/")
st.title("Gestione File Report - Euroirte s.r.l.")

# --- LOGIN ---
utenti_autorizzati = ["lbianco", "acapizzi", "gcassarino"]
password_corretta = "Euroirte111927"

username = st.text_input("Nome utente")
password = st.text_input("Password", type="password")

if username not in utenti_autorizzati or password != password_corretta:
    st.warning("Accesso riservato. Inserisci le credenziali corrette.")
    st.stop()

st.success(f"Benvenuto {username}! Seleziona il file da aggiornare.")

# --- MAPPATURA REPORT ---
report_options = {
    "Delivery TIM": ("delivery.xlsx", "lbianco11197/Avanzamento-Delivery"),
    "Assurance TIM": ("assurance.xlsx", "lbianco11197/Avanzamento-Impulsiva-v2"),
    "Delivery Open Fiber": ("deliveryopenfiber.xlsx", "lbianco11197/Avanzamento-Delivery-OF"),
}

report_choice = st.selectbox("Seleziona il report da aggiornare", list(report_options.keys()))
selected_file_name, github_repo = report_options[report_choice]

st.info(f"⚠️ Il file da caricare deve essere chiamato esattamente: **{selected_file_name}**")
uploaded_file = st.file_uploader("Seleziona il file Excel (.xlsx) da caricare", type=["xlsx"])

# --- UPLOAD ---
if uploaded_file:
    uploaded_filename = uploaded_file.name
    st.write(f"📄 File selezionato: `{uploaded_filename}`")

    if st.button("Carica"):
        if uploaded_filename != selected_file_name:
            st.error(f"❌ Nome file non valido. Hai caricato '{uploaded_filename}', ma è richiesto '{selected_file_name}'.")
            st.stop()

        try:
            df_new = pd.read_excel(uploaded_file)
            df_new.to_excel(selected_file_name, index=False)

            if github_repo:
                excel_bytes = uploaded_file.getvalue()
                commit_msg = f"Aggiornato da {username} via Streamlit"
                success = upload_to_github(github_repo, selected_file_name, excel_bytes, commit_msg)

                if success:
                    st.success(f"✅ File '{selected_file_name}' aggiornato su GitHub con successo!")
                else:
                    st.error("❌ Errore durante l'aggiornamento del file su GitHub.")
            else:
                st.warning("⚠️ Questo report non è ancora collegato a GitHub.")

            st.dataframe(df_new.head(), use_container_width=True)

        except Exception as e:
            st.error(f"Errore durante l'upload del file: {e}")
