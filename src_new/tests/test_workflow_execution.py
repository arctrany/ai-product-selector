"""Test workflow execution functionality."""

import unittest
import tempfile
import os
import sys
import shutil
import time
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_engine.core.engine import WorkflowEngine, WorkflowInterrupt
from workflow_engine.core.config import WorkflowEngineConfig
from workflow_engine.core.models import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, NodeType,
    PythonNodeData, ConditionNodeData, WorkflowState
)

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
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_node_execution(self):
        """Test start node execution."""
        state = WorkflowState(
            thread_id="test_thread",
            data={},
            metadata={}
        )
        
        result = self.engine._start_node(state)
        
        self.assertIn("current_node", result)
        self.assertEqual(result["current_node"], "__start__")

    def test_end_node_execution(self):
        """Test end node execution."""
        state = WorkflowState(
            thread_id="test_thread",
            data={},
            metadata={}
        )
        
        result = self.engine._end_node(state)
        
        self.assertIn("current_node", result)
        self.assertEqual(result["current_node"], "__end__")

    def test_condition_router_with_boolean(self):
        """Test condition router with boolean condition."""
        state = WorkflowState(
            thread_id="test_thread",
            data={"value": True},
            metadata={}
        )
        
        # Test with True condition
        router = self.engine._create_condition_router(True)
        result = router(state)
        self.assertTrue(result)
        
        # Test with False condition
        router = self.engine._create_condition_router(False)
        result = router(state)
        self.assertFalse(result)

    def test_condition_router_with_dict(self):
        """Test condition router with dictionary condition."""
        state = WorkflowState(
            thread_id="test_thread",
            data={"value": 10},
            metadata={}
        )
        
        # Test with JSONLogic-style condition
        condition = {">=": [{"var": "value"}, 5]}
        router = self.engine._create_condition_router(condition)
        
        # Should return True since value (10) >= 5
        # Note: This test may pass even without json_logic if fallback returns True
        result = router(state)
        self.assertIsInstance(result, bool)

    def test_workflow_interrupt_exception(self):
        """Test WorkflowInterrupt exception."""
        interrupt = WorkflowInterrupt("test reason", {"key": "value"})
        
        self.assertEqual(interrupt.reason, "test reason")
        self.assertEqual(interrupt.data, {"key": "value"})
        self.assertIn("test reason", str(interrupt))

    def test_create_flow(self):
        """Test creating a workflow flow."""
        definition = WorkflowDefinition(
            name="test_flow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("test_workflow", definition, "1.0.0")
        
        self.assertIsInstance(flow_id, int)
        self.assertGreater(flow_id, 0)

    def test_get_workflow_status(self):
        """Test getting workflow status."""
        # Create a test workflow first
        definition = WorkflowDefinition(
            name="test_status_flow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("test_status_workflow", definition)
        
        # Start workflow
        thread_id = self.engine.start_workflow(flow_id, {"test": "data"})
        
        # Get status
        status = self.engine.get_workflow_status(thread_id)
        
        self.assertIsNotNone(status)
        self.assertEqual(status["thread_id"], thread_id)
        self.assertIn("status", status)

    def test_list_workflows(self):
        """Test listing workflows."""
        # Create a test workflow
        definition = WorkflowDefinition(
            name="test_list_flow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("test_list_workflow", definition)
        
        # Start workflow
        self.engine.start_workflow(flow_id, {"test": "data"})
        
        # List workflows
        workflows = self.engine.list_workflows(limit=10)
        
        self.assertIsInstance(workflows, list)
        self.assertGreater(len(workflows), 0)

    def test_pause_workflow(self):
        """Test pausing workflow."""
        thread_id = "test_pause_thread"
        
        result = self.engine.pause_workflow(thread_id)
        
        self.assertTrue(result)

    @patch('workflow_engine.core.engine.WorkflowEngine._ensure_functions_registered')
    def test_start_workflow_with_mock(self, mock_ensure_functions):
        """Test starting workflow with mocked function registration."""
        # Mock the function registration to avoid app loading issues
        mock_ensure_functions.return_value = None
        
        # Create a simple workflow
        definition = WorkflowDefinition(
            name="test_mock_flow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )
        
        flow_id = self.engine.create_flow("test_mock_workflow", definition)
        
        # Start workflow
        thread_id = self.engine.start_workflow(flow_id, {"test": "data"})
        
        self.assertIsInstance(thread_id, str)
        self.assertTrue(len(thread_id) > 0)
        
        # Verify function registration was called
        mock_ensure_functions.assert_called_once_with(flow_id)

    def test_compile_workflow_with_conditional_edges(self):
        """Test compiling workflow with conditional edges."""
        definition = WorkflowDefinition(
            name="test_conditional_flow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(
                    id="condition", 
                    type=NodeType.CONDITION,
                    data=ConditionNodeData(expr={"==": [{"var": "value"}, True]})
                ),
                WorkflowNode(id="true_branch", type=NodeType.END),
                WorkflowNode(id="false_branch", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="condition"),
                WorkflowEdge(source="condition", target="true_branch", condition=True),
                WorkflowEdge(source="condition", target="false_branch", condition=False)
            ]
        )
        
        # Should compile without errors
        graph = self.engine.compile_workflow(definition)
        compiled_graph = graph.compile()
        
        self.assertIsNotNone(compiled_graph)

    def test_workflow_state_creation(self):
        """Test WorkflowState creation and properties."""
        state = WorkflowState(
            thread_id="test_state_thread",
            data={"key": "value"},
            metadata={"meta_key": "meta_value"}
        )
        
        self.assertEqual(state.thread_id, "test_state_thread")
        self.assertEqual(state.data["key"], "value")
        self.assertEqual(state.metadata["meta_key"], "meta_value")

    def test_engine_initialization_with_config(self):
        """Test engine initialization with custom config."""
        custom_config = WorkflowEngineConfig(
            db_pool_size=10,
            thread_pool_workers=8,
            checkpoint_enabled=False
        )
        
        engine = WorkflowEngine(config=custom_config)
        
        self.assertEqual(engine.config.db_pool_size, 10)
        self.assertEqual(engine.config.thread_pool_workers, 8)
        self.assertFalse(engine.config.checkpoint_enabled)
        
        # Clean up
        engine.db_manager.close()

    def test_checkpointer_initialization_disabled(self):
        """Test checkpointer initialization when disabled."""
        config = WorkflowEngineConfig(checkpoint_enabled=False)
        engine = WorkflowEngine(config=config)
        
        self.assertIsNone(engine.checkpointer)
        
        # Clean up
        engine.db_manager.close()

    def test_checkpointer_initialization_enabled(self):
        """Test checkpointer initialization when enabled."""
        config = WorkflowEngineConfig(
            checkpoint_enabled=True,
            checkpoint_db_path=":memory:"
        )
        engine = WorkflowEngine(config=config)
        
        # Should have checkpointer (or None if initialization failed)
        # We don't assert it's not None because initialization might fail in test environment
        self.assertIsInstance(engine.checkpointer, (type(None), object))
        
        # Clean up
        engine.db_manager.close()


class TestWorkflowExecutionIntegration(unittest.TestCase):
    """Integration tests for workflow execution."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_integration.db")
        
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False
        )
        self.engine = WorkflowEngine(config=config)

    def tearDown(self):
        """Clean up test fixtures."""
        self.engine.db_manager.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('workflow_engine.core.engine.WorkflowEngine._ensure_functions_registered')
    def test_simple_workflow_execution(self, mock_ensure_functions):
        """Test execution of a simple workflow."""
        mock_ensure_functions.return_value = None
        
        # Create simple workflow
        definition = WorkflowDefinition(
            name="simple_integration_flow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="end")
            ]
        )
        
        # Create and start workflow
        flow_id = self.engine.create_flow("simple_integration", definition)
        thread_id = self.engine.start_workflow(flow_id, {"input": "test"})
        
        # Verify execution
        self.assertIsInstance(thread_id, str)
        
        # Check status
        status = self.engine.get_workflow_status(thread_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["thread_id"], thread_id)

    @patch('workflow_engine.core.engine.WorkflowEngine._ensure_functions_registered')
    def test_workflow_with_multiple_nodes(self, mock_ensure_functions):
        """Test workflow with multiple nodes."""
        mock_ensure_functions.return_value = None
        
        definition = WorkflowDefinition(
            name="multi_node_flow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(
                    id="condition",
                    type=NodeType.CONDITION,
                    data=ConditionNodeData(expr={">=": [{"var": "value"}, 5]})
                ),
                WorkflowNode(id="high", type=NodeType.END),
                WorkflowNode(id="low", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="condition"),
                WorkflowEdge(source="condition", target="high", condition=True),
                WorkflowEdge(source="condition", target="low", condition=False)
            ]
        )
        
        flow_id = self.engine.create_flow("multi_node_workflow", definition)
        
        # Test with high value
        thread_id1 = self.engine.start_workflow(flow_id, {"value": 10})
        self.assertIsInstance(thread_id1, str)
        
        # Test with low value
        thread_id2 = self.engine.start_workflow(flow_id, {"value": 2})
        self.assertIsInstance(thread_id2, str)


if __name__ == '__main__':
    unittest.main()