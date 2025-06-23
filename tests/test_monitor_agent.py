
import pytest
from unittest import mock
from agents.monitor_agent import MonitorAgent

@mock.patch("agents.monitor_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = MonitorAgent()
    result = agent.run("dummy-project")
    assert isinstance(result, dict)
    assert any("errors" in v or "output" in v for v in result.values())
