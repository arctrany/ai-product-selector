"""Test cases for refactored app routes with flow_id-version format."""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workflow_engine.api.server import create_app
from workflow_engine.apps.manager import AppManager
from workflow_engine.storage.database import DatabaseManager

class TestAppRoutesRefactored:
    """Test refactored app routes with flow_id-version format."""

    @pytest.fixture
    def mock_app_manager(self):
        """Create mock app manager."""
        app_manager = Mock(spec=AppManager)

        # Mock app configuration
        mock_app = Mock()
        mock_app.app_id = "sample_app"
        mock_app.name = "示例工作流应用"
        mock_app.console_title = "示例工作流控制台"
        mock_app.extensions = []

        # Mock flow configurations
        mock_flow1 = Mock()
        mock_flow1.flow_id = "abba-ccdd-eeff"
        mock_flow1.version = "1.0.0"
        mock_flow1.title = "循环演示工作流"
        mock_flow1.description = "循环节点 + 分支节点 + 延时节点"

        mock_flow2 = Mock()
        mock_flow2.flow_id = "ghij-klmn-opqr-stuv"
        mock_flow2.version = "1.0.0"
        mock_flow2.title = "数据处理工作流"
        mock_flow2.description = "数据处理 + 分支判断 + 通知/错误处理"

        # Add complex flow for edge case testing
        mock_flow3 = Mock()
        mock_flow3.flow_id = "complex-flow-id-with-many-hyphens"
        mock_flow3.version = "2.1.0"
        mock_flow3.title = "复杂流程ID测试"
        mock_flow3.description = "测试复杂的流程ID解析"

        mock_app.flows = {
            "flow1": mock_flow1,
            "flow2": mock_flow2,
            "complex_flow": mock_flow3
        }
        mock_app.flow_ids = ["flow1", "flow2", "complex_flow"]

        app_manager.get_app.return_value = mock_app
        app_manager.list_apps.return_value = [mock_app]

        return app_manager

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        db_manager = Mock(spec=DatabaseManager)

        def mock_get_flow_by_name(flow_name):
            """Mock get_flow_by_name with different flows."""
            if flow_name == "abba-ccdd-eeff":
                return {"flow_id": 1, "name": "abba-ccdd-eeff"}
            elif flow_name == "complex-flow-id-with-many-hyphens":
                return {"flow_id": 2, "name": "complex-flow-id-with-many-hyphens"}
            return None

        def mock_get_flow_version_by_version(flow_id, version):
            """Mock get_flow_version_by_version."""
            if flow_id == 1 and version == "1.0.0":
                return {
                    "flow_version_id": 1,
                    "version": "1.0.0",
                    "flow_id": 1,
                    "published": True
                }
            elif flow_id == 2 and version == "2.1.0":
                return {
                    "flow_version_id": 2,
                    "version": "2.1.0",
                    "flow_id": 2,
                    "published": True
                }
            return None

        def mock_get_latest_flow_version(flow_id):
            """Mock get_latest_flow_version."""
            if flow_id == 1:
                return {
                    "flow_version_id": 1,
                    "version": "1.0.0",
                    "flow_id": 1,
                    "published": True
                }
            elif flow_id == 2:
                return {
                    "flow_version_id": 2,
                    "version": "2.1.0",
                    "flow_id": 2,
                    "published": True
                }
            return None

        db_manager.get_flow_by_name.side_effect = mock_get_flow_by_name
        db_manager.get_latest_flow_version.side_effect = mock_get_latest_flow_version
        db_manager.get_flow_version_by_version.side_effect = mock_get_flow_version_by_version
        db_manager.list_runs.return_value = []

        return db_manager

    @pytest.fixture
    def client(self, mock_app_manager, mock_db_manager):
        """Create test client."""
        with patch('workflow_engine.apps.manager.AppManager', return_value=mock_app_manager), \
             patch('workflow_engine.storage.database.DatabaseManager', return_value=mock_db_manager), \
             patch('workflow_engine.config.get_config') as mock_config:

            # Mock config
            mock_config_obj = Mock()
            mock_config_obj.get_apps_directory_path.return_value = Path("/tmp/apps")
            mock_config_obj.get_templates_directory_path.return_value = Path("/tmp/templates")
            mock_config_obj.get_database_path.return_value = Path("/tmp/test.db")
            mock_config.return_value = mock_config_obj

            app = create_app()
            return TestClient(app)

    def test_flow_console_page_with_flow_id(self, client):
        """Test flow console page using flow_id."""
        response = client.get("/sample_app/abba-ccdd-eeff")
        assert response.status_code == 200
        assert "流程控制台" in response.text

    def test_flow_console_page_invalid_flow_id(self, client):
        """Test flow console page with invalid flow_id."""
        response = client.get("/sample_app/invalid-flow-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_flow_console_page_invalid_app(self, client, mock_app_manager):
        """Test flow console page with invalid app."""
        mock_app_manager.get_app.return_value = None
        response = client.get("/invalid_app/abba-ccdd-eeff")
        assert response.status_code == 404
        assert "Application not found" in response.json()["detail"]

    def test_submit_flow_form_with_version(self, client, mock_db_manager):
        """Test form submission with specific version."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "test-thread-id"
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff-1.0.0/submit",
                data={"test_field": "test_value"}
            )
            assert response.status_code == 302  # Redirect
            assert "abba-ccdd-eeff" in response.headers["location"]

    def test_submit_flow_form_latest_version(self, client, mock_db_manager):
        """Test form submission with latest version."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "test-thread-id"
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff/submit",
                data={"test_field": "test_value"}
            )
            assert response.status_code == 302  # Redirect

    def test_submit_flow_form_invalid_flow(self, client, mock_db_manager):
        """Test form submission with invalid flow."""
        response = client.post(
            "/api/flows/invalid-flow-id/submit",
            data={"test_field": "test_value"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_start_workflow_api_with_version(self, client, mock_db_manager):
        """Test start workflow API with specific version."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "test-thread-id"
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff-1.0.0/start",
                json={"input_data": "test"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["flow_id"] == "abba-ccdd-eeff"
            assert data["version"] == "1.0.0"
            assert data["thread_id"] == "test-thread-id"
            assert data["status"] == "started"

    def test_start_workflow_api_latest_version(self, client, mock_db_manager):
        """Test start workflow API with latest version."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "test-thread-id"
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff/start",
                json={"input_data": "test"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["flow_id"] == "abba-ccdd-eeff"
            assert data["version"] == "latest"
            assert data["thread_id"] == "test-thread-id"

    def test_start_workflow_api_invalid_flow(self, client, mock_db_manager):
        """Test start workflow API with invalid flow."""
        response = client.post(
            "/api/flows/invalid-flow-id/start",
            json={"input_data": "test"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_stop_workflow_api(self, client, mock_db_manager):
        """Test stop workflow API."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.pause_workflow.return_value = True
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff-1.0.0/stop",
                json={"thread_id": "test-thread-id"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["flow_id"] == "abba-ccdd-eeff"
            assert data["version"] == "1.0.0"
            assert data["status"] == "stopped"

    def test_stop_workflow_api_not_found(self, client, mock_db_manager):
        """Test stop workflow API with workflow not found."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.pause_workflow.return_value = False
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff-1.0.0/stop",
                json={"thread_id": "invalid-thread-id"}
            )
            assert response.status_code == 404
            assert "cannot be stopped" in response.json()["detail"]

    def test_resume_workflow_api(self, client, mock_db_manager):
        """Test resume workflow API."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.resume_workflow.return_value = True
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff-1.0.0/resume",
                json={"thread_id": "test-thread-id", "updates": {"key": "value"}}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["flow_id"] == "abba-ccdd-eeff"
            assert data["version"] == "1.0.0"
            assert data["status"] == "resumed"
            assert data["updates"] == {"key": "value"}

    def test_resume_workflow_api_not_found(self, client, mock_db_manager):
        """Test resume workflow API with workflow not found."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.resume_workflow.return_value = False
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff-1.0.0/resume",
                json={"thread_id": "invalid-thread-id"}
            )
            assert response.status_code == 404
            assert "cannot be resumed" in response.json()["detail"]

    def test_parse_flow_version_id_with_version(self, client):
        """Test parsing flow_id-version parameter."""
        # This tests the internal parse function through API calls
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "test-thread-id"
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff-1.0.0/start",
                json={"input_data": "test"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["flow_id"] == "abba-ccdd-eeff"
            assert data["version"] == "1.0.0"

    def test_parse_flow_version_id_without_version(self, client):
        """Test parsing flow_id parameter without version."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "test-thread-id"
            mock_engine.return_value = mock_engine_instance

            response = client.post(
                "/api/flows/abba-ccdd-eeff/start",
                json={"input_data": "test"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["flow_id"] == "abba-ccdd-eeff"
            assert data["version"] == "latest"

    def test_custom_page_with_flow_id(self, client):
        """Test custom page access with flow_id."""
        with patch('os.path.exists', return_value=False):
            response = client.get("/sample_app/abba-ccdd-eeff.htm")
            assert response.status_code == 404
            assert "Custom template not found" in response.json()["detail"]

    def test_edge_cases_complex_flow_id(self, client, mock_app_manager, mock_db_manager):
        """Test edge cases with complex flow IDs containing hyphens."""
        with patch('workflow_engine.core.engine.WorkflowEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "complex-thread-id"
            mock_engine.return_value = mock_engine_instance

            # Test with specific version
            response = client.post(
                "/api/flows/complex-flow-id-with-many-hyphens-2.1.0/start",
                json={"input_data": "test"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["flow_id"] == "complex-flow-id-with-many-hyphens"
            assert data["version"] == "2.1.0"

    def test_flexible_app_name_access(self, client):
        """Test flexible app name access (sample-app vs sample_app)."""
        # Test hyphenated app name access
        response = client.get("/sample-app/flow1")
        assert response.status_code == 200
        assert "流程控制台" in response.text

    def test_flow_name_access(self, client):
        """Test access by flow_name (flow1) instead of flow_id."""
        response = client.get("/sample_app/flow1")
        assert response.status_code == 200
        assert "流程控制台" in response.text

    def test_flow_id_with_version_access(self, client):
        """Test access by flow_id with version."""
        response = client.get("/sample_app/abba-ccdd-eeff-1.0.0")
        assert response.status_code == 200
        assert "流程控制台" in response.text

    def test_custom_page_flow_name_access(self, client):
        """Test custom page access by flow_name."""
        with patch('os.path.exists', return_value=False):
            response = client.get("/sample-app/flow1.htm")
            assert response.status_code == 404
            assert "Custom template not found" in response.json()["detail"]

    def test_custom_page_flow_id_with_version_access(self, client):
        """Test custom page access by flow_id with version."""
        with patch('os.path.exists', return_value=False):
            response = client.get("/sample_app/abba-ccdd-eeff-1.0.0.htm")
            assert response.status_code == 404
            assert "Custom template not found" in response.json()["detail"]

    def test_htm_extension_access_flow_name(self, client):
        """Test .htm extension access by flow_name."""
        with patch('os.path.exists', return_value=False):
            response = client.get("/sample-app/flow1.htm")
            assert response.status_code == 404
            assert "Custom template not found" in response.json()["detail"]

    def test_htm_extension_access_flow_id_with_version(self, client):
        """Test .htm extension access by flow_id with version."""
        with patch('os.path.exists', return_value=False):
            response = client.get("/sample_app/abba-ccdd-eeff-1.0.0.htm")
            assert response.status_code == 404
            assert "Custom template not found" in response.json()["detail"]

    def test_htm_extension_access_flow_id(self, client):
        """Test .htm extension access by flow_id."""
        with patch('os.path.exists', return_value=False):
            response = client.get("/sample_app/abba-ccdd-eeff.htm")
            assert response.status_code == 404
            assert "Custom template not found" in response.json()["detail"]

    def test_invalid_flow_identifier(self, client):
        """Test invalid flow identifier."""
        response = client.get("/sample_app/invalid-flow")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_invalid_app_name_variations(self, client, mock_app_manager):
        """Test invalid app name variations."""
        mock_app_manager.get_app.return_value = None

        response = client.get("/invalid-app/flow1")
        assert response.status_code == 404
        assert "Application not found" in response.json()["detail"]

class TestDatabaseCleanup:
    """Test database cleanup functionality."""

    def test_cleanup_test_data(self):
        """Clean up test data from database."""
        # This would be implemented based on your database structure
        # For now, it's a placeholder for the cleanup functionality
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])