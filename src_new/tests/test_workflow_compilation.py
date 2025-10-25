"""Test workflow compilation functionality."""

import unittest
import tempfile
import os
import sys
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_engine.core.engine import WorkflowEngine
from workflow_engine.core.config import WorkflowEngineConfig
from workflow_engine.core.models import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, NodeType,
    PythonNodeData, ConditionNodeData
)


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
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compile_simple_workflow(self):
        """Test compilation of simple linear workflow."""
        # Create simple workflow definition with correct data structure
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
        
        # Compile workflow
        graph = self.engine.compile_workflow(definition)
        
        self.assertIsNotNone(graph)
        # Graph should be compilable
        compiled_graph = graph.compile()
        self.assertIsNotNone(compiled_graph)

    def test_compile_workflow_with_conditions(self):
        """Test compilation of workflow with conditional edges."""
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
        
        # Compile workflow
        graph = self.engine.compile_workflow(definition)
        compiled_graph = graph.compile()
        
        self.assertIsNotNone(compiled_graph)

    def test_compile_workflow_invalid_node_type(self):
        """Test compilation failure with invalid node type."""
        # Pydantic validates node types at creation time, so test that
        with self.assertRaises(ValueError) as context:
            WorkflowNode(id="invalid", type="invalid_type")

        # Should raise validation error for invalid enum value
        self.assertTrue(len(str(context.exception)) > 0)

    def test_compile_workflow_no_start_node(self):
        """Test compilation with no start node."""
        definition = WorkflowDefinition(
            name="test_no_start_workflow",
            nodes=[
                WorkflowNode(
                    id="process", 
                    type=NodeType.PYTHON, 
                    data=PythonNodeData(code_ref="test_function", args={})
                )
            ],
            edges=[]
        )
        
        # Should still compile but use first node as entry point
        graph = self.engine.compile_workflow(definition)
        compiled_graph = graph.compile()
        
        self.assertIsNotNone(compiled_graph)

    def test_compile_workflow_with_multiple_paths(self):
        """Test compilation of workflow with multiple execution paths."""
        definition = WorkflowDefinition(
            name="test_multiple_paths_workflow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(
                    id="process1", 
                    type=NodeType.PYTHON, 
                    data=PythonNodeData(code_ref="process_step1", args={})
                ),
                WorkflowNode(
                    id="condition", 
                    type=NodeType.CONDITION, 
                    data=ConditionNodeData(expr={">=": [{"var": "result"}, 10]})
                ),
                WorkflowNode(
                    id="high_value", 
                    type=NodeType.PYTHON, 
                    data=PythonNodeData(code_ref="handle_high", args={})
                ),
                WorkflowNode(
                    id="low_value", 
                    type=NodeType.PYTHON, 
                    data=PythonNodeData(code_ref="handle_low", args={})
                ),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="process1"),
                WorkflowEdge(source="process1", target="condition"),
                WorkflowEdge(source="condition", target="high_value"),
                WorkflowEdge(source="condition", target="low_value"),
                WorkflowEdge(source="high_value", target="end"),
                WorkflowEdge(source="low_value", target="end")
            ]
        )
        
        # Compile workflow
        graph = self.engine.compile_workflow(definition)
        compiled_graph = graph.compile()
        
        self.assertIsNotNone(compiled_graph)

    def test_compile_workflow_validation_enabled(self):
        """Test compilation with input validation enabled."""
        # Create engine with validation enabled
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            checkpoint_enabled=False,
            validate_inputs=True
        )
        engine_with_validation = WorkflowEngine(config=config)
        
        definition = WorkflowDefinition(
            name="test_validation_workflow",
            nodes=[
                WorkflowNode(id="start", type=NodeType.START),
                WorkflowNode(
                    id="process", 
                    type=NodeType.PYTHON, 
                    data=PythonNodeData(code_ref="safe_function", args={})
                ),
                WorkflowNode(id="end", type=NodeType.END)
            ],
            edges=[
                WorkflowEdge(source="start", target="process"),
                WorkflowEdge(source="process", target="end")
            ]
        )
        
        # Should compile successfully with safe function
        graph = engine_with_validation.compile_workflow(definition)
        compiled_graph = graph.compile()
        
        self.assertIsNotNone(compiled_graph)
        
        # Clean up
        engine_with_validation.db_manager.close()

    def test_compile_empty_workflow(self):
        """Test compilation of empty workflow."""
        definition = WorkflowDefinition(
            name="test_empty_workflow",
            nodes=[],
            edges=[]
        )
        
        # Engine should handle empty workflow gracefully
        # It may either succeed (returning empty graph) or raise an error
        try:
            graph = self.engine.compile_workflow(definition)
            # If it succeeds, graph should be valid
            self.assertIsNotNone(graph)
        except (ValueError, RuntimeError) as e:
            # If it raises an error, that's also acceptable
            self.assertTrue(len(str(e)) > 0)


if __name__ == '__main__':
    unittest.main()