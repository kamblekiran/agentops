
import pytest
from unittest import mock
from agents.sre_agent import SREAgent

@mock.patch("agents.sre_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = SREAgent()
    result = agent.run("https://example.com", "dummy-project")
    assert "output" in result or "recommended_actions" in result

@mock.patch("agents.sre_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.sre_agent.log_session")
@mock.patch("subprocess.run")
@mock.patch("shutil.rmtree")
@mock.patch("os.path.exists", return_value=True)
def test_production_mode(mock_exists, mock_rmtree, mock_subprocess, mock_logger, mock_sim):
    agent = SREAgent()
    result = agent.run("https://example.com", "dummy-project")
    assert "output" in result or "recommended_actions" in result
    assert result["critical"] is False
