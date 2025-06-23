
import pytest
from unittest import mock
from agents.build_failure_analyzer_agent import BuildFailureAnalyzerAgent

@mock.patch("agents.build_failure_analyzer_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = BuildFailureAnalyzerAgent()
    result = agent.run("build log content")
    assert "llm_analysis" in result
    assert "recommendations" in result
    assert result["critical"] is False

@mock.patch("agents.build_failure_analyzer_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.build_failure_analyzer_agent.log_session")
@mock.patch("agents.build_failure_analyzer_agent.gemini_prompt", return_value="Build failed due to missing Dockerfile")
def test_production_mode(mock_prompt, mock_logger, mock_sim):
    agent = BuildFailureAnalyzerAgent()
    result = agent.run("build log content")
    assert "llm_analysis" in result
    assert result["status"] == "success"
    assert result["critical"] is False
