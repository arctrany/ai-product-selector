"""Python node implementation."""

from typing import Any, Dict, Optional

from ..core.models import WorkflowState
from ..core.registry import get_registered_function
from ..utils.logger import WorkflowLogger
from .base import BaseNode


class PythonNode(BaseNode):
    """Node that executes registered Python functions."""
    
    def execute(self, state: WorkflowState, logger: WorkflowLogger, 
                interrupt: Optional[callable] = None) -> Dict[str, Any]:
        """Execute registered Python function."""
        
        code_ref = self.node_data.get("code_ref")
        if not code_ref:
            raise ValueError(f"Python node {self.node_id} missing code_ref")
        
        # Get registered function
        func = get_registered_function(code_ref)
        if not func:
            raise ValueError(f"Function not found: {code_ref}")
        
        logger.info(f"Executing Python function: {code_ref}", node_id=self.node_id)
        
        try:
            # Prepare function arguments
            func_args = self.node_data.get("args", {})
            
            # Convert state to dict for function call
            state_dict = {
                "thread_id": state.thread_id,
                "current_node": state.current_node,
                "data": state.data,
                "metadata": state.metadata,
                "pause_requested": state.pause_requested,
                "cancel_requested": state.cancel_requested
            }
            
            # Call function with correct arguments
            result = func(state, logger, interrupt, **func_args)
            
            logger.info(f"Python function completed: {code_ref}", 
                       node_id=self.node_id, 
                       context={"result_keys": list(result.keys()) if isinstance(result, dict) else None})
            
            # Return result to merge into state
            if isinstance(result, dict):
                return result
            else:
                return {"result": result}
                
        except Exception as e:
            logger.error(f"Python function failed: {code_ref} - {str(e)}", 
                        node_id=self.node_id,
                        context={"error": str(e), "error_type": type(e).__name__})
            raise