import pytest
from unittest import mock
from agents.code_reviewer_agent import CodeReviewerAgent
from agents.builder_agent import BuildAgent
from agents.deployer_agent import DeployAgent
from agents.monitor_agent import MonitorAgent
from agents.rollback_agent import RollbackAgent
from agents.sre_agent import SREAgent

class TestAzureAgentsIntegration:
    """Integration tests for Azure-migrated agents"""
    
    def setup_method(self):
        self.azure_config = {
            "resource_group": "test-rg",
            "location": "eastus",
            "container_registry": "testregistry",
            "subscription_id": "test-sub-id"
        }
        self.repo_url = "https://github.com/test/repo"
    
    @mock.patch("agents.code_reviewer_agent.is_simulation_mode", return_value=True)
    @mock.patch("agents.code_reviewer_agent.log_session")
    def test_code_reviewer_azure_simulation(self, mock_logger, mock_sim):
        agent = CodeReviewerAgent()
        result = agent.run(self.repo_url)
        
        assert result["status"] == "success"
        assert "review" in result
        assert result["critical"] is False
        mock_logger.assert_called_once()
    
    @mock.patch("agents.builder_agent.is_simulation_mode", return_value=True)
    @mock.patch("agents.builder_agent.log_session")
    def test_builder_azure_simulation(self, mock_logger, mock_sim):
        agent = BuildAgent()
        result = agent.run(self.repo_url, self.azure_config)
        
        assert result["status"] == "success"
        assert "azurecr.io" in result["image_url"]
        assert result["critical"] is False
        mock_logger.assert_called_once()
    
    @mock.patch("agents.deployer_agent.is_simulation_mode", return_value=True)
    @mock.patch("agents.deployer_agent.log_session")
    def test_deployer_azure_simulation(self, mock_logger, mock_sim):
        agent = DeployAgent()
        image_url = "testregistry.azurecr.io/app:latest"
        result = agent.run(image_url, self.azure_config)
        
        assert result["status"] == "success"
        assert "azurecontainerapps.io" in result["deployed_url"]
        assert result["critical"] is False
        mock_logger.assert_called_once()
    
    @mock.patch("agents.monitor_agent.is_simulation_mode", return_value=True)
    @mock.patch("agents.monitor_agent.log_session")
    def test_monitor_azure_simulation(self, mock_logger, mock_sim):
        agent = MonitorAgent()
        result = agent.run(self.azure_config)
        
        assert isinstance(result, dict)
        assert len(result) > 0
        # Check that at least one service was monitored
        for service_result in result.values():
            assert "status" in service_result
            assert "summary" in service_result
    
    @mock.patch("agents.rollback_agent.is_simulation_mode", return_value=True)
    @mock.patch("agents.rollback_agent.log_session")
    def test_rollback_azure_simulation(self, mock_logger, mock_sim):
        agent = RollbackAgent()
        result = agent.run(self.azure_config, "test-app")
        
        assert result["status"] == "success"
        assert result["restored"] is True
        assert "previous_revision" in result
        mock_logger.assert_called_once()
    
    @mock.patch("agents.sre_agent.is_simulation_mode", return_value=True)
    @mock.patch("agents.sre_agent.log_session")
    def test_sre_azure_simulation(self, mock_logger, mock_sim):
        agent = SREAgent()
        result = agent.run(self.repo_url, self.azure_config)
        
        assert result["status"] == "success"
        assert "summary" in result
        assert "recommended_actions" in result
        assert "risk_score" in result
        mock_logger.assert_called_once()
    
    def test_azure_config_structure(self):
        """Test that Azure config has required fields"""
        required_fields = ["resource_group", "location", "container_registry"]
        for field in required_fields:
            assert field in self.azure_config
            assert self.azure_config[field] is not None
    
    @mock.patch("utils.azure.is_simulation_mode", return_value=True)
    def test_azure_image_url_format(self, mock_sim):
        """Test that Azure image URLs follow correct format"""
        from utils.azure import build_container
        
        result = build_container(self.repo_url, self.azure_config)
        assert ".azurecr.io/" in result
        assert ":latest" in result
        assert self.azure_config["container_registry"] in result
    
    @mock.patch("utils.azure.is_simulation_mode", return_value=True)
    def test_azure_deployment_url_format(self, mock_sim):
        """Test that Azure deployment URLs follow correct format"""
        from utils.azure import deploy_to_container_apps
        
        image_url = "testregistry.azurecr.io/app:latest"
        result = deploy_to_container_apps(image_url, self.azure_config)
        assert "azurecontainerapps.io" in result
        assert result.startswith("https://")