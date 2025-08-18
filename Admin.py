import streamlit as st
import pandas as pd
import base64
import requests

st.set_page_config(layout="wide")

# --- STILE ---
st.markdown("""
<style>
html, body, [data-testid="stApp"] { background-color: white !important; color: black !important; }
h1, h2, h3, h4, h5, h6, p, span, div, label { color: black !important; }
div[data-baseweb="radio"] label { color: black !important; font-weight: 600 !important; }
input, textarea, select { background-color: white !important; color: black !important; }
button[kind="primary"], button[kind="secondary"], .stButton > button {
  background-color: white !important; color: black !important; border: 1px solid #999 !important; border-radius: 6px;
}
button[kind="primary"]:hover, button[kind="secondary"]:hover, .stButton > button:hover {
  background-color: #f0f0f0 !important; color: black !important;
}
.css-1d391kg, .stDataFrame, .css-1m3z7sd { color: black !important; background-color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE UPLOAD GITHUB (create/update) ---
def upload_to_github(repo, path_in_repo, file_data, commit_message, branch="main"):
    """
    Carica o aggiorna un file su GitHub (API v3).
    Se il file esiste usa SHA per update, altrimenti crea.
    """
    token = st.secrets["github_token"]  # aggiungi su Streamlit Cloud: github_token = "ghp_xxx"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    api_url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"

    # Controlla se esiste per recuperare lo SHA
    sha = None
    get_resp = requests.get(api_url, headers=headers, params={"ref": branch})
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
    elif get_resp.status_code not in (404,):
        st.error(f"❌ Errore nel controllo esistenza file: {get_resp.json().get('message','')}")
        return False

    encoded = base64.b64encode(file_data).decode("utf-8")
    payload = {"message": commit_message, "content": encoded, "branch": branch}
    if sha:  # update
        payload["sha"] = sha

    put_resp = requests.put(api_url, headers=headers, json=payload)
    if put_resp.status_code in (200, 201):
        return True
    else:
        try:
            msg = put_resp.json().get("message", "")
        except Exception:
            msg = str(put_resp.text)
        st.error(f"❌ Errore GitHub: {put_resp.status_code} — {msg}")
        return False

# --- HEADER ---
st.image("LogoEuroirte.jpg", width=180)
st.link_button("🏠 Torna alla Home", url="https://homeeuroirte.streamlit.app/")

# --- Nuovo titolo e pulsante per avanzamento economico ---
st.title("Verifica l'avanzamento economico")
st.link_button("💶 Vai al Report Economico", "https://avanzamento-economico.streamlit.app/")

st.title("Gestione")


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
    "Avanzamento Economico": ("Avanzamento.xlsx", "lbianco11197/Avanzamento-economico"),
}

report_choice = st.selectbox("Seleziona il report da aggiornare", list(report_options.keys()))
selected_file_name, github_repo = report_options[report_choice]

st.info(f"⚠️ Il file da caricare deve chiamarsi **{selected_file_name}**")
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
            # Validazione minima: si apre e si riscrive per evitare file corrotti
            df_preview = pd.read_excel(uploaded_file)  # solo preview/validazione
            excel_bytes = uploaded_file.getvalue()

            if github_repo:
                ok = upload_to_github(
                    repo=github_repo,
                    path_in_repo=selected_file_name,
                    file_data=excel_bytes,
                    commit_message=f"Aggiornato {selected_file_name} da {username} via Streamlit"
                )
                if ok:
                    st.success(f"✅ File '{selected_file_name}' aggiornato su GitHub: {github_repo}")
                else:
                    st.error("❌ Errore durante l'aggiornamento del file su GitHub.")
            else:
                st.warning("⚠️ Questo report non è ancora collegato a GitHub.")

            st.markdown("**Anteprima (prime righe):**")
            st.dataframe(df_preview.head(20), use_container_width=True)

        except Exception as e:
            st.error(f"Errore durante l'upload del file: {e}")
