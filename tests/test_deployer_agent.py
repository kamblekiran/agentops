
import pytest
from unittest import mock
from agents.deployer_agent import DeployAgent

@mock.patch("agents.deployer_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = DeployAgent()
    result = agent.run("gcr.io/project/image:latest", "dummy-project")
    assert result["status"] == "success"
    assert "deployed_url" in result

@mock.patch("agents.deployer_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.deployer_agent.log_session")
@mock.patch("subprocess.run")
@mock.patch("shutil.rmtree")
@mock.patch("os.path.exists", return_value=True)
def test_production_mode(mock_exists, mock_rmtree, mock_subprocess, mock_logger, mock_sim):
    agent = DeployAgent()
    result = agent.run("gcr.io/project/image:latest", "dummy-project")
    assert result["status"] == "success"
    assert "deployed_url" in result
    assert result["critical"] is False
