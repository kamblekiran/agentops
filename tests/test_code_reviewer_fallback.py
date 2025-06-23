
import pytest
from unittest import mock
from agents.code_reviewer_agent import CodeReviewerAgent

@mock.patch("agents.code_reviewer_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.code_reviewer_agent.log_session")
@mock.patch("agents.code_reviewer_agent.gemini_prompt", side_effect=Exception("Gemini fail"))
@mock.patch("subprocess.run")
@mock.patch("shutil.rmtree")
@mock.patch("os.path.exists", return_value=True)
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data="def test():\n    assert True")
def test_run_production_mode_fallback(mock_open, mock_exists, mock_rmtree, mock_subprocess,
                                      mock_gemini, mock_logger, mock_sim):
    agent = CodeReviewerAgent()
    result = agent.run("https://github.com/example/repo")
    assert result["status"] == "error"
    assert "Gemini fail" in result.get("reason", "")
