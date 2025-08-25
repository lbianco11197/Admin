import streamlit as st
import pandas as pd
import base64 
from pathlib import Path
import requests

# --- STILE ---
def set_page_background(image_path: str):
    """Imposta un'immagine di sfondo full-screen come background dell'app Streamlit."""
    p = Path(image_path)
    if not p.exists():
        st.warning(f"Background non trovato: {image_path}")
        return
    encoded = base64.b64encode(p.read_bytes()).decode()
    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: url("data:image/png;base64,{encoded}") center/cover no-repeat fixed;
    }}
    [data-testid="stHeader"], [data-testid="stSidebar"] {{
        background-color: rgba(255,255,255,0.0) !important;
    }}
    html, body, [data-testid="stApp"] {{
        color: #0b1320 !important;
    }}
    .stDataFrame, .stTable, .stSelectbox div[data-baseweb="select"],
    .stTextInput, .stNumberInput, .stDateInput, .stMultiSelect,
    .stRadio, .stCheckbox, .stSlider, .stFileUploader, .stTextArea {{
        background-color: rgba(255,255,255,0.88) !important;
        border-radius: 10px;
        backdrop-filter: blur(0.5px);
    }}
    .stDataFrame table, .stDataFrame th, .stDataFrame td {{
        color: #0b1320 !important;
        background-color: rgba(255,255,255,0.0) !important;
    }}
    .stButton > button, .stDownloadButton > button, .stLinkButton > a {{
        background-color: #ffffff !important;
        color: #0b1320 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

st.set_page_config(layout="wide")
set_page_background("sfondo.png")  # 👈 nome del file PNG che vuoi usare come sfondo

# --- FUNZIONE UPLOAD GITHUB (create/update) ---
def _get_token():
    return st.secrets.get("github_token") or st.secrets.get("GITHUB_TOKEN")

def _gh_headers(token: str):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "streamlit-admin",
    }

def _get_default_branch(repo: str, token: str) -> str | None:
    r = requests.get(f"https://api.github.com/repos/{repo}",
                     headers=_gh_headers(token), timeout=30)
    if r.status_code == 200:
        return r.json().get("default_branch", "main")
    return None

def _get_current_sha(repo: str, path_in_repo: str, branch: str, token: str) -> str | None:
    r = requests.get(
        f"https://api.github.com/repos/{repo}/contents/{path_in_repo}",
        headers=_gh_headers(token),
        params={"ref": branch},
        timeout=30,
    )
    if r.status_code == 200:
        return r.json().get("sha")
    if r.status_code == 404:
        return None
    # altro errore
    raise RuntimeError(f"GET contents fallito: {r.status_code} – {r.json().get('message','')}")

def upload_to_github(repo: str, path_in_repo: str, file_data: bytes,
                     commit_message: str, branch: str | None = None) -> tuple[bool, str | None]:
    """
    Crea/Aggiorna un file nel repo indicato.
    Ritorna (ok, commit_html_url|msg_errore).
    - Se branch è None, usa il default branch del repo.
    """
    token = _get_token()
    if not token:
        return (False, "Secret GitHub mancante (github_token / GITHUB_TOKEN).")

    # 1) Scopri il branch corretto
    if branch is None:
        branch = _get_default_branch(repo, token)
        if not branch:
            return (False, "Impossibile leggere il default branch del repository.")

    # 2) Recupera lo SHA se il file esiste su quel branch
    try:
        sha = _get_current_sha(repo, path_in_repo, branch, token)
    except Exception as e:
        return (False, str(e))

    # 3) PUT contenuti
    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    payload = {
        "message": commit_message,
        "content": base64.b64encode(file_data).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=_gh_headers(token), json=payload, timeout=30)

    if r.status_code in (200, 201):
        data = r.json()
        # alcune risposte includono il commit HTML URL
        commit_url = None
        if isinstance(data, dict):
            commit = data.get("commit") or {}
            commit_url = commit.get("html_url")
        return (True, commit_url or f"Commit su branch '{branch}' eseguito.")
    else:
        try:
            msg = r.json().get("message", "")
        except Exception:
            msg = r.text
        return (False, f"{r.status_code} – {msg}")

# --- HEADER ---
st.image("LogoEuroirte.png", width=180)
st.link_button("🏠 Torna alla Home", url="https://homeeuroirte.streamlit.app/")

# --- Nuovo titolo e pulsante per avanzamento economico ---
st.title("Verifica l'avanzamento economico")
st.link_button("💶 Vai al Report Economico", "https://avanzamento-economico.streamlit.app/")

st.title("Gestione file")

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
#  nuovo: "Giacenza guasti TIM" -> carica 'giacenza.xlsx' sul repo Avanzamento-Impulsiva-v2
report_options = {
    "Delivery TIM": ("delivery.xlsx", "lbianco11197/Avanzamento-Delivery"),
    "Rework/PD": ("reworkpd.xlsx", "lbianco11197/Avanzamento-Impulsiva-v2"),
    "Giacenza guasti TIM": ("giacenza.xlsx", "lbianco11197/Avanzamento-Impulsiva-v2"),
    "Delivery Open Fiber": ("deliveryopenfiber.xlsx", "lbianco11197/Avanzamento-Delivery-OF"),
    "Avanzamento Economico": ("Avanzamento.xlsx", "lbianco11197/Avanzamento-economico"),
}

report_choice = st.selectbox("Seleziona il report da aggiornare", list(report_options.keys()))
selected_file_name, github_repo = report_options[report_choice]

# Messaggio specifico per la giacenza, altrimenti generico
if report_choice == "Giacenza guasti TIM":
    st.info("Il file da caricare deve chiamarsi **giacenza.xlsx**")
else:
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
            # Validazione minima: apri/leggi per assicurarti che non sia corrotto
            df_preview = pd.read_excel(uploaded_file)  # solo preview
            excel_bytes = uploaded_file.getvalue()

            ok, info = upload_to_github(
                repo=github_repo,
                path_in_repo=selected_file_name,
                file_data=excel_bytes,
                commit_message=f"Aggiornato {selected_file_name} da {username} via Streamlit",
                branch=None,  # usa il default branch auto (main/master/altro)
            )
            if ok:
                st.success("✅ File aggiornato sul repository.")
                if info:
                    st.markdown(f"**Commit:** {info}")
            else:
                st.error(f"❌ Upload fallito: {info}")
            
            
            st.markdown("**Anteprima (prime righe):**")
            st.dataframe(df_preview.head(20), use_container_width=True)

        except Exception as e:
            st.error(f"Errore durante l'upload del file: {e}")
