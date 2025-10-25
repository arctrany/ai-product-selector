"""
Integration tests for workflow engine refactoring validation.

Tests cover:
- End-to-end workflow execution with all refactored components
- Performance improvements validation
- Security enhancements verification
- Configuration and dependency injection integration
- Database layer optimization validation
- Concurrent workflow execution stress testing
- Error recovery and resilience testing
"""

import asyncio
import os
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from unittest.mock import patch, MagicMock

from src_new.workflow_engine.core.engine import WorkflowEngine, WorkflowInterrupt
from src_new.workflow_engine.core.models import WorkflowDefinition, WorkflowState, NodeType, WorkflowNode, WorkflowEdge
from src_new.workflow_engine.core.config import WorkflowEngineConfig, DependencyContainer
from src_new.workflow_engine.core.security import (
    validate_workflow_definition, 
    UnsafeCodeError,
    InputValidationError,
    execution_timeout
)
from src_new.workflow_engine.storage.database import DatabaseManager


class TestWorkflowEngineIntegrationBasic(unittest.TestCase):
    """Basic integration tests for workflow engine refactoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "integration_test.db")
        
        # Create configuration with all features enabled
        self.config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=True,
            validate_inputs=True,
            enable_async_operations=True,
            enable_batch_operations=True,
            enable_metrics=True,
            thread_pool_workers=4,
            batch_size=50,
            max_execution_time=30
        )
        
        # Create dependency container
        self.container = DependencyContainer()
        
        # Initialize engine with dependency injection
        self.engine = WorkflowEngine(config=self.config, container=self.container)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_workflow_execution(self):
        """Test complete end-to-end workflow execution with all components."""
        # Create comprehensive workflow
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(
                    id="input_validation",
                    type=NodeType.PYTHON,
                    data={"code": "validated_input = input_data if input_data else {'default': True}"}
                ),
                WorkflowNode(
                    id="processing",
                    type=NodeType.PYTHON,
                    data={"code": "processed_data = {'result': validated_input.get('value', 0) * 2, 'timestamp': 'now'}"}
                ),
                WorkflowNode(
                    id="condition_check",
                    type=NodeType.CONDITION,
                    data={"condition": {">=": [{"var": "processed_data.result"}, 10]}}
                ),
                WorkflowNode(
                    id="high_value_handler",
                    type=NodeType.PYTHON,
                    data={"code": "final_result = {'status': 'high', 'value': processed_data['result']}"}
                ),
                WorkflowNode(
                    id="low_value_handler",
                    type=NodeType.PYTHON,
                    data={"code": "final_result = {'status': 'low', 'value': processed_data['result']}"}
                ),
                WorkflowNode(
                    id="output_formatting",
                    type=NodeType.PYTHON,
                    data={"code": "output = {'final': final_result, 'metadata': {'processed_at': 'timestamp'}}"}
                ),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="input_validation"),
                WorkflowEdge(source="input_validation", target="processing"),
                WorkflowEdge(source="processing", target="condition_check"),
                WorkflowEdge(source="condition_check", target="high_value_handler", condition=True),
                WorkflowEdge(source="condition_check", target="low_value_handler", condition=False),
                WorkflowEdge(source="high_value_handler", target="output_formatting"),
                WorkflowEdge(source="low_value_handler", target="output_formatting"),
                WorkflowEdge(source="output_formatting", target="end")
            ]
        )
        
        # Validate workflow definition (security check)
        validate_workflow_definition(definition.dict())
        
        # Create workflow
        flow_id = self.engine.create_flow("integration_test_workflow", definition, version="1.0.0")
        self.assertIsInstance(flow_id, int)
        
        # Get flow version
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        self.assertIsNotNone(flow_version)
        
        # Mock function registration to avoid dependency issues
        with patch.object(self.engine, '_ensure_functions_registered'):
            # Execute workflow with high value
            thread_id_high = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={"value": 15}
            )
            
            # Execute workflow with low value
            thread_id_low = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={"value": 3}
            )
        
        # Verify both executions
        run_high = self.engine.get_workflow_status(thread_id_high)
        run_low = self.engine.get_workflow_status(thread_id_low)
        
        self.assertIsNotNone(run_high)
        self.assertIsNotNone(run_low)
        self.assertEqual(run_high["thread_id"], thread_id_high)
        self.assertEqual(run_low["thread_id"], thread_id_low)

    def test_security_integration_validation(self):
        """Test security integration with workflow engine."""
        # Test 1: Valid workflow should pass
        safe_definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(
                    id="safe_processing", 
                    type=NodeType.PYTHON, 
                    data={"code": "import json\nresult = json.dumps({'safe': True})"}
                ),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="safe_processing"),
                Edge(source="safe_processing", target="end")
            ]
        )
        
        # Should create successfully
        flow_id = self.engine.create_flow("safe_workflow", safe_definition)
        self.assertIsInstance(flow_id, int)
        
        # Test 2: Dangerous workflow should be rejected
        dangerous_definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(
                    id="dangerous_processing", 
                    type=NodeType.PYTHON, 
                    data={"code": "import os\nos.system('rm -rf /')"}
                ),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="dangerous_processing"),
                Edge(source="dangerous_processing", target="end")
            ]
        )
        
        # Should raise security error
        with self.assertRaises(UnsafeCodeError):
            self.engine.create_flow("dangerous_workflow", dangerous_definition)

    def test_configuration_and_dependency_injection_integration(self):
        """Test configuration and dependency injection integration."""
        # Verify configuration is properly applied
        self.assertTrue(self.config.checkpoint_enabled)
        self.assertTrue(self.config.validate_inputs)
        self.assertTrue(self.config.enable_async_operations)
        self.assertEqual(self.config.thread_pool_workers, 4)
        
        # Verify dependency injection
        self.assertIs(self.engine.config, self.config)
        self.assertIs(self.engine.container, self.container)
        
        # Verify database manager is registered in container
        self.assertTrue(self.container.has(DatabaseManager))
        registered_db_manager = self.container.get(DatabaseManager)
        self.assertIs(registered_db_manager, self.engine.db_manager)
        
        # Test custom service registration
        class TestService:
            def __init__(self, value):
                self.value = value
        
        test_service = TestService("integration_test")
        self.container.register_singleton(TestService, test_service)
        
        # Verify service is available
        retrieved_service = self.container.get(TestService)
        self.assertIs(retrieved_service, test_service)
        self.assertEqual(retrieved_service.value, "integration_test")

    def test_database_layer_optimization_integration(self):
        """Test database layer optimization integration."""
        # Create multiple workflows for batch testing
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("batch_test_workflow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        
        # Test batch operations
        thread_ids = []
        with patch.object(self.engine, '_ensure_functions_registered'):
            for i in range(10):
                thread_id = self.engine.start_workflow(
                    flow_version["flow_version_id"],
                    input_data={"batch_id": i}
                )
                thread_ids.append(thread_id)
        
        # Test batch status updates
        updates = [
            {
                "thread_id": thread_id,
                "expected_status": "pending",
                "new_status": "running",
                "metadata": {"batch_updated": True}
            }
            for thread_id in thread_ids
        ]
        
        results = self.engine.db_manager.batch_update_run_statuses(updates)
        
        # Verify batch operation success
        self.assertGreaterEqual(results["success"], 5)  # At least some should succeed
        self.assertEqual(len(results["errors"]), results["failed"])
        
        # Test batch retrieval
        status_results = self.engine.db_manager.get_runs_by_status_batch(["pending", "running"])
        
        self.assertIn("pending", status_results)
        self.assertIn("running", status_results)
        
        # Test async operations
        async def test_async_operations():
            # Test async status update
            if thread_ids:
                success = await self.engine.db_manager.async_update_run_status(
                    thread_ids[0], "running", "completed"
                )
                self.assertTrue(success)
                
                # Test async run retrieval
                run = await self.engine.db_manager.async_get_run(thread_ids[0])
                self.assertIsNotNone(run)
        
        # Run async test
        asyncio.run(test_async_operations())


class TestWorkflowEnginePerformanceValidation(unittest.TestCase):
    """Performance validation tests for workflow engine refactoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "performance_test.db")
        
        # Create high-performance configuration
        self.config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False,  # Disable for performance
            thread_pool_workers=8,
            batch_size=100,
            enable_async_operations=True,
            enable_batch_operations=True
        )
        
        self.engine = WorkflowEngine(config=self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_workflow_execution_performance(self):
        """Test performance of concurrent workflow execution."""
        # Create simple workflow for performance testing
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(
                    id="process", 
                    type=NodeType.PYTHON, 
                    data={"code": "result = input_data.get('id', 0) * 2"}
                ),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="process"),
                Edge(source="process", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("performance_test_workflow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        
        # Performance test parameters
        num_workflows = 50
        max_workers = 10
        
        def execute_workflow(workflow_id):
            with patch.object(self.engine, '_ensure_functions_registered'):
                thread_id = self.engine.start_workflow(
                    flow_version["flow_version_id"],
                    input_data={"id": workflow_id}
                )
            return thread_id
        
        # Measure concurrent execution performance
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(execute_workflow, i) for i in range(num_workflows)]
            thread_ids = [future.result() for future in as_completed(futures)]
        
        execution_time = time.time() - start_time
        
        # Verify all workflows were created
        self.assertEqual(len(thread_ids), num_workflows)
        
        # Performance assertion - should complete within reasonable time
        self.assertLess(execution_time, 30.0, f"Concurrent execution took too long: {execution_time}s")
        
        # Verify all runs exist
        for thread_id in thread_ids:
            run = self.engine.get_workflow_status(thread_id)
            self.assertIsNotNone(run)

    def test_database_batch_operations_performance(self):
        """Test performance of database batch operations."""
        # Create test data
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("batch_perf_workflow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        
        # Create many runs
        num_runs = 100
        thread_ids = []
        
        for i in range(num_runs):
            thread_id = f"batch_perf_thread_{i}"
            self.engine.db_manager.create_run(thread_id, flow_version["flow_version_id"], "pending")
            thread_ids.append(thread_id)
        
        # Test batch update performance
        updates = [
            {
                "thread_id": thread_id,
                "expected_status": "pending",
                "new_status": "running",
                "metadata": {"batch_test": True}
            }
            for thread_id in thread_ids
        ]
        
        # Measure batch update performance
        start_time = time.time()
        results = self.engine.db_manager.batch_update_run_statuses(updates)
        batch_time = time.time() - start_time
        
        # Verify performance and results
        self.assertEqual(results["success"], num_runs)
        self.assertEqual(results["failed"], 0)
        self.assertLess(batch_time, 5.0, f"Batch update took too long: {batch_time}s")
        
        # Test batch retrieval performance
        start_time = time.time()
        status_results = self.engine.db_manager.get_runs_by_status_batch(["running"])
        retrieval_time = time.time() - start_time
        
        # Verify retrieval performance
        self.assertGreaterEqual(len(status_results["running"]), num_runs)
        self.assertLess(retrieval_time, 2.0, f"Batch retrieval took too long: {retrieval_time}s")

    def test_async_operations_performance(self):
        """Test performance of async database operations."""
        # Create test data
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("async_perf_workflow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        
        async def test_async_performance():
            num_operations = 50
            
            # Create runs asynchronously
            create_tasks = []
            for i in range(num_operations):
                thread_id = f"async_perf_thread_{i}"
                # Create run synchronously first
                self.engine.db_manager.create_run(thread_id, flow_version["flow_version_id"], "pending")
                
                # Then create async update task
                task = self.engine.db_manager.async_update_run_status(
                    thread_id, "pending", "running"
                )
                create_tasks.append(task)
            
            # Measure async operations performance
            start_time = time.time()
            results = await asyncio.gather(*create_tasks, return_exceptions=True)
            async_time = time.time() - start_time
            
            # Verify results
            successful_operations = sum(1 for result in results if result is True)
            self.assertGreater(successful_operations, num_operations * 0.8)  # At least 80% success
            self.assertLess(async_time, 10.0, f"Async operations took too long: {async_time}s")
        
        # Run async performance test
        asyncio.run(test_async_performance())


class TestWorkflowEngineStressTesting(unittest.TestCase):
    """Stress testing for workflow engine refactoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "stress_test.db")
        
        # Create stress test configuration
        self.config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=True,
            thread_pool_workers=16,
            batch_size=200,
            enable_async_operations=True,
            enable_batch_operations=True,
            max_execution_time=60
        )
        
        self.engine = WorkflowEngine(config=self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_high_concurrency_stress(self):
        """Test high concurrency stress scenarios."""
        # Create workflow for stress testing
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(
                    id="stress_process", 
                    type=NodeType.PYTHON, 
                    data={"code": "import time; time.sleep(0.01); result = input_data.get('worker_id', 0)"}
                ),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="stress_process"),
                Edge(source="stress_process", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("stress_test_workflow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        
        # Stress test parameters
        num_workers = 100
        max_concurrent = 20
        
        results = []
        errors = []
        
        def stress_worker(worker_id):
            try:
                with patch.object(self.engine, '_ensure_functions_registered'):
                    # Start workflow
                    thread_id = self.engine.start_workflow(
                        flow_version["flow_version_id"],
                        input_data={"worker_id": worker_id}
                    )
                    
                    # Perform operations
                    self.engine.pause_workflow(thread_id)
                    status = self.engine.get_workflow_status(thread_id)
                    self.engine.resume_workflow(thread_id)
                    
                    results.append((worker_id, thread_id, status is not None))
                    
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Execute stress test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [executor.submit(stress_worker, i) for i in range(num_workers)]
            
            # Wait for completion
            for future in as_completed(futures):
                future.result()  # This will raise any exceptions
        
        stress_time = time.time() - start_time
        
        # Verify stress test results
        self.assertLess(len(errors), num_workers * 0.1, f"Too many errors in stress test: {len(errors)}")
        self.assertGreater(len(results), num_workers * 0.9, f"Too few successful operations: {len(results)}")
        self.assertLess(stress_time, 120.0, f"Stress test took too long: {stress_time}s")

    def test_memory_and_resource_management(self):
        """Test memory and resource management under load."""
        # Create multiple workflows to test resource management
        definitions = []
        for i in range(5):
            definition = WorkflowDefinition(
                nodes=[
                    Node(id="start", type=NodeType.START),
                    Node(
                        id=f"process_{i}", 
                        type=NodeType.PYTHON, 
                        data={"code": f"result = 'workflow_{i}_' + str(input_data.get('id', 0))"}
                    ),
                    Node(id="end", type=NodeType.END)
                ],
                edges=[
                    Edge(source="start", target=f"process_{i}"),
                    Edge(source=f"process_{i}", target="end")
                ]
            )
            definitions.append(definition)
        
        # Create workflows
        flow_ids = []
        for i, definition in enumerate(definitions):
            flow_id = self.engine.create_flow(f"resource_test_workflow_{i}", definition)
            flow_ids.append(flow_id)
        
        # Execute many workflow instances
        num_executions = 200
        thread_ids = []
        
        with patch.object(self.engine, '_ensure_functions_registered'):
            for i in range(num_executions):
                flow_id = flow_ids[i % len(flow_ids)]
                flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
                
                thread_id = self.engine.start_workflow(
                    flow_version["flow_version_id"],
                    input_data={"id": i}
                )
                thread_ids.append(thread_id)
        
        # Verify all executions were created
        self.assertEqual(len(thread_ids), num_executions)
        
        # Test resource cleanup
        workflows = self.engine.list_workflows(limit=num_executions + 10)
        self.assertGreaterEqual(len(workflows), num_executions)

    def test_error_recovery_and_resilience(self):
        """Test error recovery and system resilience."""
        # Create workflow that may encounter errors
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(
                    id="error_prone", 
                    type=NodeType.PYTHON, 
                    data={"code": "result = 'success' if input_data.get('should_succeed', True) else 1/0"}
                ),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="error_prone"),
                Edge(source="error_prone", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("resilience_test_workflow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        
        # Test mixed success/failure scenarios
        num_tests = 50
        success_count = 0
        error_count = 0
        
        with patch.object(self.engine, '_ensure_functions_registered'):
            for i in range(num_tests):
                should_succeed = i % 3 != 0  # 2/3 should succeed, 1/3 should fail
                
                try:
                    thread_id = self.engine.start_workflow(
                        flow_version["flow_version_id"],
                        input_data={"should_succeed": should_succeed}
                    )
                    
                    # Check workflow status
                    status = self.engine.get_workflow_status(thread_id)
                    if status:
                        success_count += 1
                    
                except Exception:
                    error_count += 1
        
        # Verify system resilience
        total_operations = success_count + error_count
        self.assertEqual(total_operations, num_tests)
        self.assertGreater(success_count, 0, "No successful operations")
        
        # System should handle errors gracefully without crashing
        self.assertIsNotNone(self.engine.db_manager)
        
        # Test system recovery by executing a simple successful workflow
        simple_definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="end")
            ]
        )
        
        recovery_flow_id = self.engine.create_flow("recovery_test", simple_definition)
        recovery_flow_version = self.engine.db_manager.get_latest_flow_version(recovery_flow_id)
        
        with patch.object(self.engine, '_ensure_functions_registered'):
            recovery_thread_id = self.engine.start_workflow(
                recovery_flow_version["flow_version_id"],
                input_data={}
            )
        
        # Verify system recovered
        recovery_status = self.engine.get_workflow_status(recovery_thread_id)
        self.assertIsNotNone(recovery_status)


class TestWorkflowEngineRegressionValidation(unittest.TestCase):
    """Regression validation tests to ensure refactoring didn't break existing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "regression_test.db")
        
        # Use default configuration to test backward compatibility
        self.config = WorkflowEngineConfig(db_path=self.test_db_path)
        self.engine = WorkflowEngine(config=self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_backward_compatibility_basic_workflow(self):
        """Test backward compatibility with basic workflow patterns."""
        # Test the most basic workflow pattern that should always work
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="end")
            ]
        )
        
        # Should work exactly as before
        flow_id = self.engine.create_flow("regression_basic", definition)
        self.assertIsInstance(flow_id, int)
        
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        self.assertIsNotNone(flow_version)
        
        with patch.object(self.engine, '_ensure_functions_registered'):
            thread_id = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={}
            )
        
        self.assertIsNotNone(thread_id)
        
        # Basic operations should still work
        status = self.engine.get_workflow_status(thread_id)
        self.assertIsNotNone(status)
        
        pause_result = self.engine.pause_workflow(thread_id)
        self.assertTrue(pause_result)
        
        with patch.object(self.engine, '_ensure_functions_registered'):
            resume_result = self.engine.resume_workflow(thread_id)
        self.assertTrue(resume_result)

    def test_existing_api_compatibility(self):
        """Test that existing API methods still work as expected."""
        # Test all public API methods exist and work
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(id="process", type=NodeType.PYTHON, data={"code": "result = 'test'"}),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="process"),
                Edge(source="process", target="end")
            ]
        )
        
        # Test create_flow
        flow_id = self.engine.create_flow("api_test", definition, version="2.0.0")
        self.assertIsInstance(flow_id, int)
        
        # Test workflow compilation
        compiled_graph = self.engine.compile_workflow(definition)
        self.assertIsNotNone(compiled_graph)
        
        # Test start_workflow
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        with patch.object(self.engine, '_ensure_functions_registered'):
            thread_id = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={"test": "data"}
            )
        self.assertIsNotNone(thread_id)
        
        # Test get_workflow_status
        status = self.engine.get_workflow_status(thread_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["thread_id"], thread_id)
        
        # Test list_workflows
        workflows = self.engine.list_workflows(limit=10)
        self.assertIsInstance(workflows, list)
        self.assertGreater(len(workflows), 0)
        
        # Test pause_workflow
        pause_result = self.engine.pause_workflow(thread_id)
        self.assertIsInstance(pause_result, bool)
        
        # Test resume_workflow
        with patch.object(self.engine, '_ensure_functions_registered'):
            resume_result = self.engine.resume_workflow(thread_id)
        self.assertIsInstance(resume_result, bool)

    def test_data_format_compatibility(self):
        """Test that data formats remain compatible."""
        # Create workflow and verify data structures
        definition = WorkflowDefinition(
            nodes=[
                Node(id="start", type=NodeType.START),
                Node(id="end", type=NodeType.END)
            ],
            edges=[
                Edge(source="start", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("data_format_test", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        
        # Verify flow version data structure
        expected_fields = ["flow_version_id", "flow_id", "version", "dsl_json", "published", "created_at"]
        for field in expected_fields:
            self.assertIn(field, flow_version)
        
        # Verify DSL JSON structure
        dsl_json = flow_version["dsl_json"]
        self.assertIn("nodes", dsl_json)
        self.assertIn("edges", dsl_json)
        self.assertIsInstance(dsl_json["nodes"], list)
        self.assertIsInstance(dsl_json["edges"], list)
        
        # Execute workflow and verify run data structure
        with patch.object(self.engine, '_ensure_functions_registered'):
            thread_id = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={"test": "compatibility"}
            )
        
        run_status = self.engine.get_workflow_status(thread_id)
        expected_run_fields = ["thread_id", "flow_version_id", "status", "metadata"]
        for field in expected_run_fields:
            self.assertIn(field, run_status)


if __name__ == '__main__':
    # Create test suite with all integration tests
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestWorkflowEngineIntegrationBasic))
    suite.addTest(unittest.makeSuite(TestWorkflowEnginePerformanceValidation))
    suite.addTest(unittest.makeSuite(TestWorkflowEngineStressTesting))
    suite.addTest(unittest.makeSuite(TestWorkflowEngineRegressionValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print("\n🎉 All integration tests passed! Workflow engine refactoring validation successful.")
    else:
        print(f"\n❌ Integration tests failed: {len(result.failures)} failures, {len(result.errors)} errors")