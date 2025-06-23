
import pytest
from unittest import mock
from agents.builder_agent import BuildAgent

@mock.patch("agents.builder_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = BuildAgent()
    result = agent.run("https://github.com/example/repo", "dummy-project")
    assert result["status"] == "success"
    assert "image_url" in result
    assert isinstance(result["image_url"], str)

@mock.patch("agents.builder_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.builder_agent.log_session")
@mock.patch("subprocess.run")
@mock.patch("shutil.rmtree")
@mock.patch("os.path.exists", return_value=True)
def test_production_mode(mock_exists, mock_rmtree, mock_subprocess,
                         mock_logger, mock_sim):
    mock_subprocess.return_value.returncode = 0
    agent = BuildAgent()
    result = agent.run("https://github.com/example/repo", "dummy-project")
    assert result["status"] == "success"
    assert "image_url" in result
    assert result["critical"] is False
