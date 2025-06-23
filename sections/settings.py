import streamlit as st
from utils.firebase_logger import set_global_mode
from config import is_simulation_mode

st.set_page_config(page_title="Settings", layout="centered")
st.title("⚙️ AgentOps Settings")

current_mode = st.session_state.get("mode", "simulation")
st.markdown(f"### 🧠 Current Mode: **{current_mode.capitalize()}**")

# Radio input to update session and persist globally
selected_mode = st.radio("Choose execution mode:", ["simulation", "production"], 
                         index=0 if current_mode == "simulation" else 1)

# Update mode globally
if selected_mode != current_mode:
    st.session_state["mode"] = selected_mode
    set_global_mode(selected_mode)
    st.success(f"Mode updated to {selected_mode.capitalize()}")

# Optional debugging
st.caption(f"Simulation Active: `{is_simulation_mode()}`")
