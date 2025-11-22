"""
RPA Browser Module

浏览器自动化模块的主入口
提供完整的浏览器自动化功能
"""

# 导入接口
from .core.interfaces.browser_driver import IBrowserDriver

# 导入主要服务类
from .browser_service import (
    SimplifiedBrowserService,
    create_simplified_browser_service,
    create_shared_browser_service,
    create_headless_browser_service,
    create_debug_browser_service
)

# 导入实现类
from .implementations.playwright_browser_driver import PlaywrightBrowserDriver
# ConfigManager removed - using simplified config system
from .implementations.logger_system import get_logger

# 导入核心数据模型和异常（仅导入存在的）
from .core.models.browser_config import (
    BrowserConfig,
    ViewportConfig,
    ProxyConfig,
    SecurityConfig,
    PerformanceConfig,
    create_default_config
)

from .core.exceptions.browser_exceptions import (
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

__version__ = "1.0.0"
__author__ = "RPA Browser Team"

__all__ = [
    # 接口
    'IBrowserDriver',

    # 主要服务类
    'SimplifiedBrowserService',
    'create_simplified_browser_service',
    'create_shared_browser_service',
    'create_headless_browser_service',
    'create_debug_browser_service',

    # 实现类
    'PlaywrightBrowserDriver',
    'get_logger',

    # 数据模型
    'BrowserConfig',
    'ViewportConfig',
    'ProxyConfig',
    'SecurityConfig',
    'PerformanceConfig',
    'create_default_config',
    
    # 异常类型
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