"""
Core Exceptions Module

包含所有核心异常类型
"""

from .browser_exceptions import (
    BrowserError,
    BrowserInitializationError,
    BrowserConnectionError,
    BrowserTimeoutError,
    PageLoadError,
    ElementNotFoundError,
    ElementInteractionError,
    NavigationError,
    ResourceError,
    ConfigurationError,
    ValidationError,
    ScenarioExecutionError,
    PaginationError,
    create_browser_error,
    handle_browser_error
)

__all__ = [
    'BrowserError',
    'BrowserInitializationError',
    'BrowserConnectionError',
    'BrowserTimeoutError',
    'PageLoadError',
    'ElementNotFoundError',
    'ElementInteractionError',
    'NavigationError',
    'ResourceError',
    'ConfigurationError',
    'ValidationError',
    'ScenarioExecutionError',
    'PaginationError',
    'create_browser_error',
    'handle_browser_error'
]