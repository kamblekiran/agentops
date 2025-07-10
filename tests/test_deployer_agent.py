import pytest
from unittest import mock
from agents.deployer_agent import DeployAgent

@mock.patch("agents.deployer_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = DeployAgent()
    azure_config = {"resource_group": "test-rg"}
    result = agent.run("testregistry.azurecr.io/app:latest", azure_config)
    assert result["status"] == "success"
    assert "deployed_url" in result
    assert "azurecontainerapps.io" in result["deployed_url"]

@mock.patch("agents.deployer_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.deployer_agent.log_session")
@mock.patch("utils.azure.deploy_to_container_apps")
def test_production_mode(mock_deploy, mock_logger, mock_sim):
    mock_deploy.return_value = "https://test-app.azurecontainerapps.io"
    agent = DeployAgent()
    azure_config = {"resource_group": "test-rg", "location": "eastus"}
    result = agent.run("testregistry.azurecr.io/app:latest", azure_config)
    assert result["status"] == "success"
    assert "deployed_url" in result
    assert result["critical"] is False