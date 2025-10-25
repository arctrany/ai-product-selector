"""Test workflow engine initialization functionality."""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock

from src_new.workflow_engine.core.engine import WorkflowEngine
from src_new.workflow_engine.core.config import WorkflowEngineConfig
from src_new.workflow_engine.core.models import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, NodeType,
    PythonNodeData, ConditionNodeData
)


class TestWorkflowEngineInitialization(unittest.TestCase):
    """Test WorkflowEngine initialization and configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_engine_initialization_default_config(self):
        """Test engine initialization with default configuration."""
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=True
        )
        engine = WorkflowEngine(config=config)
        
        self.assertIsNotNone(engine.config)
        self.assertIsNotNone(engine.db_manager)
        self.assertEqual(engine.config.db_path, self.test_db_path)
        self.assertTrue(engine.config.checkpoint_enabled)
        
        # Clean up
        engine.db_manager.close()

    def test_engine_initialization_custom_config(self):
        """Test engine initialization with custom configuration."""
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False,
            validate_inputs=False
        )
        engine = WorkflowEngine(config=config)
        
        self.assertIsNotNone(engine.config)
        self.assertIsNotNone(engine.db_manager)
        self.assertEqual(engine.config.db_path, self.test_db_path)
        self.assertFalse(engine.config.checkpoint_enabled)
        self.assertFalse(engine.config.validate_inputs)
        
        # Clean up
        engine.db_manager.close()

    def test_checkpointer_initialization_enabled(self):
        """Test checkpointer initialization when enabled."""
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=True
        )
        engine = WorkflowEngine(config=config)
        
        # Checkpointer should be initialized
        self.assertIsNotNone(engine.checkpointer)
        
        # Clean up
        engine.db_manager.close()

    def test_checkpointer_initialization_disabled(self):
        """Test checkpointer initialization when disabled."""
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False
        )
        engine = WorkflowEngine(config=config)
        
        # Checkpointer should be None
        self.assertIsNone(engine.checkpointer)
        
        # Clean up
        engine.db_manager.close()

    def test_simple_workflow_definition_creation(self):
        """Test creating a simple workflow definition with correct data structure."""
        # Create workflow definition with proper data structure
        definition = WorkflowDefinition(
            name="test_simple_workflow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(
                    id="process", 
                    type=NodeType.PYTHON, 
                    data=PythonNodeData(code_ref="test_function", args={"input": "test"})
                ),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="process"),
                WorkflowEdge(source="process", target="end")
            ]
        )
        
        # Verify the definition is created correctly
        self.assertEqual(definition.name, "test_simple_workflow")
        self.assertEqual(len(definition.nodes), 3)
        self.assertEqual(len(definition.edges), 2)
        
        # Verify node types
        self.assertEqual(definition.nodes[0].type, NodeType.START)
        self.assertEqual(definition.nodes[1].type, NodeType.PYTHON)
        self.assertEqual(definition.nodes[2].type, NodeType.END)
        
        # Verify Python node data
        python_node = definition.nodes[1]
        self.assertIsInstance(python_node.data, PythonNodeData)
        self.assertEqual(python_node.data.code_ref, "test_function")
        self.assertEqual(python_node.data.args, {"input": "test"})

    def test_condition_workflow_definition_creation(self):
        """Test creating a workflow definition with condition nodes."""
        definition = WorkflowDefinition(
            name="test_condition_workflow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(
                    id="condition", 
                    type=NodeType.CONDITION, 
                    data=ConditionNodeData(expr={"==": [{"var": "value"}, True]})
                ),
                WorkflowNode(
                    id="true_branch", 
                    type=NodeType.PYTHON, 
                    data=PythonNodeData(code_ref="handle_true", args={})
                ),
                WorkflowNode(
                    id="false_branch", 
                    type=NodeType.PYTHON, 
                    data=PythonNodeData(code_ref="handle_false", args={})
                ),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="condition"),
                WorkflowEdge(source="condition", target="true_branch"),
                WorkflowEdge(source="condition", target="false_branch"),
                WorkflowEdge(source="true_branch", target="end"),
                WorkflowEdge(source="false_branch", target="end")
            ]
        )
        
        # Verify the definition is created correctly
        self.assertEqual(definition.name, "test_condition_workflow")
        self.assertEqual(len(definition.nodes), 5)
        self.assertEqual(len(definition.edges), 5)
        
        # Verify condition node data
        condition_node = definition.nodes[1]
        self.assertIsInstance(condition_node.data, ConditionNodeData)
        self.assertEqual(condition_node.data.expr, {"==": [{"var": "value"}, True]})


if __name__ == '__main__':
    unittest.main()