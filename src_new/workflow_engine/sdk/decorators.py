"""Decorators for workflow function registration and node definition."""

import functools
from typing import Any, Callable, Dict, Optional
from ..core.registry import register_function


def workflow_function(name: Optional[str] = None):
    """Decorator to register a function for use in workflows.
    
    Args:
        name: Optional name for the function (defaults to function name)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        function_name = name or func.__name__
        register_function(function_name, func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Add metadata to the function
        wrapper._workflow_function = True
        wrapper._workflow_name = function_name
        
        return wrapper
    
    return decorator


def code_node(node_id: str, args: Optional[Dict[str, Any]] = None):
    """Decorator to mark a function as a code node implementation.
    
    Args:
        node_id: Unique identifier for the node
        args: Optional default arguments for the node
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Add node metadata
        wrapper._is_code_node = True
        wrapper._node_id = node_id
        wrapper._node_args = args or {}
        
        return wrapper
    
    return decorator


def branch_node(node_id: str, condition_key: str, expected_value: Any = True):
    """Decorator to mark a function as a branch node implementation.
    
    Args:
        node_id: Unique identifier for the node
        condition_key: Key in workflow state to evaluate
        expected_value: Expected value for true branch
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Add branch metadata
        wrapper._is_branch_node = True
        wrapper._node_id = node_id
        wrapper._condition_key = condition_key
        wrapper._expected_value = expected_value
        
        return wrapper
    
    return decorator


def pausable_node(check_interval: float = 0.1):
    """Decorator to make a node function pausable.
    
    Args:
        check_interval: Interval in seconds to check for pause signals
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(state, logger, interrupt_fn, *args, **kwargs):
            # Check for pause before execution
            if hasattr(state, 'pause_requested') and state.pause_requested:
                logger.info(f"Node paused before execution: {func.__name__}")
                interrupt_fn(f"Node {func.__name__} paused by request")
                return state.data
            
            # Execute the original function
            return func(state, logger, interrupt_fn, *args, **kwargs)
        
        # Add pausable metadata
        wrapper._is_pausable = True
        wrapper._check_interval = check_interval
        
        return wrapper
    
    return decorator


def interruptible(check_points: Optional[list] = None):
    """Decorator to make a function interruptible at specific points.
    
    Args:
        check_points: List of checkpoint names where interruption can occur
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Add interrupt checking capability
            if len(args) >= 3 and callable(args[2]):  # interrupt_fn is 3rd argument
                interrupt_fn = args[2]
                
                # Create checkpoint function
                def checkpoint(name: str = "default"):
                    if hasattr(args[0], 'pause_requested') and args[0].pause_requested:
                        interrupt_fn(f"Interrupted at checkpoint: {name}")
                
                # Add checkpoint to kwargs
                kwargs['checkpoint'] = checkpoint
            
            return func(*args, **kwargs)
        
        # Add interruptible metadata
        wrapper._is_interruptible = True
        wrapper._check_points = check_points or []
        
        return wrapper
    
    return decorator