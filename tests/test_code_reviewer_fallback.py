import pytest
from unittest import mock
from agents.code_reviewer_agent import CodeReviewerAgent

@mock.patch("agents.code_reviewer_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.code_reviewer_agent.log_session")
@mock.patch("agents.code_reviewer_agent.azure_openai_prompt", side_effect=Exception("Azure OpenAI fail"))
def test_run_production_mode_fallback(mock_openai, mock_logger, mock_sim):
    agent = CodeReviewerAgent()
    result = agent.run("https://github.com/example/repo")
    assert result["status"] == "error"
    assert "Azure OpenAI fail" in result.get("reason", "")