"""Workflow builder for programmatic workflow definition."""

import uuid
from typing import Any, Dict, List, Optional, Callable
from ..core.models import WorkflowDefinition, WorkflowNode, WorkflowEdge, NodeType, PythonNodeData, ConditionNodeData


class WorkflowBuilder:
    """Builder class for creating workflows programmatically."""
    
    def __init__(self, name: str):
        self.name = name
        self.nodes: List[WorkflowNode] = []
        self.edges: List[WorkflowEdge] = []
        self._node_registry: Dict[str, WorkflowNode] = {}
    
    def add_code_node(self, node_id: str, function_ref: str, args: Optional[Dict[str, Any]] = None) -> 'WorkflowBuilder':
        """Add a code execution node to the workflow.
        
        Args:
            node_id: Unique identifier for the node
            function_ref: Reference to the registered function
            args: Arguments to pass to the function
        
        Returns:
            Self for method chaining
        """
        node_data = PythonNodeData(
            code_ref=function_ref,
            args=args or {}
        )
        
        node = WorkflowNode(
            id=node_id,
            type=NodeType.PYTHON,
            data=node_data
        )
        
        self.nodes.append(node)
        self._node_registry[node_id] = node
        return self
    
    def add_branch_node(self, node_id: str, condition: Dict[str, Any]) -> 'WorkflowBuilder':
        """Add a branch/condition node to the workflow.
        
        Args:
            node_id: Unique identifier for the node
            condition: JSONLogic condition expression
        
        Returns:
            Self for method chaining
        """
        node_data = ConditionNodeData(expr=condition)
        
        node = WorkflowNode(
            id=node_id,
            type=NodeType.CONDITION,
            data=node_data
        )
        
        self.nodes.append(node)
        self._node_registry[node_id] = node
        return self
    
    def add_edge(self, from_node: str, to_node: str, condition: Optional[Dict[str, Any]] = None) -> 'WorkflowBuilder':
        """Add an edge between two nodes.
        
        Args:
            from_node: Source node ID
            to_node: Target node ID
            condition: Optional condition for conditional edges
        
        Returns:
            Self for method chaining
        """
        edge_data = None
        if condition is not None:
            from ..core.models import EdgeData
            edge_data = EdgeData(when=condition)
        
        edge = WorkflowEdge(
            source=from_node,
            target=to_node,
            data=edge_data
        )
        
        self.edges.append(edge)
        return self
    
    def add_start_node(self, node_id: str = "start") -> 'WorkflowBuilder':
        """Add a start node to the workflow.
        
        Args:
            node_id: Node identifier (default: "start")
        
        Returns:
            Self for method chaining
        """
        node = WorkflowNode(
            id=node_id,
            type=NodeType.START
        )
        
        self.nodes.append(node)
        self._node_registry[node_id] = node
        return self
    
    def add_end_node(self, node_id: str = "end") -> 'WorkflowBuilder':
        """Add an end node to the workflow.
        
        Args:
            node_id: Node identifier (default: "end")
        
        Returns:
            Self for method chaining
        """
        node = WorkflowNode(
            id=node_id,
            type=NodeType.END
        )
        
        self.nodes.append(node)
        self._node_registry[node_id] = node
        return self
    
    def build(self) -> WorkflowDefinition:
        """Build and return the workflow definition.
        
        Returns:
            Complete workflow definition
        """
        return WorkflowDefinition(
            name=self.name,
            nodes=self.nodes,
            edges=self.edges
        )
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by its ID.
        
        Args:
            node_id: Node identifier
        
        Returns:
            Node if found, None otherwise
        """
        return self._node_registry.get(node_id)
    
    def validate(self) -> List[str]:
        """Validate the workflow definition.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for start node
        start_nodes = [n for n in self.nodes if n.type == NodeType.START]
        if not start_nodes:
            errors.append("Workflow must have at least one start node")
        elif len(start_nodes) > 1:
            errors.append("Workflow can only have one start node")
        
        # Check for end node
        end_nodes = [n for n in self.nodes if n.type == NodeType.END]
        if not end_nodes:
            errors.append("Workflow must have at least one end node")
        
        # Check edge references
        node_ids = {n.id for n in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge references unknown source node: {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"Edge references unknown target node: {edge.target}")
        
        return errors