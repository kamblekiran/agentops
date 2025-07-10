import streamlit as st
st.set_page_config(page_title="AgentOps", layout="wide")

import importlib.util
import os
from utils.azure_auth import login_user, verify_id_token, refresh_id_token

# --- Inject Sidebar Styling ---
st.markdown("""
    <style>
    .sidebar-section {
        padding: 1rem;
        margin-bottom: 1.5rem;
        background-color: #1e1e1e;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .sidebar-sub {
        font-size: 0.9rem;
        color: #bbbbbb;
        margin-bottom: 0.5rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# --- Initialize session state variables ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "refresh_token" not in st.session_state:
    st.session_state["refresh_token"] = None
if "id_token" not in st.session_state:
    st.session_state["id_token"] = None

# --- Sync refresh_token from URL to session state ---
url_token = st.query_params.get("token", [None])[0]
if url_token and url_token != st.session_state["refresh_token"]:
    st.session_state["refresh_token"] = url_token

# --- Attempt silent login if not authenticated ---
if not st.session_state["authenticated"]:
    if st.session_state["refresh_token"]:
        try:
            refreshed_user = refresh_id_token(st.session_state["refresh_token"])
            if refreshed_user:
                st.session_state["authenticated"] = True
                st.session_state["user"] = refreshed_user
                st.session_state["id_token"] = refreshed_user["idToken"]
                st.session_state["refresh_token"] = refreshed_user["refreshToken"]
                # Update URL param with refreshed token if changed
                if st.query_params.get("token", [None])[0] != refreshed_user["refreshToken"]:
                    st.query_params = {"token": refreshed_user["refreshToken"]}
        except Exception as e:
            if "INVALID_REFRESH_TOKEN" in str(e):
                st.session_state["authenticated"] = False
                st.session_state["user"] = None
                st.session_state["refresh_token"] = None
                st.session_state["id_token"] = None
                st.query_params = {}

# --- Show login UI if not authenticated ---
if not st.session_state["authenticated"]:
    st.title("🔐 Sign In to Azure AgentOps")
    st.markdown("Please enter your credentials to continue.")
    username = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["user"] = user
            st.session_state["id_token"] = user["idToken"]
            st.session_state["refresh_token"] = user["refreshToken"]
            # Store refresh token in URL params for persistence
            st.query_params = {"token": user["refreshToken"]}
            st.rerun()
        else:
            st.error("❌ Invalid credentials")
    st.stop()

# --- Initialize Execution Mode (default = production) ---
if "mode" not in st.session_state:
    st.session_state["mode"] = "production"

# --- Sidebar UI ---
with st.sidebar:
    if st.button("🚪 Logout"):
        for key in ["authenticated", "user", "id_token", "refresh_token"]:
            st.session_state.pop(key, None)
        st.query_params = {}  # Clear URL params on logout
        st.rerun()

    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>⚙️ Execution Mode</div>", unsafe_allow_html=True)
    st.selectbox(
        "Choose Mode",
        ["simulation", "production"],
        index=0 if st.session_state["mode"] == "simulation" else 1,
        key="mode",
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>🧭 Navigation</div>", unsafe_allow_html=True)
    page = st.radio(
        "Go to",
        ["🔹 Run Pipeline", "📜 Historical Runs", "📊 Dashboards"],
        index=0,
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# --- Page Routing Map ---
PAGE_MODULES = {
    "🔹 Run Pipeline": "sections/run_pipeline.py",
    "📜 Historical Runs": "sections/historical_runs.py",
    "📊 Dashboards": "sections/dashboard.py",
}

# --- Render Selected Page ---
def render_page(file_path):
    absolute_path = os.path.abspath(file_path)
    spec = importlib.util.spec_from_file_location("current_page", absolute_path)
    page = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(page)

if page in PAGE_MODULES:
    render_page(PAGE_MODULES[page])
else:
    st.title("🤖 Azure AgentOps — AI DevOps Assistant")
    st.markdown("Use the sidebar to begin.")
