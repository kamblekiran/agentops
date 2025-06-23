import pytest
from unittest import mock
from agents.code_reviewer_agent import CodeReviewerAgent
from agents.regression_checker_agent import RegressionCheckerAgent
from agents.builder_agent import BuildAgent
from agents.deployer_agent import DeployAgent
from agents.rollback_agent import RollbackAgent
from agents.sre_agent import SREAgent
from agents.monitor_agent import MonitorAgent
from agents.test_writer_agent import TestWriterAgent
from agents.build_failure_analyzer_agent import BuildFailureAnalyzerAgent

@mock.patch("agents.code_reviewer_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.code_reviewer_agent.log_session")
def test_code_reviewer_llm_failure(mock_logger, mock_sim):
    agent = CodeReviewerAgent()
    result = agent.run("https://github.com/example/repo")
    assert result["status"] in ["error", "success"]

@mock.patch("agents.regression_checker_agent.is_simulation_mode", return_value=True)
@mock.patch("agents.regression_checker_agent.log_session")
def test_regression_checker_no_tests(mock_logger, mock_sim):
    agent = RegressionCheckerAgent()
    result = agent.run("https://github.com/example/repo")
    assert "status" in result

@mock.patch("agents.builder_agent.is_simulation_mode", return_value=True)
@mock.patch("agents.builder_agent.log_session")
def test_builder_docker_failure(mock_logger, mock_sim):
    agent = BuildAgent()
    result = agent.run("https://github.com/example/repo", "dummy-project")
    assert "status" in result

@mock.patch("agents.rollback_agent.is_simulation_mode", return_value=False)
@mock.patch("agents.rollback_agent.log_session")
def test_rollback_gcp_failure(mock_logger, mock_sim):
    agent = RollbackAgent()
    try:
        result = agent.run("dummy-project")
        assert result["status"] in ["error", "success"]
    except Exception as e:
        assert "failed" in str(e).lower()

@mock.patch("agents.deployer_agent.is_simulation_mode", return_value=True)
@mock.patch("agents.deployer_agent.log_session")
def test_deployer_no_logs(mock_logger, mock_sim):
    agent = DeployAgent()
    result = agent.run("https://github.com/example/repo", "dummy-project")
    assert "deployed_url" in result

@mock.patch("agents.monitor_agent.is_simulation_mode", return_value=True)
@mock.patch("agents.monitor_agent.log_session")
def test_monitor_simulation_success(mock_logger, mock_sim):
    agent = MonitorAgent()
    result = agent.run("dummy-project")
    assert isinstance(result, dict)

@mock.patch("agents.test_writer_agent.is_simulation_mode", return_value=True)
@mock.patch("agents.test_writer_agent.log_session")
def test_test_writer_fallback(mock_logger, mock_sim):
    agent = TestWriterAgent()
    result = agent.run("https://github.com/example/repo")
    assert "generated_tests" in result

@mock.patch("agents.build_failure_analyzer_agent.is_simulation_mode", return_value=True)
@mock.patch("agents.build_failure_analyzer_agent.log_session")
def test_build_analyzer_default(mock_logger, mock_sim):
    agent = BuildFailureAnalyzerAgent()
    result = agent.run("Build failed logs", "https://github.com/example/repo")
    assert "llm_analysis" in result