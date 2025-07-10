import pytest
from unittest import mock
from agents.rollback_agent import RollbackAgent

@mock.patch("agents.rollback_agent.is_simulation_mode", return_value=True)
@mock.patch("agents.rollback_agent.log_session")
def test_simulation_mode(mock_logger, mock_sim_mode):
    agent = RollbackAgent()
    azure_config = {"resource_group": "test-rg"}
    result = agent.run(azure_config, "test-app")
    assert result["status"] == "success"
    assert result["critical"] is False
    assert "input" in result
    assert "azure_config" in result["input"]

@mock.patch("agents.rollback_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.rollback_agent.log_session")
@mock.patch("subprocess.run")
def test_production_mode_azure_failure(mock_subprocess, mock_logger, mock_sim):
    mock_subprocess.side_effect = Exception("Azure CLI error")
    agent = RollbackAgent()
    azure_config = {"resource_group": "test-rg"}
    result = agent.run(azure_config, "test-app")
    assert result["status"] == "error"
    assert "Azure CLI error" in result["reason"]