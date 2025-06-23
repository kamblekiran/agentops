import pytest
from agents.test_writer_agent import TestWriterAgent

@pytest.fixture
def mock_generate_tests_with_llm(monkeypatch):
    def _mock(*args, **kwargs):
        return ["test_example.py"], "85%", "Mocked coverage output"
    monkeypatch.setattr("utils.gemini.generate_tests_with_llm", _mock)

@pytest.fixture
def mock_clone_repo(monkeypatch):
    def _mock(repo_url):
        return "/tmp/fake_repo"
    monkeypatch.setattr("utils.github.clone_repo", _mock)
