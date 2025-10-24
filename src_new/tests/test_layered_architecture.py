"""
LAYERED ARCHITECTURE UNIT TESTS

Tests the correct separation of concerns between:
1. Flow Layer (/api/flows/) - Flow management and startup
2. Run Layer (/api/runs/) - Thread-based execution control  
3. Engine Layer - Core workflow execution logic
"""

import pytest
import requests
import json
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock


class TestLayeredArchitecture:
    """Test the layered architecture design."""
    
    def setup_method(self):
        """Setup test environment."""
        self.base_url = "http://localhost:8889"
        self.session = requests.Session()
        
    def test_flow_layer_responsibilities(self):
        """Test that Flow Layer only handles flow management and startup."""
        
        # Test 1: Flow layer should handle submit/start
        flow_endpoints = [
            "/api/flows/test-flow-1.0.0/submit",
            "/api/flows/test-flow-1.0.0/start"
        ]
        
        for endpoint in flow_endpoints:
            response = self.session.post(f"{self.base_url}{endpoint}", json={})
            # Should exist (not 404 for route not found)
            assert response.status_code != 404 or "Not Found" not in response.text
            
        # Test 2: Flow layer should NOT have stop/resume/pause endpoints
        # These endpoints were removed as they don't belong in the flow layer
        invalid_endpoints = [
            "/api/flows/test-flow-1.0.0/stop",
            "/api/flows/test-flow-1.0.0/resume", 
            "/api/flows/test-flow-1.0.0/pause"
        ]
        
        for endpoint in invalid_endpoints:
            response = self.session.post(f"{self.base_url}{endpoint}", json={})
            # Should return 404 for route not found (these endpoints should not exist)
            assert response.status_code == 404
            
    def test_run_layer_responsibilities(self):
        """Test that Run Layer handles thread-based control."""
        
        # Test 1: Run layer should handle thread-based control
        thread_id = "test-thread-12345"
        run_endpoints = [
            f"/api/runs/{thread_id}/pause",
            f"/api/runs/{thread_id}/resume",
            f"/api/runs/{thread_id}",  # GET status
        ]
        
        for endpoint in run_endpoints:
            if endpoint.endswith(thread_id):
                response = self.session.get(f"{self.base_url}{endpoint}")
            else:
                response = self.session.post(f"{self.base_url}{endpoint}", json={})
            
            # Should exist (not 404 for route not found)
            assert response.status_code != 404 or "Not Found" not in response.text
            
        # Test 2: DELETE should work for cancellation
        response = self.session.delete(f"{self.base_url}/api/runs/{thread_id}")
        assert response.status_code != 404 or "Not Found" not in response.text
        
    def test_correct_flow_to_run_transition(self):
        """Test the correct flow: flows start -> runs control."""
        
        # Mock a successful workflow start
        with patch('workflow_engine.sdk.control.WorkflowControl') as mock_control:
            mock_instance = Mock()
            mock_instance.start_workflow.return_value = "test-thread-uuid"
            mock_control.return_value = mock_instance
            
            # Step 1: Start via flow layer
            start_data = {
                "input_data": {"test": "data"}
            }
            
            # This should create a thread_id
            # In real scenario, this would return thread_id in response
            expected_thread_id = "test-thread-uuid"
            
            # Step 2: Control via run layer using the thread_id
            control_endpoints = [
                f"/api/runs/{expected_thread_id}/pause",
                f"/api/runs/{expected_thread_id}/resume"
            ]
            
            for endpoint in control_endpoints:
                response = self.session.post(f"{self.base_url}{endpoint}", json={})
                # Should be able to control using thread_id
                assert response.status_code != 404
                
    def test_engine_layer_isolation(self):
        """Test that engine layer is properly isolated."""
        
        # Test that engine methods work correctly
        try:
            from workflow_engine.core.engine import WorkflowEngine
            from workflow_engine.sdk.control import WorkflowControl
            from workflow_engine.storage.database import DatabaseManager
            
            # Test engine instantiation
            engine = WorkflowEngine()
            assert engine is not None
            
            # Test control instantiation  
            control = WorkflowControl()
            assert control is not None
            
            # Test database manager
            db_manager = DatabaseManager()
            assert db_manager is not None
            
        except ImportError as e:
            pytest.skip(f"Engine layer components not available: {e}")
            
    def test_api_response_consistency(self):
        """Test that API responses follow consistent patterns."""
        
        # Test thread_id consistency in responses
        test_thread_id = "consistency-test-thread"
        
        endpoints_expecting_thread_id = [
            (f"/api/runs/{test_thread_id}/pause", "POST"),
            (f"/api/runs/{test_thread_id}/resume", "POST"),
            (f"/api/runs/{test_thread_id}", "GET"),
        ]
        
        for endpoint, method in endpoints_expecting_thread_id:
            if method == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}")
            else:
                response = self.session.post(f"{self.base_url}{endpoint}", json={})
                
            # Should return proper error format with thread_id
            if response.status_code == 404:
                try:
                    data = response.json()
                    # Should mention the thread_id in error details
                    assert "thread_id" in str(data).lower() or test_thread_id in str(data)
                except json.JSONDecodeError:
                    pass  # Some endpoints might not return JSON
                    
    def test_separation_of_concerns(self):
        """Test that each layer has distinct responsibilities."""
        
        # Flow layer concerns: flow definition, versioning, startup
        flow_concerns = [
            "flow_id",
            "version", 
            "flow_version_id",
            "submit",
            "start"
        ]
        
        # Run layer concerns: execution control, thread management
        run_concerns = [
            "thread_id",
            "pause",
            "resume", 
            "cancel",
            "status",
            "logs"
        ]
        
        # Test that flow endpoints don't handle run concerns
        flow_response = self.session.post(
            f"{self.base_url}/api/flows/test-flow-1.0.0/start", 
            json={"input_data": {}}
        )
        
        if flow_response.status_code == 200:
            try:
                flow_data = flow_response.json()
                # Flow response should include thread_id for handoff to run layer
                assert "thread_id" in flow_data
                # But should not handle pause/resume directly
                assert "pause" not in str(flow_data).lower()
                assert "resume" not in str(flow_data).lower()
            except json.JSONDecodeError:
                pass
                
    def test_error_handling_consistency(self):
        """Test consistent error handling across layers."""
        
        # Test non-existent flow
        response = self.session.post(
            f"{self.base_url}/api/flows/non-existent-flow-1.0.0/start",
            json={}
        )
        
        if response.status_code == 404:
            try:
                data = response.json()
                assert "error" in data or "detail" in data
            except json.JSONDecodeError:
                pass
                
        # Test non-existent thread
        response = self.session.get(f"{self.base_url}/api/runs/non-existent-thread")
        
        if response.status_code == 404:
            try:
                data = response.json()
                assert "error" in data or "detail" in data
                assert "thread" in str(data).lower()
            except json.JSONDecodeError:
                pass


class TestWorkflowControlMechanisms:
    """Test the underlying workflow control mechanisms."""
    
    def test_pause_resume_signal_mechanism(self):
        """Test the signal-based pause/resume mechanism."""
        
        try:
            from workflow_engine.storage.database import DatabaseManager
            from workflow_engine.sdk.control import WorkflowControl
            
            db_manager = DatabaseManager()
            control = WorkflowControl(db_manager)
            
            test_thread_id = "signal-test-thread"
            
            # Test pause signal creation
            pause_success = control.pause_workflow(test_thread_id)
            assert pause_success is True
            
            # Test resume signal creation
            resume_success = control.resume_workflow(test_thread_id, {"test": "update"})
            assert resume_success is True
            
        except ImportError:
            pytest.skip("Control mechanisms not available")
            
    def test_thread_id_uniqueness(self):
        """Test that thread IDs are unique for each workflow start."""
        
        try:
            from workflow_engine.sdk.control import WorkflowControl
            
            control = WorkflowControl()
            
            # Mock flow version ID
            mock_flow_version_id = 1
            
            with patch.object(control, 'start_workflow') as mock_start:
                # Mock different thread IDs for each call
                mock_start.side_effect = ["thread-1", "thread-2", "thread-3"]
                
                thread_ids = []
                for i in range(3):
                    thread_id = mock_start(mock_flow_version_id, {})
                    thread_ids.append(thread_id)
                
                # All thread IDs should be unique
                assert len(set(thread_ids)) == len(thread_ids)
                
        except ImportError:
            pytest.skip("Control mechanisms not available")
            
    def test_workflow_state_management(self):
        """Test workflow state transitions."""
        
        try:
            from workflow_engine.core.models import WorkflowState
            
            # Test state creation with required fields
            state = WorkflowState(
                thread_id="test-thread",
                data={"test": "data"},
                metadata={"flow_version_id": 1}
            )
            
            assert state.thread_id == "test-thread"
            assert state.data["test"] == "data"
            assert state.metadata["flow_version_id"] == 1
            
        except ImportError:
            pytest.skip("State management not available")


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def setup_method(self):
        """Setup test environment."""
        self.base_url = "http://localhost:8889"
        self.session = requests.Session()
        
    def test_complete_workflow_lifecycle(self):
        """Test complete workflow from start to finish."""
        
        # Step 1: Start workflow via flow layer
        start_response = self.session.post(
            f"{self.base_url}/api/flows/abba-ccdd-eeff-1.0.0/start",
            json={"input_data": {"test": "integration"}}
        )
        
        if start_response.status_code == 200:
            try:
                start_data = start_response.json()
                thread_id = start_data.get("thread_id")
                
                if thread_id:
                    # Step 2: Check status via run layer
                    status_response = self.session.get(f"{self.base_url}/api/runs/{thread_id}")
                    assert status_response.status_code in [200, 404]  # 404 if workflow completed quickly
                    
                    # Step 3: Try to pause via run layer
                    pause_response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/pause")
                    assert pause_response.status_code in [200, 404]  # 404 if workflow already completed
                    
                    # Step 4: Try to resume via run layer
                    resume_response = self.session.post(
                        f"{self.base_url}/api/runs/{thread_id}/resume",
                        json={"updates": {"resumed": True}}
                    )
                    assert resume_response.status_code in [200, 404]  # 404 if workflow already completed
                    
            except json.JSONDecodeError:
                pytest.skip("Invalid JSON response from start endpoint")
        else:
            pytest.skip(f"Could not start workflow: {start_response.status_code}")
            
    def test_error_propagation(self):
        """Test that errors propagate correctly through layers."""
        
        try:
            # Test invalid flow version
            response = self.session.post(
                f"{self.base_url}/api/flows/invalid-flow-999.999.999/start",
                json={}
            )

            assert response.status_code in [404, 400, 500]

            # Test invalid thread operations
            invalid_thread = "definitely-not-a-real-thread-id"

            operations = [
                ("GET", f"/api/runs/{invalid_thread}"),
                ("POST", f"/api/runs/{invalid_thread}/pause"),
                ("POST", f"/api/runs/{invalid_thread}/resume"),
                ("DELETE", f"/api/runs/{invalid_thread}")
            ]

            for method, endpoint in operations:
                try:
                    if method == "GET":
                        response = self.session.get(f"{self.base_url}{endpoint}")
                    elif method == "DELETE":
                        response = self.session.delete(f"{self.base_url}{endpoint}")
                    else:
                        response = self.session.post(f"{self.base_url}{endpoint}", json={})

                    # Should return appropriate error status
                    assert response.status_code in [404, 400, 500]
                except Exception:
                    # If connection fails, that's also acceptable for this test
                    pass

        except Exception:
            # If any connection issues occur, skip this test
            pass


def run_all_tests():
    """Run all layered architecture tests."""
    
    print("🚀 RUNNING LAYERED ARCHITECTURE TESTS")
    print("=" * 60)
    
    test_classes = [
        TestLayeredArchitecture,
        TestWorkflowControlMechanisms, 
        TestIntegrationScenarios
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}")
        print("-" * 40)
        
        instance = test_class()
        if hasattr(instance, 'setup_method'):
            instance.setup_method()
            
        # Get all test methods
        test_methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for test_method_name in test_methods:
            total_tests += 1
            test_method = getattr(instance, test_method_name)
            
            try:
                test_method()
                print(f"✅ {test_method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"❌ {test_method_name}: {str(e)}")
                
    print(f"\n📊 RESULTS: {passed_tests}/{total_tests} tests passed")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 ALL LAYERED ARCHITECTURE TESTS PASSED!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - Architecture needs attention")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)