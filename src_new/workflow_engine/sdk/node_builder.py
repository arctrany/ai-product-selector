"""Node builders for different node types."""

import time
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from ..core.models import WorkflowState
from ..utils.logger import WorkflowLogger


class NodeBuilder:
    """Base class for node builders."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
    
    def execute(self, state: WorkflowState, logger: WorkflowLogger, interrupt_fn: Callable) -> Dict[str, Any]:
        """Execute the node logic.
        
        Args:
            state: Current workflow state
            logger: Workflow logger
            interrupt_fn: Function to call for interrupting execution
        
        Returns:
            Updated state data
        """
        raise NotImplementedError("Subclasses must implement execute method")


class CodeNode(NodeBuilder):
    """Builder for code execution nodes with fine-grained control."""
    
    def __init__(self, node_id: str, function: Callable, args: Optional[Dict[str, Any]] = None):
        super().__init__(node_id)
        self.function = function
        self.args = args or {}
    
    def execute(self, state: WorkflowState, logger: WorkflowLogger, interrupt_fn: Callable) -> Dict[str, Any]:
        """Execute the code node with interrupt support.
        
        Args:
            state: Current workflow state
            logger: Workflow logger
            interrupt_fn: Function to call for pausing execution
        
        Returns:
            Updated state data
        """
        logger.info(f"Executing code node: {self.node_id}")
        
        # Check for pause signals
        if state.pause_requested:
            logger.info(f"Pause requested for node: {self.node_id}")
            interrupt_fn(f"Node {self.node_id} paused by request")
            return state.data
        
        try:
            # Execute the function with interrupt capability
            result = self.function(state, logger, interrupt_fn, **self.args)
            
            # Update state data
            if isinstance(result, dict):
                state.data.update(result)
                return result
            else:
                return {"result": result}
                
        except Exception as e:
            logger.error(f"Error in code node {self.node_id}: {str(e)}")
            return {"error": str(e), "node_id": self.node_id}


class BranchNode(NodeBuilder):
    """Builder for branch/condition nodes."""
    
    def __init__(self, node_id: str, condition_fn: Callable):
        super().__init__(node_id)
        self.condition_fn = condition_fn
    
    def execute(self, state: WorkflowState, logger: WorkflowLogger, interrupt_fn: Callable) -> Dict[str, Any]:
        """Execute the branch node logic.
        
        Args:
            state: Current workflow state
            logger: Workflow logger
            interrupt_fn: Function to call for pausing execution
        
        Returns:
            Updated state data with condition result
        """
        logger.info(f"Executing branch node: {self.node_id}")
        
        # Check for pause signals
        if state.pause_requested:
            logger.info(f"Pause requested for node: {self.node_id}")
            interrupt_fn(f"Node {self.node_id} paused by request")
            return state.data
        
        try:
            # Evaluate condition
            condition_result = self.condition_fn(state, logger)
            
            logger.info(f"Branch condition result: {condition_result}", 
                       node_id=self.node_id,
                       context={"condition_result": condition_result})
            
            return {
                "condition_result": condition_result,
                "branch_node": self.node_id
            }
            
        except Exception as e:
            logger.error(f"Error in branch node {self.node_id}: {str(e)}")
            return {"error": str(e), "node_id": self.node_id, "condition_result": False}


# Utility functions for common node patterns

def create_loop_node(node_id: str, iterations: int, interval_seconds: float = 0) -> CodeNode:
    """Create a loop node that executes for a specified number of iterations.
    
    Args:
        node_id: Node identifier
        iterations: Number of iterations to perform
        interval_seconds: Seconds to wait between iterations
    
    Returns:
        Configured CodeNode
    """
    def loop_function(state: WorkflowState, logger: WorkflowLogger, interrupt_fn: Callable) -> Dict[str, Any]:
        loop_count = state.data.get(f"{node_id}_count", 0)
        
        for i in range(loop_count, iterations):
            # Check for pause before each iteration
            if state.pause_requested:
                logger.info(f"Loop paused at iteration {i}")
                interrupt_fn(f"Loop node {node_id} paused at iteration {i}", 
                           update={f"{node_id}_count": i})
                return {f"{node_id}_count": i}
            
            # Execute iteration
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Loop iteration {i+1}/{iterations} - Current time: {current_time}",
                       node_id=node_id,
                       context={"iteration": i+1, "total": iterations, "time": current_time})
            
            # Wait between iterations (except for the last one)
            if i < iterations - 1 and interval_seconds > 0:
                time.sleep(interval_seconds)
        
        logger.info(f"Loop completed: {iterations} iterations", node_id=node_id)
        return {f"{node_id}_completed": True, f"{node_id}_count": iterations}
    
    return CodeNode(node_id, loop_function)


def create_delay_node(node_id: str, delay_seconds: float, message: str = "done") -> CodeNode:
    """Create a delay node that waits for a specified time then logs a message.
    
    Args:
        node_id: Node identifier
        delay_seconds: Seconds to delay
        message: Message to log after delay
    
    Returns:
        Configured CodeNode
    """
    def delay_function(state: WorkflowState, logger: WorkflowLogger, interrupt_fn: Callable) -> Dict[str, Any]:
        start_time = state.data.get(f"{node_id}_start_time")
        
        if not start_time:
            # First execution - start the delay
            start_time = time.time()
            logger.info(f"Starting delay of {delay_seconds} seconds", node_id=node_id)
            
            # Check for pause during delay
            elapsed = 0
            while elapsed < delay_seconds:
                if state.pause_requested:
                    logger.info(f"Delay paused after {elapsed:.1f} seconds")
                    interrupt_fn(f"Delay node {node_id} paused", 
                               update={f"{node_id}_start_time": start_time, f"{node_id}_elapsed": elapsed})
                    return {f"{node_id}_start_time": start_time, f"{node_id}_elapsed": elapsed}
                
                time.sleep(min(0.1, delay_seconds - elapsed))  # Check every 100ms
                elapsed = time.time() - start_time
        else:
            # Resuming from pause
            elapsed = state.data.get(f"{node_id}_elapsed", 0)
            remaining = delay_seconds - elapsed
            
            logger.info(f"Resuming delay, {remaining:.1f} seconds remaining", node_id=node_id)
            
            while elapsed < delay_seconds:
                if state.pause_requested:
                    logger.info(f"Delay paused again after {elapsed:.1f} seconds")
                    interrupt_fn(f"Delay node {node_id} paused", 
                               update={f"{node_id}_start_time": start_time, f"{node_id}_elapsed": elapsed})
                    return {f"{node_id}_start_time": start_time, f"{node_id}_elapsed": elapsed}
                
                time.sleep(min(0.1, delay_seconds - elapsed))
                elapsed = time.time() - start_time
        
        # Delay completed
        logger.info(f"Delay completed: {message}", node_id=node_id)
        return {f"{node_id}_completed": True, "delay_message": message}
    
    return CodeNode(node_id, delay_function)


def create_simple_branch_node(node_id: str, condition_key: str, expected_value: Any = True) -> BranchNode:
    """Create a simple branch node that checks a state value.
    
    Args:
        node_id: Node identifier
        condition_key: Key in state data to check
        expected_value: Expected value for true condition
    
    Returns:
        Configured BranchNode
    """
    def condition_function(state: WorkflowState, logger: WorkflowLogger) -> bool:
        actual_value = state.data.get(condition_key)
        result = actual_value == expected_value
        
        logger.info(f"Branch condition: {condition_key}={actual_value}, expected={expected_value}, result={result}",
                   node_id=node_id)
        
        return result
    
    return BranchNode(node_id, condition_function)