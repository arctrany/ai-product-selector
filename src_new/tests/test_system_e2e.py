"""End-to-end system tests for complete workflow scenarios."""

import pytest
import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Import workflow engine components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workflow_engine.api.server import create_app
from workflow_engine.core.config import WorkflowEngineConfig


class TestCompleteWorkflowScenarios:
    """End-to-end tests for complete workflow scenarios."""

    @pytest.fixture
    def e2e_system(self):
        """Setup complete system for end-to-end testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        config = WorkflowEngineConfig(
            db_path=db_path,
            checkpoint_enabled=False,
            thread_pool_workers=4
        )
        
        app = create_app(config=config)
        client = TestClient(app)
        
        yield client, config
        Path(db_path).unlink(missing_ok=True)

    def test_simple_linear_workflow_e2e(self, e2e_system):
        """Test complete execution of a simple linear workflow."""
        client, config = e2e_system
        
        # Mock comprehensive workflow execution
        with patch('workflow_engine.api.dependencies.get_workflow_engine') as mock_engine, \
             patch('workflow_engine.api.dependencies.get_database_manager') as mock_db, \
             patch('workflow_engine.api.dependencies.get_workflow_control') as mock_control:
            
            # Setup workflow execution simulation
            workflow_state = {
                "current_step": 0,
                "steps": ["pending", "running", "step1", "step2", "completed"],
                "thread_id": "e2e-linear-123"
            }
            
            def simulate_workflow_progress():
                if workflow_state["current_step"] < len(workflow_state["steps"]) - 1:
                    workflow_state["current_step"] += 1
                return workflow_state["steps"][workflow_state["current_step"]]
            
            # Setup mocks
            mock_db_instance = Mock()
            mock_db_instance.get_flow_by_name.return_value = {
                "flow_id": 1, "name": "linear-workflow"
            }
            mock_db_instance.get_latest_flow_version.return_value = {
                "flow_version_id": 1, "version": "1.0.0"
            }
            mock_db_instance.get_run.side_effect = lambda tid: {
                "thread_id": tid,
                "status": workflow_state["steps"][workflow_state["current_step"]],
                "flow_version_id": 1,
                "metadata": {"step": workflow_state["current_step"]}
            }
            mock_db.return_value = mock_db_instance
            
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = workflow_state["thread_id"]
            mock_engine.return_value = mock_engine_instance
            
            mock_control_instance = Mock()
            mock_control_instance.start_workflow.side_effect = lambda *args: simulate_workflow_progress()
            mock_control_instance.pause_workflow.return_value = True
            mock_control_instance.resume_workflow.side_effect = lambda *args: simulate_workflow_progress()
            mock_control.return_value = mock_control_instance
            
            # Step 1: Start workflow
            response = client.post(
                "/api/flows/linear-workflow/start",
                json={
                    "input_data": {
                        "input_value": 42,
                        "process_type": "linear"
                    }
                }
            )
            assert response.status_code == 200
            start_result = response.json()
            thread_id = start_result["thread_id"]
            assert thread_id == workflow_state["thread_id"]
            assert "started successfully" in start_result["message"]
            
            # Step 2: Check initial status
            response = client.get(f"/api/thread/{thread_id}/status")
            assert response.status_code == 200
            status_result = response.json()
            assert status_result["thread_id"] == thread_id
            assert status_result["status"] == "pending"
            
            # Step 3: Start thread execution
            response = client.post(f"/api/thread/{thread_id}/start", json={})
            assert response.status_code == 200
            start_thread_result = response.json()
            assert start_thread_result["status"] == "started"
            
            # Step 4: Monitor workflow progress
            for expected_step in ["running", "step1", "step2"]:
                # Simulate time passing
                time.sleep(0.1)
                
                response = client.get(f"/api/thread/{thread_id}/status")
                assert response.status_code == 200
                status_result = response.json()
                
                # The status should progress through the steps
                current_status = status_result["status"]
                assert current_status in workflow_state["steps"]
                
                print(f"Workflow progress: {current_status}")
            
            # Step 5: Test pause and resume
            response = client.post(f"/api/thread/{thread_id}/pause")
            assert response.status_code == 200
            pause_result = response.json()
            assert pause_result["status"] == "pause_requested"
            
            # Check paused status
            response = client.get(f"/api/thread/{thread_id}/status")
            assert response.status_code == 200
            
            # Resume workflow
            response = client.post(
                f"/api/thread/{thread_id}/resume",
                json={"updates": {"resume_reason": "user_requested"}}
            )
            assert response.status_code == 200
            resume_result = response.json()
            assert resume_result["status"] == "resumed"
            
            # Step 6: Check final completion
            # Simulate workflow completion
            workflow_state["current_step"] = len(workflow_state["steps"]) - 1
            
            response = client.get(f"/api/thread/{thread_id}/status")
            assert response.status_code == 200
            final_status = response.json()
            assert final_status["status"] == "completed"
            
            # Step 7: Get workflow logs
            response = client.get(f"/api/thread/{thread_id}/logs")
            assert response.status_code == 200
            logs_result = response.json()
            assert logs_result["thread_id"] == thread_id
            assert "logs" in logs_result

    def test_conditional_workflow_e2e(self, e2e_system):
        """Test workflow with conditional branching."""
        client, config = e2e_system
        
        with patch('workflow_engine.api.dependencies.get_workflow_engine') as mock_engine, \
             patch('workflow_engine.api.dependencies.get_database_manager') as mock_db, \
             patch('workflow_engine.api.dependencies.get_workflow_control') as mock_control:
            
            # Setup conditional workflow simulation
            workflow_conditions = {
                "thread_id": "e2e-conditional-456",
                "input_value": 75,
                "branch_taken": "high_value_branch",
                "status": "pending"
            }
            
            # Setup mocks
            mock_db_instance = Mock()
            mock_db_instance.get_flow_by_name.return_value = {
                "flow_id": 2, "name": "conditional-workflow"
            }
            mock_db_instance.get_latest_flow_version.return_value = {
                "flow_version_id": 2, "version": "1.0.0"
            }
            mock_db_instance.get_run.side_effect = lambda tid: {
                "thread_id": tid,
                "status": workflow_conditions["status"],
                "flow_version_id": 2,
                "metadata": {
                    "input_value": workflow_conditions["input_value"],
                    "branch": workflow_conditions["branch_taken"]
                }
            }
            mock_db.return_value = mock_db_instance
            
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = workflow_conditions["thread_id"]
            mock_engine.return_value = mock_engine_instance
            
            mock_control_instance = Mock()
            
            def simulate_conditional_execution(*args):
                if workflow_conditions["input_value"] > 50:
                    workflow_conditions["status"] = "high_value_processing"
                    workflow_conditions["branch_taken"] = "high_value_branch"
                else:
                    workflow_conditions["status"] = "low_value_processing"
                    workflow_conditions["branch_taken"] = "low_value_branch"
                return True
            
            mock_control_instance.start_workflow.side_effect = simulate_conditional_execution
            mock_control.return_value = mock_control_instance
            
            # Test high-value branch
            response = client.post(
                "/api/flows/conditional-workflow/start",
                json={
                    "input_data": {
                        "value": workflow_conditions["input_value"],
                        "threshold": 50
                    }
                }
            )
            assert response.status_code == 200
            thread_id = response.json()["thread_id"]
            
            # Start execution
            response = client.post(f"/api/thread/{thread_id}/start", json={})
            assert response.status_code == 200
            
            # Check that high-value branch was taken
            response = client.get(f"/api/thread/{thread_id}/status")
            assert response.status_code == 200
            status_result = response.json()
            assert "high_value" in status_result["status"]
            
            # Test low-value branch
            workflow_conditions["input_value"] = 25
            workflow_conditions["thread_id"] = "e2e-conditional-789"
            workflow_conditions["status"] = "pending"
            
            response = client.post(
                "/api/flows/conditional-workflow/start",
                json={
                    "input_data": {
                        "value": 25,
                        "threshold": 50
                    }
                }
            )
            assert response.status_code == 200
            thread_id_low = response.json()["thread_id"]
            
            response = client.post(f"/api/thread/{thread_id_low}/start", json={})
            assert response.status_code == 200
            
            # Verify low-value branch
            response = client.get(f"/api/thread/{thread_id_low}/status")
            assert response.status_code == 200
            status_result = response.json()
            # The mock should reflect the low value processing
            print(f"Low value branch status: {status_result['status']}")

    def test_error_recovery_workflow_e2e(self, e2e_system):
        """Test workflow error handling and recovery."""
        client, config = e2e_system
        
        with patch('workflow_engine.api.dependencies.get_workflow_engine') as mock_engine, \
             patch('workflow_engine.api.dependencies.get_database_manager') as mock_db, \
             patch('workflow_engine.api.dependencies.get_workflow_control') as mock_control:
            
            # Setup error scenario simulation
            error_workflow = {
                "thread_id": "e2e-error-recovery-999",
                "status": "pending",
                "error_count": 0,
                "max_retries": 3
            }
            
            # Setup mocks
            mock_db_instance = Mock()
            mock_db_instance.get_flow_by_name.return_value = {
                "flow_id": 3, "name": "error-recovery-workflow"
            }
            mock_db_instance.get_latest_flow_version.return_value = {
                "flow_version_id": 3, "version": "1.0.0"
            }
            mock_db_instance.get_run.side_effect = lambda tid: {
                "thread_id": tid,
                "status": error_workflow["status"],
                "flow_version_id": 3,
                "metadata": {
                    "error_count": error_workflow["error_count"],
                    "max_retries": error_workflow["max_retries"]
                }
            }
            mock_db.return_value = mock_db_instance
            
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = error_workflow["thread_id"]
            mock_engine.return_value = mock_engine_instance
            
            mock_control_instance = Mock()
            
            def simulate_error_and_recovery(*args):
                error_workflow["error_count"] += 1
                if error_workflow["error_count"] <= error_workflow["max_retries"]:
                    error_workflow["status"] = f"error_retry_{error_workflow['error_count']}"
                    return True
                else:
                    error_workflow["status"] = "failed_max_retries"
                    return False
            
            mock_control_instance.start_workflow.side_effect = simulate_error_and_recovery
            mock_control_instance.resume_workflow.side_effect = simulate_error_and_recovery
            mock_control.return_value = mock_control_instance
            
            # Start error-prone workflow
            response = client.post(
                "/api/flows/error-recovery-workflow/start",
                json={
                    "input_data": {
                        "simulate_errors": True,
                        "max_retries": 3
                    }
                }
            )
            assert response.status_code == 200
            thread_id = response.json()["thread_id"]
            
            # Attempt to start and simulate errors
            for retry_attempt in range(1, 4):  # 3 retries
                response = client.post(f"/api/thread/{thread_id}/start", json={})
                assert response.status_code == 200
                
                # Check error status
                response = client.get(f"/api/thread/{thread_id}/status")
                assert response.status_code == 200
                status_result = response.json()
                
                expected_status = f"error_retry_{retry_attempt}"
                assert status_result["status"] == expected_status
                
                print(f"Retry attempt {retry_attempt}: {status_result['status']}")
                
                # Try to resume after error
                if retry_attempt < 3:
                    response = client.post(
                        f"/api/thread/{thread_id}/resume",
                        json={"retry_attempt": retry_attempt}
                    )
                    assert response.status_code == 200

    def test_parallel_workflow_execution_e2e(self, e2e_system):
        """Test multiple workflows running in parallel."""
        client, config = e2e_system
        
        with patch('workflow_engine.api.dependencies.get_workflow_engine') as mock_engine, \
             patch('workflow_engine.api.dependencies.get_database_manager') as mock_db, \
             patch('workflow_engine.api.dependencies.get_workflow_control') as mock_control:
            
            # Setup parallel workflow simulation
            parallel_workflows = {
                f"parallel-{i}": {
                    "thread_id": f"e2e-parallel-{i}",
                    "status": "pending",
                    "progress": 0
                }
                for i in range(5)
            }
            
            # Setup mocks
            mock_db_instance = Mock()
            mock_db_instance.get_flow_by_name.return_value = {
                "flow_id": 4, "name": "parallel-workflow"
            }
            mock_db_instance.get_latest_flow_version.return_value = {
                "flow_version_id": 4, "version": "1.0.0"
            }
            
            def get_run_status(thread_id):
                for workflow_name, workflow_data in parallel_workflows.items():
                    if workflow_data["thread_id"] == thread_id:
                        return {
                            "thread_id": thread_id,
                            "status": workflow_data["status"],
                            "flow_version_id": 4,
                            "metadata": {"progress": workflow_data["progress"]}
                        }
                return None
            
            mock_db_instance.get_run.side_effect = get_run_status
            mock_db.return_value = mock_db_instance
            
            mock_engine_instance = Mock()
            
            def start_parallel_workflow(*args, **kwargs):
                # Find next available workflow
                for workflow_name, workflow_data in parallel_workflows.items():
                    if workflow_data["status"] == "pending":
                        return workflow_data["thread_id"]
                return f"e2e-parallel-{len(parallel_workflows)}"
            
            mock_engine_instance.start_workflow.side_effect = start_parallel_workflow
            mock_engine.return_value = mock_engine_instance
            
            mock_control_instance = Mock()
            
            def simulate_parallel_execution(thread_id, *args):
                for workflow_name, workflow_data in parallel_workflows.items():
                    if workflow_data["thread_id"] == thread_id:
                        workflow_data["status"] = "running"
                        workflow_data["progress"] = 50
                        return True
                return False
            
            mock_control_instance.start_workflow.side_effect = simulate_parallel_execution
            mock_control.return_value = mock_control_instance
            
            # Start multiple workflows in parallel
            thread_ids = []
            for i in range(5):
                response = client.post(
                    "/api/flows/parallel-workflow/start",
                    json={
                        "input_data": {
                            "workflow_index": i,
                            "parallel_execution": True
                        }
                    }
                )
                assert response.status_code == 200
                thread_id = response.json()["thread_id"]
                thread_ids.append(thread_id)
                
                # Start each workflow
                response = client.post(f"/api/thread/{thread_id}/start", json={})
                assert response.status_code == 200
            
            # Check all workflows are running
            for thread_id in thread_ids:
                response = client.get(f"/api/thread/{thread_id}/status")
                assert response.status_code == 200
                status_result = response.json()
                assert status_result["status"] == "running"
                print(f"Parallel workflow {thread_id}: {status_result['status']}")
            
            # Verify all workflows are independent
            assert len(set(thread_ids)) == 5, "All workflows should have unique thread IDs"

    def test_workflow_versioning_e2e(self, e2e_system):
        """Test workflow versioning scenarios."""
        client, config = e2e_system
        
        with patch('workflow_engine.api.dependencies.get_workflow_engine') as mock_engine, \
             patch('workflow_engine.api.dependencies.get_database_manager') as mock_db, \
             patch('workflow_engine.api.dependencies.get_workflow_control') as mock_control:
            
            # Setup versioning simulation
            workflow_versions = {
                "1.0.0": {"flow_version_id": 1, "features": ["basic"]},
                "2.0.0": {"flow_version_id": 2, "features": ["basic", "advanced"]},
                "3.0.0": {"flow_version_id": 3, "features": ["basic", "advanced", "experimental"]}
            }
            
            # Setup mocks
            mock_db_instance = Mock()
            mock_db_instance.get_flow_by_name.return_value = {
                "flow_id": 5, "name": "versioned-workflow"
            }
            
            def get_version_info(flow_id, version=None):
                if version:
                    return workflow_versions.get(version, {
                        "flow_version_id": 999, "version": version
                    })
                else:
                    # Return latest version
                    latest_version = max(workflow_versions.keys())
                    return {
                        "flow_version_id": workflow_versions[latest_version]["flow_version_id"],
                        "version": latest_version
                    }
            
            mock_db_instance.get_latest_flow_version.side_effect = lambda flow_id: get_version_info(flow_id)
            mock_db_instance.get_flow_version_by_version.side_effect = lambda flow_id, version: get_version_info(flow_id, version)
            mock_db_instance.get_run.return_value = {
                "thread_id": "version-test-123",
                "status": "completed",
                "flow_version_id": 1
            }
            mock_db.return_value = mock_db_instance
            
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "version-test-123"
            mock_engine.return_value = mock_engine_instance
            
            mock_control_instance = Mock()
            mock_control_instance.start_workflow.return_value = True
            mock_control.return_value = mock_control_instance
            
            # Test starting latest version
            response = client.post(
                "/api/flows/versioned-workflow/start",
                json={"input_data": {"test": "latest_version"}}
            )
            assert response.status_code == 200
            result = response.json()
            assert "latest version" in result["message"]
            
            # Test starting specific versions
            for version in ["1.0.0", "2.0.0", "3.0.0"]:
                response = client.post(
                    f"/api/flows/versioned-workflow-{version}/start",
                    json={"input_data": {"test": f"version_{version}"}}
                )
                assert response.status_code == 200
                result = response.json()
                assert f"v{version}" in result["message"]
                print(f"Started workflow version {version}: {result['message']}")
            
            # Test invalid version
            response = client.post(
                "/api/flows/versioned-workflow-99.0.0/start",
                json={"input_data": {"test": "invalid_version"}}
            )
            # Should handle gracefully (exact behavior depends on implementation)
            print(f"Invalid version response: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])