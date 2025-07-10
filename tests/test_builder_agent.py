import pytest
from unittest import mock
from agents.builder_agent import BuildAgent

@mock.patch("agents.builder_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = BuildAgent()
    azure_config = {"container_registry": "testregistry"}
    result = agent.run("https://github.com/example/repo", azure_config)
    assert result["status"] == "success"
    assert "image_url" in result
    assert isinstance(result["image_url"], str)
    assert "azurecr.io" in result["image_url"]

@mock.patch("agents.builder_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.builder_agent.log_session")
@mock.patch("utils.azure.build_container")
def test_production_mode(mock_build_container, mock_logger, mock_sim):
    mock_build_container.return_value = "testregistry.azurecr.io/example-repo:latest"
    agent = BuildAgent()
    azure_config = {"container_registry": "testregistry", "resource_group": "test-rg"}
    result = agent.run("https://github.com/example/repo", azure_config)
    assert result["status"] == "success"
    assert "image_url" in result
    assert result["critical"] is False