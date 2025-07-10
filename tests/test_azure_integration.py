import pytest
from unittest import mock
from utils.azure import build_container, deploy_to_container_apps
from utils.azure_openai import azure_openai_prompt
from utils.azure_cosmos import log_session, fetch_agent_history

@mock.patch("utils.azure.is_simulation_mode", return_value=True)
def test_azure_build_simulation(mock_sim):
    azure_config = {
        "container_registry": "testregistry",
        "resource_group": "test-rg"
    }
    result = build_container("https://github.com/test/repo", azure_config)
    assert "testregistry.azurecr.io" in result
    assert "repo:latest" in result

@mock.patch("utils.azure.is_simulation_mode", return_value=True)
def test_azure_deploy_simulation(mock_sim):
    azure_config = {
        "resource_group": "test-rg",
        "location": "eastus"
    }
    result = deploy_to_container_apps("testregistry.azurecr.io/app:latest", azure_config)
    assert "azurecontainerapps.io" in result

@mock.patch("utils.azure_openai.is_simulation_mode", return_value=True)
def test_azure_openai_simulation(mock_sim):
    result = azure_openai_prompt([{"content": "test prompt"}])
    assert "SIMULATED AZURE OPENAI RESPONSE" in result

@mock.patch("utils.azure_cosmos.is_simulation_mode", return_value=True)
def test_cosmos_logging_simulation(mock_sim):
    # Should not raise any exceptions in simulation mode
    log_session("test-session", "test-agent", {"status": "success"})
    
    history = fetch_agent_history("test-agent")
    assert len(history) > 0
    assert "mock-session" in history[0]["session_id"]