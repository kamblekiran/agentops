import pytest
from unittest import mock
from agents.test_writer_agent import TestWriterAgent

@mock.patch("agents.test_writer_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.test_writer_agent.log_session")
@mock.patch("agents.test_writer_agent.azure_openai_prompt", side_effect=Exception("Azure OpenAI error"))
@mock.patch("subprocess.run")
@mock.patch("os.makedirs")
@mock.patch("shutil.rmtree")
@mock.patch("os.path.exists", return_value=True)
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data="def test():\n    assert True")
def test_run_production_mode_fallback(mock_open, mock_exists, mock_rmtree, mock_makedirs,
                                      mock_subprocess, mock_openai, mock_logger, mock_sim):
    agent = TestWriterAgent()
    result = agent.run("https://github.com/example/repo")
    assert result["status"] == "success"
    assert "unexpected error" in result["output"].lower()
    assert result["critical"] is False