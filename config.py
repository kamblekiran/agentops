import streamlit as st

def get_ui_mode() -> str:
    return st.session_state.get("mode", "simulation")

def is_simulation_mode() -> bool:
    return get_ui_mode() == "simulation"
