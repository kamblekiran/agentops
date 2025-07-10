import streamlit as st

def get_ui_mode() -> str:
    return st.session_state.get("mode", "simulation")

def is_simulation_mode() -> bool:
    return get_ui_mode() == "simulation"

def get_azure_config():
    """Get Azure configuration from environment variables"""
    import os
    return {
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
        "resource_group": os.getenv("AZURE_RESOURCE_GROUP", "agentops-rg"),
        "location": os.getenv("AZURE_LOCATION", "eastus"),
        "container_registry": os.getenv("AZURE_CONTAINER_REGISTRY"),
        "app_service_plan": os.getenv("AZURE_APP_SERVICE_PLAN", "agentops-plan")
    }
