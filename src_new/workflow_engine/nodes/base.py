"""Base node implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..core.models import WorkflowState
from ..utils.logger import WorkflowLogger


class BaseNode(ABC):
    """Base class for all workflow nodes."""
    
    def __init__(self, node_id: str, node_data: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.node_data = node_data or {}
    
    @abstractmethod
    def execute(self, state: WorkflowState, logger: WorkflowLogger, 
                interrupt: Optional[callable] = None) -> Dict[str, Any]:
        """
        Execute the node logic.
        
        Args:
            state: Current workflow state
            logger: Workflow logger instance
            interrupt: Function to call for pausing/checkpointing
            
        Returns:
            Dictionary with execution results to merge into state
        """
        pass
    
    def should_interrupt(self, state: WorkflowState) -> bool:
        """Check if node should interrupt execution."""
        return state.pause_requested or state.cancel_requested