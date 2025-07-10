import pytest
from unittest import mock
from agents.sre_agent import SREAgent

@mock.patch("agents.sre_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = SREAgent()
    azure_config = {"resource_group": "test-rg"}
    result = agent.run("https://example.com", azure_config)
    assert "output" in result or "recommended_actions" in result

@mock.patch("agents.sre_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.sre_agent.log_session")
@mock.patch("agents.sre_agent.azure_openai_prompt")
@mock.patch("agents.sre_agent.fetch_agent_history")
def test_production_mode(mock_fetch_history, mock_openai, mock_logger, mock_sim):
    mock_fetch_history.return_value = [{"data": {"summary": "Test summary"}}]
    mock_openai.return_value = """
    Summary: System is stable
    Root Cause: No issues detected
    Recommended Actions: Continue monitoring
    Risk Score: 15
    Critical: false
    """
    
    agent = SREAgent()
    azure_config = {"resource_group": "test-rg"}
    result = agent.run("https://example.com", azure_config)
    assert "output" in result or "recommended_actions" in result
    assert result["critical"] is False