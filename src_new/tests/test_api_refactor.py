"""Unit tests for API refactoring - new thread control and flow APIs."""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from workflow_engine.api.thread_routes import create_thread_router
from workflow_engine.api.flow_routes import create_flow_router
from workflow_engine.api.dependencies import init_dependencies
from workflow_engine.api.exceptions import setup_exception_handlers


class TestThreadControlAPI:
    """Test cases for new thread control API endpoints."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with thread routes."""
        app = FastAPI()
        setup_exception_handlers(app)
        
        # Mock dependencies
        mock_engine = Mock()
        mock_app_manager = Mock()
        mock_templates = Mock()
        mock_config = Mock()
        
        init_dependencies(mock_engine, mock_app_manager, mock_templates, mock_config)
        
        app.include_router(create_thread_router(), prefix="/api")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        mock = Mock()
        mock.get_run.return_value = {
            "thread_id": "test-thread-123",
            "status": "pending",
            "flow_version_id": 1,
            "metadata": {"inputs": {"test": "data"}}
        }
        return mock

    @pytest.fixture
    def mock_control(self):
        """Mock workflow control."""
        mock = Mock()
        mock.start_workflow.return_value = "test-thread-123"
        mock.pause_workflow.return_value = True
        mock.resume_workflow.return_value = True
        return mock

    def test_start_thread_success(self, client, mock_db_manager, mock_control):
        """Test successful thread start."""
        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):
            
            response = client.post("/api/thread/test-thread-123/start", json={})
            
            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "test-thread-123"
            assert data["status"] == "started"
            assert "started successfully" in data["message"]

    def test_start_thread_not_found(self, client, mock_control):
        """Test thread start with non-existent thread."""
        mock_db_manager = Mock()
        mock_db_manager.get_run.return_value = None
        
        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):
            
            response = client.post("/api/thread/non-existent/start", json={})
            
            assert response.status_code == 404
            assert "not found" in response.json()["error"].lower()

    def test_start_thread_invalid_status(self, client, mock_control):
        """Test thread start with invalid status."""
        mock_db_manager = Mock()
        mock_db_manager.get_run.return_value = {
            "thread_id": "test-thread-123",
            "status": "completed",  # Cannot start completed thread
            "flow_version_id": 1
        }

        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.post("/api/thread/test-thread-123/start", json={})

            assert response.status_code == 400
            assert "cannot be started" in response.json()["error"]

    def test_pause_thread_success(self, client, mock_db_manager, mock_control):
        """Test successful thread pause."""
        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.post("/api/thread/test-thread-123/pause")

            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "test-thread-123"
            assert data["status"] == "pause_requested"

    def test_resume_thread_success(self, client, mock_db_manager, mock_control):
        """Test successful thread resume."""
        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.post("/api/thread/test-thread-123/resume", json={"updates": {"key": "value"}})

            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "test-thread-123"
            assert data["status"] == "resumed"

    def test_get_thread_status_success(self, client, mock_db_manager, mock_control):
        """Test successful thread status retrieval."""
        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.get("/api/thread/test-thread-123/status")

            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "test-thread-123"
            assert data["status"] == "pending"
            assert data["flow_version_id"] == 1

    def test_get_thread_logs_success(self, client, mock_db_manager):
        """Test successful thread logs retrieval."""
        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('builtins.open', create=True) as mock_open, \
             patch('pathlib.Path.exists', return_value=False):

            response = client.get("/api/thread/test-thread-123/logs")

            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "test-thread-123"
            assert data["logs"] == []
            assert data["total"] == 0


class TestFlowStartAPI:
    """Test cases for refactored flow start API endpoints."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with flow routes."""
        app = FastAPI()
        setup_exception_handlers(app)

        # Mock dependencies
        mock_engine = Mock()
        mock_app_manager = Mock()
        mock_templates = Mock()
        mock_config = Mock()

        init_dependencies(mock_engine, mock_app_manager, mock_templates, mock_config)

        app.include_router(create_flow_router(), prefix="/api")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        mock = Mock()
        mock.get_flow_by_name.return_value = {"flow_id": 1, "name": "test-flow"}
        mock.get_latest_flow_version.return_value = {"flow_version_id": 1, "version": "1.0.0"}
        mock.get_flow_version_by_version.return_value = {"flow_version_id": 2, "version": "2.0.0"}
        return mock

    @pytest.fixture
    def mock_control(self):
        """Mock workflow control."""
        mock = Mock()
        mock.start_workflow.return_value = "new-thread-456"
        return mock

    def test_start_flow_latest_version(self, client, mock_db_manager, mock_control):
        """Test starting flow with latest version."""
        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.post("/api/flows/test-flow/start/latest", json={"input_data": {"test": "data"}})

            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "new-thread-456"
            assert data["status"] == "started"
            assert "latest version" in data["message"]

    def test_start_flow_specific_version(self, client, mock_db_manager, mock_control):
        """Test starting flow with specific version."""
        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.post("/api/flows/test-flow/start/version/2.0.0", json={"input_data": {"test": "data"}})

            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "new-thread-456"
            assert data["status"] == "started"
            # The message should contain version info - check for either format
            assert "2.0.0" in data["message"] or "v2.0.0" in data["message"]

    def test_start_flow_not_found(self, client, mock_control):
        """Test starting non-existent flow."""
        mock_db_manager = Mock()
        mock_db_manager.get_flow_by_name.return_value = None

        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.post("/api/flows/non-existent-flow/start/latest", json={})

            assert response.status_code == 404
            assert "not found" in response.json()["error"].lower()

    def test_start_flow_invalid_version_format(self, client, mock_db_manager, mock_control):
        """Test starting flow with invalid version format."""
        # Mock the flow to exist but version parsing to fail
        mock_db_manager.get_flow_by_name.return_value = {"flow_id": 1, "name": "test-flow"}
        mock_db_manager.get_flow_version_by_version.return_value = None

        # Mock workflow control to raise an exception for invalid version format
        mock_control.start_workflow.side_effect = Exception("Invalid version format: invalid-version")

        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.post("/api/flows/test-flow/start/version/invalid-version", json={})

            # Should return 400 for invalid version format
            assert response.status_code == 400
            assert "Failed to start workflow" in response.json()["error"]

    def test_start_flow_version_not_found(self, client, mock_control):
        """Test starting flow with non-existent version."""
        mock_db_manager = Mock()
        mock_db_manager.get_flow_by_name.return_value = {"flow_id": 1, "name": "test-flow"}
        mock_db_manager.get_flow_version_by_version.return_value = None
        
        # Mock workflow control to raise an exception for version not found
        mock_control.start_workflow.side_effect = Exception("Version not found")

        with patch('workflow_engine.api.dependencies.get_database_manager', return_value=mock_db_manager), \
             patch('workflow_engine.api.dependencies.get_workflow_control', return_value=mock_control):

            response = client.post("/api/flows/test-flow/start/version/999.0.0", json={})

            assert response.status_code == 400
            assert "Failed to start workflow" in response.json()["error"]


class TestAPIValidation:
    """Test cases for API validation and error handling."""

    def test_thread_id_validation(self):
        """Test thread ID validation in various scenarios."""
        # This would test the validation logic for thread IDs
        # including format validation, existence checks, etc.
        pass

    def test_flow_id_version_parsing(self):
        """Test flow ID and version parsing logic."""
        from workflow_engine.api.flow_routes import create_flow_router
        
        # Test the internal parsing function
        # This would require extracting the parsing logic to a testable function
        pass

    def test_error_response_format(self):
        """Test that error responses follow consistent format."""
        # This would test that all error responses have consistent structure
        pass


if __name__ == "__main__":
    pytest.main([__file__])