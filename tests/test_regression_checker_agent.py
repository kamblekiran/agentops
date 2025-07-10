import pytest
from unittest import mock
from agents.regression_checker_agent import RegressionCheckerAgent

@mock.patch("agents.regression_checker_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = RegressionCheckerAgent()
    result = agent.run("https://github.com/example/repo")
    assert result["status"] == "success"
    assert "failures" in result or "output" in result

@mock.patch("agents.regression_checker_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.regression_checker_agent.log_session")
@mock.patch("agents.regression_checker_agent.azure_openai_prompt")
@mock.patch("subprocess.run")
@mock.patch("shutil.rmtree")
@mock.patch("os.path.exists", return_value=True)
def test_production_mode(mock_exists, mock_rmtree, mock_subprocess, mock_openai, mock_logger, mock_sim):
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "All tests passed"
    mock_subprocess.return_value.stderr = ""
    mock_openai.return_value = "Test analysis complete"
    
    agent = RegressionCheckerAgent()
    result = agent.run("https://github.com/example/repo")
    assert result["status"] == "success"
    assert "output" in result
    assert result["critical"] is False