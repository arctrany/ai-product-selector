"""Test cases for WorkflowControl refactoring."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from workflow_engine.sdk.control import WorkflowControl
from workflow_engine.storage.database import DatabaseManager
from workflow_engine.api.dependencies import init_dependencies
from workflow_engine.api.workflow_routes import create_workflow_router
from workflow_engine.api.app_routes import create_app_router
from workflow_engine.core.engine import WorkflowEngine
from workflow_engine.apps.manager import AppManager


class TestWorkflowControl:
    """Test WorkflowControl functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.workflow_control = WorkflowControl(db_manager=self.mock_db_manager)
    
    def test_pause_workflow_success(self):
        """Test successful workflow pause."""
        # Mock database operations
        self.mock_db_manager.create_signal.return_value = "signal_123"
        
        # Test pause workflow
        result = self.workflow_control.pause_workflow("thread_123", "node_456")
        
        # Verify
        assert result is True
        self.mock_db_manager.create_signal.assert_called_once_with(
            "thread_123", "pause_request", {"node_id": "node_456"}
        )
    
    def test_pause_workflow_failure(self):
        """Test workflow pause failure."""
        # Mock database failure
        self.mock_db_manager.create_signal.side_effect = Exception("DB Error")
        
        # Test pause workflow
        result = self.workflow_control.pause_workflow("thread_123")
        
        # Verify
        assert result is False
    
    def test_resume_workflow_success(self):
        """Test successful workflow resume."""
        # Mock database operations
        self.mock_db_manager.create_signal.return_value = "signal_124"
        
        # Test resume workflow
        updates = {"key": "value"}
        result = self.workflow_control.resume_workflow("thread_123", updates)
        
        # Verify
        assert result is True
        self.mock_db_manager.create_signal.assert_called_once_with(
            "thread_123", "resume_request", {"updates": updates}
        )
    
    def test_cancel_workflow_success(self):
        """Test successful workflow cancellation."""
        # Mock database operations
        self.mock_db_manager.create_signal.return_value = "signal_125"
        
        # Test cancel workflow
        result = self.workflow_control.cancel_workflow("thread_123", "User requested")
        
        # Verify
        assert result is True
        self.mock_db_manager.create_signal.assert_called_once_with(
            "thread_123", "cancel_request", {"reason": "User requested"}
        )
    
    def test_get_workflow_status_success(self):
        """Test successful workflow status retrieval."""
        # Mock database response
        expected_status = {"status": "running", "thread_id": "thread_123"}
        self.mock_db_manager.get_run.return_value = expected_status
        
        # Test get status
        result = self.workflow_control.get_workflow_status("thread_123")
        
        # Verify
        assert result == expected_status
        self.mock_db_manager.get_run.assert_called_once_with("thread_123")
    
    def test_get_workflow_status_not_found(self):
        """Test workflow status retrieval when not found."""
        # Mock database response
        self.mock_db_manager.get_run.return_value = None
        
        # Test get status
        result = self.workflow_control.get_workflow_status("thread_123")
        
        # Verify
        assert result is None
    
    def test_list_workflows_success(self):
        """Test successful workflow listing."""
        # Mock database response
        expected_runs = [
            {"thread_id": "thread_1", "status": "completed"},
            {"thread_id": "thread_2", "status": "running"}
        ]
        self.mock_db_manager.list_runs.return_value = expected_runs
        
        # Test list workflows
        result = self.workflow_control.list_workflows(limit=10)
        
        # Verify
        assert result == expected_runs
        self.mock_db_manager.list_runs.assert_called_once_with(limit=10)
    
    def test_list_workflows_empty(self):
        """Test workflow listing when empty."""
        # Mock database response
        self.mock_db_manager.list_runs.return_value = []
        
        # Test list workflows
        result = self.workflow_control.list_workflows()
        
        # Verify
        assert result == []
    
    @patch('workflow_engine.sdk.control.WorkflowEngine')
    def test_start_workflow_success(self, mock_engine_class):
        """Test successful workflow start."""
        # Mock engine
        mock_engine = Mock()
        mock_engine.start_workflow.return_value = "thread_123"
        mock_engine_class.return_value = mock_engine
        
        # Test start workflow
        result = self.workflow_control.start_workflow(
            flow_version_id=1,
            input_data={"key": "value"},
            thread_id="custom_thread"
        )
        
        # Verify
        assert result == "thread_123"
        mock_engine_class.assert_called_once_with(db_manager=self.mock_db_manager)
        mock_engine.start_workflow.assert_called_once_with(
            1, {"key": "value"}, "custom_thread"
        )
    
    def test_wait_for_completion_success(self):
        """Test successful workflow completion wait."""
        # Mock status progression
        status_sequence = [
            {"status": "running"},
            {"status": "running"},
            {"status": "completed"}
        ]
        self.mock_db_manager.get_run.side_effect = status_sequence
        
        # Test wait for completion
        result = self.workflow_control.wait_for_completion("thread_123", timeout_seconds=1)
        
        # Verify
        assert result is True
    
    def test_wait_for_completion_failure(self):
        """Test workflow completion wait with failure."""
        # Mock status progression
        status_sequence = [
            {"status": "running"},
            {"status": "failed"}
        ]
        self.mock_db_manager.get_run.side_effect = status_sequence
        
        # Test wait for completion
        result = self.workflow_control.wait_for_completion("thread_123", timeout_seconds=1)
        
        # Verify
        assert result is False


class TestWorkflowRoutesRefactor:
    """Test refactored workflow routes using WorkflowControl."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()
        
        # Create mocks
        self.mock_engine = Mock(spec=WorkflowEngine)
        self.mock_app_manager = Mock(spec=AppManager)
        self.mock_control = Mock(spec=WorkflowControl)
        
        # Initialize dependencies with mocks
        init_dependencies(
            engine=self.mock_engine,
            app_manager=self.mock_app_manager,
            templates=Mock(),
            config=Mock()
        )
        
        # Override workflow control dependency
        with patch('workflow_engine.api.dependencies._workflow_control', self.mock_control):
            # Add routes
            workflow_router = create_workflow_router()
            self.app.include_router(workflow_router)
        
        self.client = TestClient(self.app)
    
    def test_start_workflow_endpoint(self):
        """Test start workflow endpoint uses WorkflowControl."""
        # Mock control response
        self.mock_control.start_workflow.return_value = "thread_123"
        
        # Test request
        response = self.client.post("/runs/start", json={
            "flow_version_id": 1,
            "input_data": {"key": "value"}
        })
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "thread_123"
        assert data["status"] == "started"
        
        # Verify control was called
        self.mock_control.start_workflow.assert_called_once()
    
    def test_get_workflow_status_endpoint(self):
        """Test get workflow status endpoint uses WorkflowControl."""
        # Mock control response
        expected_status = {"status": "running", "thread_id": "thread_123"}
        self.mock_control.get_workflow_status.return_value = expected_status
        
        # Test request
        response = self.client.get("/runs/thread_123")
        
        # Verify response
        assert response.status_code == 200
        assert response.json() == expected_status
        
        # Verify control was called
        self.mock_control.get_workflow_status.assert_called_once_with("thread_123")
    
    def test_pause_workflow_endpoint(self):
        """Test pause workflow endpoint uses WorkflowControl."""
        # Mock control response
        self.mock_control.pause_workflow.return_value = True
        
        # Test request
        response = self.client.post("/runs/thread_123/pause")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "thread_123"
        assert data["status"] == "pause_requested"
        
        # Verify control was called
        self.mock_control.pause_workflow.assert_called_once_with("thread_123")
    
    def test_resume_workflow_endpoint(self):
        """Test resume workflow endpoint uses WorkflowControl."""
        # Mock control response
        self.mock_control.resume_workflow.return_value = True
        
        # Test request
        response = self.client.post("/runs/thread_123/resume", json={
            "updates": {"key": "new_value"}
        })
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "thread_123"
        assert data["status"] == "resumed"
        
        # Verify control was called
        self.mock_control.resume_workflow.assert_called_once_with(
            "thread_123", {"key": "new_value"}
        )
    
    def test_cancel_workflow_endpoint(self):
        """Test cancel workflow endpoint uses WorkflowControl."""
        # Mock control response
        self.mock_control.cancel_workflow.return_value = True
        
        # Test request
        response = self.client.delete("/runs/thread_123")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "thread_123"
        assert data["status"] == "cancelled"
        
        # Verify control was called
        self.mock_control.cancel_workflow.assert_called_once_with(
            "thread_123", "Cancelled via API"
        )
    
    def test_list_workflows_endpoint(self):
        """Test list workflows endpoint uses WorkflowControl."""
        # Mock control response
        expected_runs = [
            {"thread_id": "thread_1", "status": "completed"},
            {"thread_id": "thread_2", "status": "running"}
        ]
        self.mock_control.list_workflows.return_value = expected_runs
        
        # Test request
        response = self.client.get("/runs?limit=10")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == expected_runs
        assert data["total"] == 2
        assert data["limit"] == 10
        
        # Verify control was called
        self.mock_control.list_workflows.assert_called_once_with(10)

    def test_start_workflow_api_endpoint(self):
        """Test start workflow API endpoint uses WorkflowControl."""
        # Mock database and control responses
        flow_version = {"flow_version_id": 1, "version": "1.0.0"}
        flow = {"flow_id": "test_flow"}
        self.mock_db_manager.get_flow_by_name.return_value = flow
        self.mock_db_manager.get_latest_flow_version.return_value = flow_version
        self.mock_control.start_workflow.return_value = "thread_123"

        # Test request
        response = self.client.post("/api/flows/test_flow-1.0.0/start", json={
            "input_data": {"key": "value"}
        })

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "thread_123"
        assert data["status"] == "started"

        # Verify control was called
        self.mock_control.start_workflow.assert_called_once_with(
            flow_version_id=1,
            input_data={"key": "value"},
            thread_id=None
        )




class TestAppRoutesRefactor:
    """Test refactored app routes using WorkflowControl."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()

        # Create mocks
        self.mock_engine = Mock(spec=WorkflowEngine)
        self.mock_app_manager = Mock(spec=AppManager)
        self.mock_control = Mock(spec=WorkflowControl)
        self.mock_db_manager = Mock(spec=DatabaseManager)

        # Initialize dependencies with mocks
        init_dependencies(
            engine=self.mock_engine,
            app_manager=self.mock_app_manager,
            templates=Mock(),
            config=Mock()
        )

        # Override dependencies
        with patch('workflow_engine.api.dependencies._workflow_control', self.mock_control), \
             patch('workflow_engine.api.dependencies.get_database_manager', return_value=self.mock_db_manager):

            # Add routes
            app_router = create_app_router()
            self.app.include_router(app_router)

        self.client = TestClient(self.app)

    def test_start_workflow_placeholder(self):
        """Placeholder test - would need proper setup."""
        pass


class TestIntegration:
    """Integration tests for the refactored architecture."""

    def setup_method(self):
        """Setup integration test fixtures."""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.workflow_control = WorkflowControl(db_manager=self.mock_db_manager)

    def test_workflow_control_integration(self):
        """Test WorkflowControl integration with database operations."""
        # Test pause -> resume -> cancel workflow

        # 1. Pause workflow
        self.mock_db_manager.create_signal.return_value = "signal_1"
        result = self.workflow_control.pause_workflow("thread_123")
        assert result is True

        # 2. Resume workflow
        self.mock_db_manager.create_signal.return_value = "signal_2"
        result = self.workflow_control.resume_workflow("thread_123", {"updated": True})
        assert result is True

        # 3. Cancel workflow
        self.mock_db_manager.create_signal.return_value = "signal_3"
        result = self.workflow_control.cancel_workflow("thread_123", "Test complete")
        assert result is True

        # Verify all database calls
        assert self.mock_db_manager.create_signal.call_count == 3

    def test_error_handling_integration(self):
        """Test error handling across the refactored components."""
        # Test database failure scenarios

        # 1. Database connection failure
        self.mock_db_manager.create_signal.side_effect = Exception("Connection failed")
        result = self.workflow_control.pause_workflow("thread_123")
        assert result is False

        # 2. Invalid thread ID
        self.mock_db_manager.get_run.return_value = None
        result = self.workflow_control.get_workflow_status("invalid_thread")
        assert result is None

        # 3. Empty workflow list
        self.mock_db_manager.list_runs.return_value = []
        result = self.workflow_control.list_workflows()
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])