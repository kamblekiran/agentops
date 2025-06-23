import pytest
from unittest import mock
from agents.rollback_agent import RollbackAgent

@mock.patch("agents.rollback_agent.is_simulation_mode", return_value=True)
@mock.patch("agents.rollback_agent.log_session")
def test_simulation_mode(mock_logger, mock_sim_mode):
    agent = RollbackAgent()
    result = agent.run("gcr.io/project/image:previous", "dummy-project")
    assert result["status"] == "success"
    assert result["critical"] is False
    assert "input" in result

