"""Core data models for workflow engine."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Annotated
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class NodeType(str, Enum):
    """Supported node types."""
    START = "start"
    END = "end"
    PYTHON = "python"
    CONDITION = "condition"


class RunStatus(str, Enum):
    """Workflow run status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SignalType(str, Enum):
    """Signal types for workflow control."""
    PAUSE_REQUEST = "pause_request"
    RESUME_REQUEST = "resume_request"
    CANCEL_REQUEST = "cancel_request"


class NodeData(BaseModel):
    """Base node data model."""
    pass


class PythonNodeData(NodeData):
    """Python node configuration."""
    code_ref: str = Field(..., description="Reference to registered function")
    args: Dict[str, Any] = Field(default_factory=dict, description="Function arguments")


class ConditionNodeData(NodeData):
    """Condition node configuration."""
    expr: Dict[str, Any] = Field(..., description="JSONLogic expression")


class EdgeData(BaseModel):
    """Edge configuration."""
    when: Optional[Union[bool, Dict[str, Any]]] = Field(None, description="Condition for edge traversal")


class WorkflowNode(BaseModel):
    """Workflow node definition."""
    id: str = Field(..., description="Unique node identifier")
    type: NodeType = Field(..., description="Node type")
    data: Optional[Union[PythonNodeData, ConditionNodeData]] = Field(None, description="Node-specific data")


class WorkflowEdge(BaseModel):
    """Workflow edge definition."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    data: Optional[EdgeData] = Field(None, description="Edge-specific data")


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""
    name: str = Field(..., description="Workflow name")
    nodes: List[WorkflowNode] = Field(..., description="Workflow nodes")
    edges: List[WorkflowEdge] = Field(..., description="Workflow edges")


def replace_current_node(left: Optional[str], right: Optional[str]) -> Optional[str]:
    """Replace function for current_node to handle concurrent updates."""
    return right if right is not None else left

class WorkflowState(BaseModel):
    """Workflow execution state."""
    thread_id: str = Field(..., description="Unique thread identifier")
    current_node: Annotated[Optional[str], replace_current_node] = Field(None, description="Currently executing node")
    data: Dict[str, Any] = Field(default_factory=dict, description="Workflow data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
    pause_requested: bool = Field(False, description="Pause request flag")
    cancel_requested: bool = Field(False, description="Cancel request flag")


class FlowVersion(BaseModel):
    """Flow version model."""
    id: Optional[int] = None
    flow_id: int
    version: str
    dsl_json: Dict[str, Any]
    compiled_meta: Optional[Dict[str, Any]] = None
    published: bool = False
    created_at: Optional[datetime] = None


class FlowRun(BaseModel):
    """Flow run model."""
    thread_id: str
    flow_version_id: int
    status: RunStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Signal(BaseModel):
    """Control signal model."""
    id: Optional[int] = None
    thread_id: str
    type: SignalType
    payload_json: Dict[str, Any] = Field(default_factory=dict)
    ts: Optional[datetime] = None
    processed: bool = False


class LogEntry(BaseModel):
    """Log entry model."""
    ts: datetime
    level: str
    thread_id: str
    node_id: Optional[str] = None
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)