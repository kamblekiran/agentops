import pytest
from unittest import mock
from agents.monitor_agent import MonitorAgent

@mock.patch("agents.monitor_agent.is_simulation_mode", return_value=True)
def test_simulation_mode(mock_sim):
    agent = MonitorAgent()
    azure_config = {"resource_group": "test-rg"}
    result = agent.run(azure_config)
    assert isinstance(result, dict)
    assert any("errors" in v or "summary" in v for v in result.values())