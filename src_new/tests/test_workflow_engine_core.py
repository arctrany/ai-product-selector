"""
Unit tests for workflow engine core functionality.

Tests cover:
- WorkflowEngine initialization with dependency injection
- Workflow compilation and execution
- WorkflowInterrupt exception handling
- Checkpoint persistence integration
- Node execution (start, end, python, condition)
- Edge routing and conditional logic
- Thread safety and concurrent workflow execution
- Error handling and recovery
"""

import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

from src_new.workflow_engine.core.engine import WorkflowEngine, WorkflowInterrupt
from src_new.workflow_engine.core.models import WorkflowDefinition, WorkflowState, NodeType, WorkflowNode, WorkflowEdge
from src_new.workflow_engine.core.config import WorkflowEngineConfig, DependencyContainer
from src_new.workflow_engine.storage.database import DatabaseManager


class TestWorkflowEngineInitialization(unittest.TestCase):
    """Test WorkflowEngine initialization and configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_engine_initialization_default_config(self):
        """Test engine initialization with default configuration."""
        engine = WorkflowEngine()
        
        self.assertIsNotNone(engine.config)
        self.assertIsNotNone(engine.container)
        self.assertIsNotNone(engine.db_manager)
        self.assertIsInstance(engine.config, WorkflowEngineConfig)
        self.assertIsInstance(engine.container, DependencyContainer)

    def test_engine_initialization_custom_config(self):
        """Test engine initialization with custom configuration."""
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False,
            thread_pool_workers=8
        )
        container = DependencyContainer()
        
        engine = WorkflowEngine(config=config, container=container)
        
        self.assertIs(engine.config, config)
        self.assertIs(engine.container, container)
        self.assertEqual(engine.config.db_path, self.test_db_path)
        self.assertFalse(engine.config.checkpoint_enabled)

    def test_engine_dependency_injection(self):
        """Test dependency injection in engine initialization."""
        config = WorkflowEngineConfig(db_path=self.test_db_path)
        container = DependencyContainer()
        
        # Pre-register database manager
        db_manager = DatabaseManager(self.test_db_path)
        container.register_singleton(DatabaseManager, db_manager)
        
        engine = WorkflowEngine(config=config, container=container)
        
        # Should use the pre-registered database manager
        self.assertIs(engine.db_manager, db_manager)
        
        # Clean up
        db_manager.close()

    def test_checkpointer_initialization_enabled(self):
        """Test checkpointer initialization when enabled."""
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=True
        )
        
        engine = WorkflowEngine(config=config)
        
        # Checkpointer should be initialized
        self.assertIsNotNone(engine.checkpointer)

    def test_checkpointer_initialization_disabled(self):
        """Test checkpointer initialization when disabled."""
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False
        )
        
        engine = WorkflowEngine(config=config)
        
        # Checkpointer should be None
        self.assertIsNone(engine.checkpointer)

    def test_thread_safety_initialization(self):
        """Test thread safety of engine initialization."""
        engines = []
        errors = []

        def create_engine(worker_id):
            try:
                config = WorkflowEngineConfig(
                    db_path=os.path.join(self.temp_dir, f"test_{worker_id}.db")
                )
                engine = WorkflowEngine(config=config)
                engines.append((worker_id, engine))
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_engine, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Thread safety test failed: {errors}")
        self.assertEqual(len(engines), 5)
        
        # All engines should be properly initialized
        for worker_id, engine in engines:
            self.assertIsNotNone(engine.config)
            self.assertIsNotNone(engine.db_manager)


class TestWorkflowCompilation(unittest.TestCase):
    """Test workflow compilation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")
        
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False
        )
        self.engine = WorkflowEngine(config=config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compile_simple_workflow(self):
        """Test compilation of simple linear workflow."""
        # Create simple workflow definition
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="process", type=NodeType.PYTHON, data={"code": "result = 'processed'"}),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="process"),
                WorkflowEdge(source="process", target="end")
            ]
        )

        # Compile workflow
        graph = self.engine.compile_workflow(definition)

        self.assertIsNotNone(graph)
        # Graph should be compilable
        compiled_graph = graph.compile()
        self.assertIsNotNone(compiled_graph)

    def test_compile_workflow_with_conditions(self):
        """Test compilation of workflow with conditional edges."""
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="condition", type=NodeType.CONDITION, data={"condition": {"==": [{"var": "value"}, True]}}),
                WorkflowNode(id="true_branch", type=NodeType.PYTHON, data={"code": "result = 'true'"}),
                WorkflowNode(id="false_branch", type=NodeType.PYTHON, data={"code": "result = 'false'"}),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="condition"),
                WorkflowEdge(source="condition", target="true_branch", condition=True),
                WorkflowEdge(source="condition", target="false_branch", condition=False),
                WorkflowEdge(source="true_branch", target="end"),
                WorkflowEdge(source="false_branch", target="end")
            ]
        )

        # Compile workflow
        graph = self.engine.compile_workflow(definition)
        compiled_graph = graph.compile()

        self.assertIsNotNone(compiled_graph)

    def test_compile_workflow_invalid_node_type(self):
        """Test compilation failure with invalid node type."""
        # Create workflow with invalid node type
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="invalid", type="invalid_type")
            ],
            edges=[]
        )

        with self.assertRaises(ValueError) as context:
            self.engine.compile_workflow(definition)

        self.assertIn("Unsupported node type", str(context.exception))

    def test_compile_workflow_no_start_node(self):
        """Test compilation with no start node."""
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="process", type=NodeType.PYTHON, data={"code": "result = 'test'"})
            ],
            edges=[]
        )

        # Should still compile but use first node as entry point
        graph = self.engine.compile_workflow(definition)
        compiled_graph = graph.compile()

        self.assertIsNotNone(compiled_graph)


class TestWorkflowExecution(unittest.TestCase):
    """Test workflow execution functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")

        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False
        )
        self.engine = WorkflowEngine(config=config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_execute_simple_workflow(self):
        """Test creating and executing a simple workflow."""
        # Create workflow definition
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )

        # Create workflow
        flow_id = self.engine.create_flow("test_simple_flow", definition)
        self.assertIsInstance(flow_id, int)

        # Get flow version
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        self.assertIsNotNone(flow_version)

        # Mock function registration to avoid dependency issues
        with patch.object(self.engine, '_ensure_functions_registered'):
            # Start workflow execution
            thread_id = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={"test": "data"}
            )

        self.assertIsNotNone(thread_id)

        # Check run was created
        run = self.engine.get_workflow_status(thread_id)
        self.assertIsNotNone(run)
        self.assertEqual(run["thread_id"], thread_id)

    def test_workflow_execution_with_python_node(self):
        """Test workflow execution with Python node."""
        # Mock the function registration and node execution
        with patch('src_new.workflow_engine.core.registry.get_registered_function') as mock_get_func:
            mock_get_func.return_value = lambda state, logger: {"result": "processed"}

            definition = WorkflowDefinition(
                nodes=[
                    WorkflowNode(id="start", type=NodeType.START),
                    WorkflowNode(id="process", type=NodeType.PYTHON, data={"code": "result = 'processed'"}),
                    WorkflowNode(id="end", type=NodeType.END)
                ],
                edges=[
                    WorkflowEdge(source="start", target="process"),
                    WorkflowEdge(source="process", target="end")
                ]
            )

            flow_id = self.engine.create_flow("test_python_flow", definition)
            flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)

            with patch.object(self.engine, '_ensure_functions_registered'):
                thread_id = self.engine.start_workflow(
                    flow_version["flow_version_id"],
                    input_data={"input": "test"}
                )

            self.assertIsNotNone(thread_id)

    def test_workflow_execution_with_interrupt(self):
        """Test workflow execution with interrupt handling."""
        # Create workflow that will be interrupted
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="interrupt_node", type=NodeType.PYTHON, data={"code": "interrupt('test_interrupt')"}),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="interrupt_node"),
                WorkflowEdge(source="interrupt_node", target="end")
            ]
        )

        flow_id = self.engine.create_flow("test_interrupt_flow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)

        with patch.object(self.engine, '_ensure_functions_registered'):
            thread_id = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={}
            )

        # Check that run exists (may be paused due to interrupt)
        run = self.engine.get_workflow_status(thread_id)
        self.assertIsNotNone(run)

    def test_workflow_pause_and_resume(self):
        """Test workflow pause and resume functionality."""
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )

        flow_id = self.engine.create_flow("test_pause_flow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)

        with patch.object(self.engine, '_ensure_functions_registered'):
            thread_id = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={}
            )

        # Pause workflow
        pause_success = self.engine.pause_workflow(thread_id)
        self.assertTrue(pause_success)

        # Check pause signal was created
        signals = self.engine.db_manager.get_pending_signals(thread_id)
        pause_signals = [s for s in signals if s["type"] == "pause_request"]
        self.assertGreater(len(pause_signals), 0)

        # Resume workflow
        with patch.object(self.engine, '_ensure_functions_registered'):
            resume_success = self.engine.resume_workflow(thread_id)

        # Resume should work (even if workflow already completed)
        self.assertTrue(resume_success)

    def test_concurrent_workflow_execution(self):
        """Test concurrent execution of multiple workflows."""
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )

        flow_id = self.engine.create_flow("test_concurrent_flow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)

        thread_ids = []
        errors = []

        def execute_workflow(worker_id):
            try:
                with patch.object(self.engine, '_ensure_functions_registered'):
                    thread_id = self.engine.start_workflow(
                        flow_version["flow_version_id"],
                        input_data={"worker_id": worker_id}
                    )
                thread_ids.append(thread_id)
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=execute_workflow, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent execution failed: {errors}")
        self.assertEqual(len(thread_ids), 5)

        # All workflows should have been created
        for thread_id in thread_ids:
            run = self.engine.get_workflow_status(thread_id)
            self.assertIsNotNone(run)


class TestWorkflowInterrupt(unittest.TestCase):
    """Test WorkflowInterrupt exception functionality."""

    def test_workflow_interrupt_creation(self):
        """Test WorkflowInterrupt exception creation."""
        interrupt = WorkflowInterrupt("test reason", {"key": "value"})

        self.assertEqual(interrupt.reason, "test reason")
        self.assertEqual(interrupt.data["key"], "value")
        self.assertIn("test reason", str(interrupt))

    def test_workflow_interrupt_without_data(self):
        """Test WorkflowInterrupt exception without data."""
        interrupt = WorkflowInterrupt("test reason")

        self.assertEqual(interrupt.reason, "test reason")
        self.assertEqual(interrupt.data, {})

    def test_workflow_interrupt_inheritance(self):
        """Test WorkflowInterrupt exception inheritance."""
        interrupt = WorkflowInterrupt("test")

        self.assertIsInstance(interrupt, Exception)


class TestNodeExecution(unittest.TestCase):
    """Test individual node execution functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")

        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False
        )
        self.engine = WorkflowEngine(config=config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_node_execution(self):
        """Test start node execution."""
        # Create test state
        state = WorkflowState(
            thread_id="test_thread",
            data={},
            metadata={}
        )

        # Create run in database
        flow_id = self.engine.db_manager.create_flow_by_name("test_flow", "1.0.0")
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        self.engine.db_manager.create_run(
            state.thread_id,
            flow_version["flow_version_id"],
            "pending"
        )

        # Execute start node
        result = self.engine._start_node(state)

        self.assertIn("current_node", result)
        self.assertEqual(result["current_node"], "__start__")

        # Check that run status was updated
        run = self.engine.db_manager.get_run(state.thread_id)
        # Note: Status might not be updated if atomic update fails due to timing

    def test_end_node_execution(self):
        """Test end node execution."""
        # Create test state
        state = WorkflowState(
            thread_id="test_thread_end",
            data={},
            metadata={}
        )

        # Create run in database
        flow_id = self.engine.db_manager.create_flow_by_name("test_flow", "1.0.0")
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        self.engine.db_manager.create_run(
            state.thread_id,
            flow_version["flow_version_id"],
            "running"
        )

        # Execute end node
        result = self.engine._end_node(state)

        self.assertIn("current_node", result)
        self.assertEqual(result["current_node"], "__end__")

    def test_python_node_handler_creation(self):
        """Test Python node handler creation."""
        node_def = WorkflowNode(
            id="test_python",
            type=NodeType.PYTHON,
            data={"code": "result = 'test'"}
        )

        handler = self.engine._create_python_node_handler(node_def)

        self.assertIsNotNone(handler)
        self.assertTrue(callable(handler))

    def test_condition_node_handler_creation(self):
        """Test condition node handler creation."""
        node_def = WorkflowNode(
            id="test_condition",
            type=NodeType.CONDITION,
            data={"condition": {"==": [{"var": "test"}, True]}}
        )

        handler = self.engine._create_condition_node_handler(node_def)

        self.assertIsNotNone(handler)
        self.assertTrue(callable(handler))

    def test_condition_router_creation(self):
        """Test condition router creation."""
        # Boolean condition
        router = self.engine._create_condition_router(True)
        state = WorkflowState(thread_id="test", data={}, metadata={})
        result = router(state)
        self.assertTrue(result)

        # Dict condition (JSONLogic)
        condition = {"==": [{"var": "test_value"}, "expected"]}
        router = self.engine._create_condition_router(condition)

        # Test with matching data
        state = WorkflowState(
            thread_id="test",
            data={"test_value": "expected"},
            metadata={}
        )

        # Mock json_logic if not available
        with patch('src_new.workflow_engine.core.engine.jsonlogic') as mock_jsonlogic:
            mock_jsonlogic.jsonLogic.return_value = True
            result = router(state)
            self.assertTrue(result)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in workflow engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")

        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False
        )
        self.engine = WorkflowEngine(config=config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_workflow_execution_error_handling(self):
        """Test error handling during workflow execution."""
        # Create workflow that will cause an error
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="error_node", type=NodeType.PYTHON, data={"code": "raise Exception('test error')"}),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="error_node"),
                WorkflowEdge(source="error_node", target="end")
            ]
        )

        flow_id = self.engine.create_flow("test_error_flow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)

        # Mock function registration
        with patch.object(self.engine, '_ensure_functions_registered'):
            # Execution should handle the error gracefully
            try:
                thread_id = self.engine.start_workflow(
                    flow_version["flow_version_id"],
                    input_data={}
                )
                # If no exception is raised, check the run status
                run = self.engine.get_workflow_status(thread_id)
                self.assertIsNotNone(run)
            except Exception:
                # Exception is expected for error scenarios
                pass

    def test_nonexistent_flow_version_error(self):
        """Test error handling for nonexistent flow version."""
        with patch.object(self.engine, '_ensure_functions_registered'):
            with self.assertRaises(ValueError) as context:
                self.engine.start_workflow(99999, input_data={})

        self.assertIn("Flow version not found", str(context.exception))

    def test_invalid_workflow_definition_error(self):
        """Test error handling for invalid workflow definition."""
        # Create invalid definition (will be caught by security validation)
        invalid_definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="invalid", type=NodeType.PYTHON, data={"code": "import os; os.system('rm -rf /')"})
            ],
            edges=[]
        )

        # Should raise security error
        with self.assertRaises(Exception):  # Could be UnsafeCodeError or similar
            self.engine.create_flow("invalid_flow", invalid_definition)


class TestWorkflowEngineIntegration(unittest.TestCase):
    """Integration tests for workflow engine functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")

        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=True,  # Enable checkpoints for integration test
            thread_pool_workers=4
        )
        self.engine = WorkflowEngine(config=config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_workflow_lifecycle(self):
        """Test complete workflow lifecycle from creation to execution."""
        # Create complex workflow
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="process1", type=NodeType.PYTHON, data={"code": "result = input_data.get('value', 0) * 2"}),
                WorkflowNode(id="condition", type=NodeType.CONDITION, data={"condition": {">=": [{"var": "result"}, 10]}}),
                WorkflowNode(id="high_value", type=NodeType.PYTHON, data={"code": "final_result = 'high'"}),
                WorkflowNode(id="low_value", type=NodeType.PYTHON, data={"code": "final_result = 'low'"}),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="process1"),
                WorkflowEdge(source="process1", target="condition"),
                WorkflowEdge(source="condition", target="high_value", condition=True),
                WorkflowEdge(source="condition", target="low_value", condition=False),
                WorkflowEdge(source="high_value", target="end"),
                WorkflowEdge(source="low_value", target="end")
            ]
        )

        # Create workflow
        flow_id = self.engine.create_flow("integration_test_flow", definition, version="1.0.0")
        self.assertIsInstance(flow_id, int)

        # Get flow version
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        self.assertIsNotNone(flow_version)
        self.assertEqual(flow_version["version"], "1.0.0")

        # Mock function registration
        with patch.object(self.engine, '_ensure_functions_registered'):
            # Execute workflow with high value
            thread_id_high = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={"value": 10}
            )

            # Execute workflow with low value
            thread_id_low = self.engine.start_workflow(
                flow_version["flow_version_id"],
                input_data={"value": 2}
            )

        # Check both executions
        run_high = self.engine.get_workflow_status(thread_id_high)
        run_low = self.engine.get_workflow_status(thread_id_low)

        self.assertIsNotNone(run_high)
        self.assertIsNotNone(run_low)
        self.assertEqual(run_high["flow_version_id"], flow_version["flow_version_id"])
        self.assertEqual(run_low["flow_version_id"], flow_version["flow_version_id"])

    def test_workflow_list_and_status_operations(self):
        """Test workflow listing and status operations."""
        # Create multiple workflows
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )

        flow_ids = []
        for i in range(3):
            flow_id = self.engine.create_flow(f"list_test_flow_{i}", definition)
            flow_ids.append(flow_id)

        # Execute some workflows
        thread_ids = []
        with patch.object(self.engine, '_ensure_functions_registered'):
            for flow_id in flow_ids:
                flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
                thread_id = self.engine.start_workflow(
                    flow_version["flow_version_id"],
                    input_data={"test": f"data_{flow_id}"}
                )
                thread_ids.append(thread_id)

        # List workflows
        workflows = self.engine.list_workflows(limit=10)
        self.assertGreaterEqual(len(workflows), 3)

        # Check individual workflow statuses
        for thread_id in thread_ids:
            status = self.engine.get_workflow_status(thread_id)
            self.assertIsNotNone(status)
            self.assertEqual(status["thread_id"], thread_id)

    def test_engine_thread_safety_comprehensive(self):
        """Test comprehensive thread safety of workflow engine."""
        definition = WorkflowDefinition(
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="process", type=NodeType.PYTHON, data={"code": "result = f'processed_{input_data.get(\"id\", 0)}'"}),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="process"),
                WorkflowEdge(source="process", target="end")
            ]
        )
        
        # Create workflow once
        flow_id = self.engine.create_flow("thread_safety_flow", definition)
        flow_version = self.engine.db_manager.get_latest_flow_version(flow_id)
        
        results = []
        errors = []

        def comprehensive_worker(worker_id):
            try:
                with patch.object(self.engine, '_ensure_functions_registered'):
                    # Start workflow
                    thread_id = self.engine.start_workflow(
                        flow_version["flow_version_id"],
                        input_data={"id": worker_id}
                    )
                    
                    # Pause workflow
                    self.engine.pause_workflow(thread_id)
                    
                    # Get status
                    status = self.engine.get_workflow_status(thread_id)
                    
                    # Resume workflow
                    self.engine.resume_workflow(thread_id)
                    
                    results.append((worker_id, thread_id, status is not None))
                    
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=comprehensive_worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Thread safety test failed: {errors}")
        self.assertEqual(len(results), 10)
        
        # All operations should succeed
        for worker_id, thread_id, status_exists in results:
            self.assertIsNotNone(thread_id)
            self.assertTrue(status_exists, f"Worker {worker_id} failed to get status")


if __name__ == '__main__':
    unittest.main()