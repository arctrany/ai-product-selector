"""Function registry for workflow nodes."""

import inspect
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional
from functools import wraps

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Global function registry
_FUNCTION_REGISTRY: Dict[str, Callable] = {}


def register_function(code_ref: str, func: Optional[Callable] = None):
    """
    Register a function for use in workflow nodes.

    Can be used as decorator or direct function call.

    Args:
        code_ref: Unique reference identifier for the function
        func: Function to register (if not used as decorator)

    Example:
        @register_function("data.scrape_products")
        def scrape_products(state, **kwargs):
            return {"products": [...]}

        # Or direct registration:
        register_function("my.function", my_function)
    """
    def decorator(f: Callable) -> Callable:
        # Validate function signature
        sig = inspect.signature(f)
        params = list(sig.parameters.keys())

        if not params or params[0] != 'state':
            raise ValueError(f"Function {f.__name__} must have 'state' as first parameter")

        # Register the function
        _FUNCTION_REGISTRY[code_ref] = f
        logger.info(f"Registered function: {code_ref} -> {f.__name__}")

        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    if func is not None:
        # Direct registration
        return decorator(func)
    else:
        # Decorator usage
        return decorator


def get_registered_function(code_ref: str) -> Optional[Callable]:
    """Get a registered function by its code reference."""
    return _FUNCTION_REGISTRY.get(code_ref)


def list_registered_functions() -> List[str]:
    """List all registered function references."""
    return list(_FUNCTION_REGISTRY.keys())


def install_dependencies(requirements: List[str]) -> bool:
    """
    Install Python dependencies for registered functions.
    
    Args:
        requirements: List of package requirements (e.g., ["requests>=2.25.0"])
        
    Returns:
        True if installation successful, False otherwise
    """
    if not requirements:
        return True
    
    try:
        logger.info(f"Installing dependencies: {requirements}")
        
        for requirement in requirements:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", requirement],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Installed {requirement}: {result.stdout.strip()}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error installing dependencies: {e}")
        return False


def validate_function_dependencies(code_ref: str) -> List[str]:
    """
    Analyze function dependencies and return missing packages.
    
    This is a simplified implementation that could be enhanced
    to parse import statements and check installed packages.
    """
    func = get_registered_function(code_ref)
    if not func:
        return []
    
    # For MVP, we'll return empty list
    # In production, this could analyze the function's source code
    # to detect import statements and check if packages are installed
    return []


# Example registered functions for testing
@register_function("test.hello_world")
def hello_world(state, name: str = "World", **kwargs):
    """Simple test function."""
    message = f"Hello, {name}!"
    logger.info(f"Executing hello_world: {message}")
    return {"message": message, "timestamp": "2025-10-22T15:53:00Z"}


@register_function("test.add_numbers")
def add_numbers(state, a: int, b: int, **kwargs):
    """Add two numbers."""
    result = a + b
    logger.info(f"Adding {a} + {b} = {result}")
    return {"result": result, "operation": "addition"}


@register_function("test.process_data")
def process_data(state, items: List[Any], batch_size: int = 10, **kwargs):
    """Process data in batches with pause support."""
    interrupt = kwargs.get('interrupt')
    processed = state.get('processed_count', 0)
    total = len(items)
    
    logger.info(f"Processing {total} items, starting from {processed}")
    
    while processed < total:
        # Process batch
        batch_end = min(processed + batch_size, total)
        batch = items[processed:batch_end]
        
        # Simulate processing
        for item in batch:
            processed += 1
            
            # Check for pause request
            if state.get('pause_requested', False):
                logger.info(f"Pause requested at item {processed}")
                if interrupt:
                    interrupt(
                        value={"reason": "pause_requested", "processed": processed},
                        update={"processed_count": processed}
                    )
                break
        
        # Checkpoint every batch
        if interrupt and processed % (batch_size * 2) == 0:
            logger.info(f"Checkpoint at {processed}/{total}")
            interrupt(
                value={"checkpoint": processed},
                update={"processed_count": processed}
            )
    
    logger.info(f"Completed processing {processed}/{total} items")
    return {
        "processed_count": processed,
        "total_count": total,
        "completed": processed >= total
    }