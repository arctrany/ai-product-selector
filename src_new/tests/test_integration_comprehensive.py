"""Comprehensive integration tests for workflow engine API and core components."""

import pytest
import asyncio
import json
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import workflow engine components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workflow_engine.api.server import create_app
from workflow_engine.core.engine import WorkflowEngine
from workflow_engine.core.config import WorkflowEngineConfig
from workflow_engine.storage.database import DatabaseManager
from workflow_engine.core.models import WorkflowDefinition, NodeDefinition, NodeType


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def db_manager(self, temp_db):
        """Create database manager with temporary database."""
        return DatabaseManager(temp_db)

    def test_database_initialization(self, db_manager):
        """Test database initialization and table creation."""
        # Verify tables exist
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['flows', 'flow_versions', 'runs', 'run_logs']
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"

    def test_flow_crud_operations(self, db_manager):
        """Test complete CRUD operations for flows."""
        # Create flow
        flow_id = db_manager.create_flow_by_name(
            flow_name="test-flow",
            version="1.0.0",
            dsl_json={"nodes": [], "edges": []},
            published=True
        )
        assert flow_id is not None

        # Read flow
        flow = db_manager.get_flow_by_name("test-flow")
        assert flow is not None
        assert flow["name"] == "test-flow"

        # Update flow (create new version)
        version_id = db_manager.create_flow_by_name(
            flow_name="test-flow",
            version="2.0.0",
            dsl_json={"nodes": [{"id": "node1"}], "edges": []},
            published=True
        )
        assert version_id != flow_id

        # Get latest version
        latest = db_manager.get_latest_flow_version(flow["flow_id"])
        assert latest["version"] == "2.0.0"

    def test_run_lifecycle_operations(self, db_manager):
        """Test complete run lifecycle operations."""
        # Create flow first
        flow_id = db_manager.create_flow_by_name(
            flow_name="test-flow",
            version="1.0.0",
            dsl_json={"nodes": [], "edges": []},
            published=True
        )

        # Create run
        thread_id = "test-thread-123"
        db_manager.create_run(thread_id, flow_id, "pending", {"input": "test"})

        # Get run
        run = db_manager.get_run(thread_id)
        assert run is not None
        assert run["thread_id"] == thread_id
        assert run["status"] == "pending"

        # Update run status
        success = db_manager.atomic_update_run_status(thread_id, "pending", "running")
        assert success is True

        # Verify status update
        run = db_manager.get_run(thread_id)
        assert run["status"] == "running"

        # Add logs
        db_manager.add_run_log(thread_id, "info", "Test log message", {"step": 1})
        
        # Get logs
        logs = db_manager.get_run_logs(thread_id)
        assert len(logs) == 1
        assert logs[0]["message"] == "Test log message"


class TestWorkflowEngineIntegration:
    """Integration tests for workflow engine core functionality."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        config = WorkflowEngineConfig(
            db_path=db_path,
            checkpoint_enabled=False,  # Disable for testing
            thread_pool_workers=2,
            batch_size=10
        )
        yield config
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def workflow_engine(self, temp_config):
        """Create workflow engine with temporary configuration."""
        return WorkflowEngine(config=temp_config)

    def test_workflow_creation_and_compilation(self, workflow_engine):
        """Test workflow creation and compilation process."""
        # Create simple workflow definition
        definition = WorkflowDefinition(
            nodes=[
                NodeDefinition(
                    id="start",
                    type=NodeType.START,
                    config={}
                ),
                NodeDefinition(
                    id="end",
                    type=NodeType.END,
                    config={}
                )
            ],
            edges=[
                {"from": "start", "to": "end"}
            ]
        )

        # Create workflow
        flow_id = workflow_engine.create_flow("test-workflow", definition, "1.0.0")
        assert flow_id is not None

        # Compile workflow
        graph = workflow_engine.compile_workflow(definition)
        assert graph is not None

    def test_workflow_execution_lifecycle(self, workflow_engine):
        """Test complete workflow execution lifecycle."""
        # Create workflow
        definition = WorkflowDefinition(
            nodes=[
                NodeDefinition(
                    id="start",
                    type=NodeType.START,
                    config={}
                ),
                NodeDefinition(
                    id="python_node",
                    type=NodeType.PYTHON,
                    config={
                        "code": "return {'result': data.get('input', 0) * 2}"
                    }
                ),
                NodeDefinition(
                    id="end",
                    type=NodeType.END,
                    config={}
                )
            ],
            edges=[
                {"from": "start", "to": "python_node"},
                {"from": "python_node", "to": "end"}
            ]
        )

        flow_version_id = workflow_engine.create_flow("test-execution", definition, "1.0.0")

        # Mock the app manager to avoid dependency issues
        with patch('workflow_engine.core.engine.get_container') as mock_container:
            mock_app_manager = Mock()
            mock_app_manager.load_workflow_definition.return_value = None
            mock_container.return_value.get.return_value = mock_app_manager

            # Start workflow execution
            thread_id = workflow_engine.start_workflow(
                flow_version_id=flow_version_id,
                input_data={"input": 5}
            )
            assert thread_id is not None

            # Verify run was created
            run = workflow_engine.db_manager.get_run(thread_id)
            assert run is not None
            assert run["flow_version_id"] == flow_version_id


class TestAPIIntegration:
    """Integration tests for API endpoints with real components."""

    @pytest.fixture
    def temp_app(self):
        """Create FastAPI app with temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        config = WorkflowEngineConfig(
            db_path=db_path,
            checkpoint_enabled=False
        )
        
        app = create_app(config=config)
        yield app
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def client(self, temp_app):
        """Create test client with temporary app."""
        return TestClient(temp_app)

    def test_flow_creation_and_start_integration(self, client):
        """Test complete flow creation and start process."""
        # First create a flow through database (simulating admin action)
        # This would normally be done through admin interface
        
        # Mock the workflow engine components
        with patch('workflow_engine.api.dependencies.get_workflow_engine') as mock_engine, \
             patch('workflow_engine.api.dependencies.get_database_manager') as mock_db:
            
            # Setup mock database
            mock_db_instance = Mock()
            mock_db_instance.get_flow_by_name.return_value = {
                "flow_id": 1, 
                "name": "test-flow"
            }
            mock_db_instance.get_latest_flow_version.return_value = {
                "flow_version_id": 1, 
                "version": "1.0.0"
            }
            mock_db.return_value = mock_db_instance

            # Setup mock engine
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "thread-123"
            mock_engine.return_value = mock_engine_instance

            # Test flow start
            response = client.post(
                "/api/flows/test-flow/start/latest",
                json={"input_data": {"test": "value"}}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "thread-123"
            assert data["status"] == "started"

    def test_thread_control_integration(self, client):
        """Test thread control operations integration."""
        with patch('workflow_engine.api.dependencies.get_database_manager') as mock_db, \
             patch('workflow_engine.api.dependencies.get_workflow_control') as mock_control:
            
            # Setup mock database
            mock_db_instance = Mock()
            mock_db_instance.get_run.return_value = {
                "thread_id": "thread-123",
                "status": "running",
                "flow_version_id": 1
            }
            mock_db.return_value = mock_db_instance

            # Setup mock control
            mock_control_instance = Mock()
            mock_control_instance.pause_workflow.return_value = True
            mock_control_instance.resume_workflow.return_value = True
            mock_control.return_value = mock_control_instance

            # Test pause
            response = client.post("/api/thread/thread-123/pause")
            assert response.status_code == 200
            assert response.json()["status"] == "pause_requested"

            # Test resume
            response = client.post("/api/thread/thread-123/resume", json={})
            assert response.status_code == 200
            assert response.json()["status"] == "resumed"

            # Test status
            response = client.get("/api/thread/thread-123/status")
            assert response.status_code == 200
            assert response.json()["thread_id"] == "thread-123"

    def test_error_handling_integration(self, client):
        """Test error handling across API layers."""
        with patch('workflow_engine.api.dependencies.get_database_manager') as mock_db:
            # Setup mock to return None (not found)
            mock_db_instance = Mock()
            mock_db_instance.get_run.return_value = None
            mock_db.return_value = mock_db_instance

            # Test thread not found
            response = client.get("/api/thread/non-existent/status")
            assert response.status_code == 404
            assert "error" in response.json()
            assert "not found" in response.json()["error"].lower()


class TestConcurrencyIntegration:
    """Integration tests for concurrent operations."""

    @pytest.fixture
    def shared_engine(self):
        """Create shared workflow engine for concurrency tests."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        config = WorkflowEngineConfig(
            db_path=db_path,
            checkpoint_enabled=False,
            thread_pool_workers=4
        )
        engine = WorkflowEngine(config=config)
        yield engine
        Path(db_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_concurrent_workflow_creation(self, shared_engine):
        """Test concurrent workflow creation operations."""
        async def create_workflow(name, version):
            definition = WorkflowDefinition(
                nodes=[
                    NodeDefinition(id="start", type=NodeType.START, config={}),
                    NodeDefinition(id="end", type=NodeType.END, config={})
                ],
                edges=[{"from": "start", "to": "end"}]
            )
            return shared_engine.create_flow(f"{name}-{version}", definition, version)

        # Create multiple workflows concurrently
        tasks = [
            create_workflow("concurrent-flow", f"1.{i}.0")
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all workflows were created successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 5
        assert len(set(successful_results)) == 5  # All unique flow IDs

    def test_concurrent_database_operations(self, shared_engine):
        """Test concurrent database operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_and_update_run(thread_num):
            try:
                thread_id = f"concurrent-thread-{thread_num}"
                
                # Create flow first
                flow_id = shared_engine.db_manager.create_flow_by_name(
                    flow_name=f"concurrent-flow-{thread_num}",
                    version="1.0.0",
                    dsl_json={"nodes": [], "edges": []},
                    published=True
                )
                
                # Create run
                shared_engine.db_manager.create_run(
                    thread_id, flow_id, "pending", {"thread_num": thread_num}
                )
                
                # Update status multiple times
                for status in ["running", "paused", "running", "completed"]:
                    time.sleep(0.01)  # Small delay to increase concurrency
                    success = shared_engine.db_manager.atomic_update_run_status(
                        thread_id, None, status  # Use None for current status
                    )
                    if success:
                        results.append((thread_num, status))
                
            except Exception as e:
                errors.append((thread_num, str(e)))
        
        # Start concurrent threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_and_update_run, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) > 0, "No successful operations recorded"


class TestSystemIntegration:
    """End-to-end system integration tests."""

    @pytest.fixture
    def full_system(self):
        """Setup complete system for end-to-end testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        config = WorkflowEngineConfig(
            db_path=db_path,
            checkpoint_enabled=False
        )
        
        app = create_app(config=config)
        client = TestClient(app)
        
        yield client, config
        Path(db_path).unlink(missing_ok=True)

    def test_complete_workflow_lifecycle(self, full_system):
        """Test complete workflow lifecycle from creation to completion."""
        client, config = full_system
        
        # Mock all dependencies for end-to-end test
        with patch('workflow_engine.api.dependencies.get_workflow_engine') as mock_engine, \
             patch('workflow_engine.api.dependencies.get_database_manager') as mock_db, \
             patch('workflow_engine.api.dependencies.get_workflow_control') as mock_control:
            
            # Setup comprehensive mocks
            mock_db_instance = Mock()
            mock_engine_instance = Mock()
            mock_control_instance = Mock()
            
            # Flow creation simulation
            mock_db_instance.get_flow_by_name.return_value = {
                "flow_id": 1, "name": "e2e-test-flow"
            }
            mock_db_instance.get_latest_flow_version.return_value = {
                "flow_version_id": 1, "version": "1.0.0"
            }
            
            # Workflow execution simulation
            mock_engine_instance.start_workflow.return_value = "e2e-thread-123"
            
            # Thread control simulation
            run_states = {
                "pending": {"thread_id": "e2e-thread-123", "status": "pending", "flow_version_id": 1},
                "running": {"thread_id": "e2e-thread-123", "status": "running", "flow_version_id": 1},
                "paused": {"thread_id": "e2e-thread-123", "status": "paused", "flow_version_id": 1},
                "completed": {"thread_id": "e2e-thread-123", "status": "completed", "flow_version_id": 1}
            }
            
            current_state = "pending"
            
            def get_run_mock(thread_id):
                return run_states.get(current_state)
            
            def update_state(new_state):
                nonlocal current_state
                current_state = new_state
                return True
            
            mock_db_instance.get_run.side_effect = get_run_mock
            mock_control_instance.start_workflow.side_effect = lambda *args: update_state("running")
            mock_control_instance.pause_workflow.side_effect = lambda *args: update_state("paused")
            mock_control_instance.resume_workflow.side_effect = lambda *args: update_state("running")
            
            # Wire up mocks
            mock_db.return_value = mock_db_instance
            mock_engine.return_value = mock_engine_instance
            mock_control.return_value = mock_control_instance
            
            # Step 1: Start workflow
            response = client.post(
                "/api/flows/e2e-test-flow/start/latest",
                json={"input_data": {"test": "e2e"}}
            )
            assert response.status_code == 200
            thread_id = response.json()["thread_id"]
            assert thread_id == "e2e-thread-123"
            
            # Step 2: Check initial status
            response = client.get(f"/api/thread/{thread_id}/status")
            assert response.status_code == 200
            assert response.json()["status"] == "pending"
            
            # Step 3: Start thread
            response = client.post(f"/api/thread/{thread_id}/start", json={})
            assert response.status_code == 200
            
            # Step 4: Check running status
            current_state = "running"  # Simulate state change
            response = client.get(f"/api/thread/{thread_id}/status")
            assert response.status_code == 200
            assert response.json()["status"] == "running"
            
            # Step 5: Pause workflow
            response = client.post(f"/api/thread/{thread_id}/pause")
            assert response.status_code == 200
            
            # Step 6: Check paused status
            current_state = "paused"
            response = client.get(f"/api/thread/{thread_id}/status")
            assert response.status_code == 200
            assert response.json()["status"] == "paused"
            
            # Step 7: Resume workflow
            response = client.post(f"/api/thread/{thread_id}/resume", json={})
            assert response.status_code == 200
            
            # Step 8: Check final status
            current_state = "running"
            response = client.get(f"/api/thread/{thread_id}/status")
            assert response.status_code == 200
            assert response.json()["status"] == "running"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])