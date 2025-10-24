"""
RPA Browser Core Module

核心模块，包含所有接口定义、数据模型、异常类型等基础组件
"""

# 导入所有核心接口
from .interfaces.browser_driver import (
    IBrowserDriver,
    IPageManager,
    IResourceManager as IBrowserResourceManager
)

from .interfaces.page_analyzer import (
    IPageAnalyzer,
    IContentExtractor,
    IElementMatcher,
    IPageValidator
)

from .interfaces.paginator import (
    IPaginator,
    IDataExtractor,
    IPaginationStrategy,
    IScrollPaginator,
    ILoadMorePaginator,
    PaginationType,
    PaginationDirection
)

from .interfaces.runner import (
    IRunner,
    IRunnerStep,
    IRunnerOrchestrator,
    IActionExecutor,
    IRunnerValidator,
    RunnerStatus,
    ActionType
)

from .interfaces.resource_manager import (
    IResourceManager,
    IConnectionPool,
    ICacheManager,
    IMemoryManager,
    IFileManager,
    ResourceType,
    ResourceStatus
)

from .interfaces.config_manager import (
    IConfigManager,
    IConfigValidator,
    IConfigTransformer,
    IEnvironmentManager,
    ConfigFormat,
    ConfigScope
)

# 导入所有数据模型
from .models.browser_config import (
    BrowserConfig,
    ViewportConfig,
    ProxyConfig,
    SecurityConfig,
    PerformanceConfig,
    create_default_config
)

from .models.page_element import (
    PageElement,
    ElementAttributes,
    ElementBounds,
    ElementState,
    ElementCollection,
    ElementType
)

# 导入所有异常类型
from .exceptions.browser_exceptions import (
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
    # 浏览器驱动接口
    'IBrowserDriver',
    'IPageManager',
    'IBrowserResourceManager',
    
    # 页面分析接口
    'IPageAnalyzer',
    'IContentExtractor',
    'IElementMatcher',
    'IPageValidator',
    
    # 分页器接口
    'IPaginator',
    'IDataExtractor',
    'IPaginationStrategy',
    'IScrollPaginator',
    'ILoadMorePaginator',
    'PaginationType',
    'PaginationDirection',
    
    # 运行器接口
    'IRunner',
    'IRunnerStep',
    'IRunnerOrchestrator',
    'IActionExecutor',
    'IRunnerValidator',
    'RunnerStatus',
    'ActionType',
    
    # 资源管理接口
    'IResourceManager',
    'IConnectionPool',
    'ICacheManager',
    'IMemoryManager',
    'IFileManager',
    'ResourceType',
    'ResourceStatus',
    
    # 配置管理接口
    'IConfigManager',
    'IConfigValidator',
    'IConfigTransformer',
    'IEnvironmentManager',
    'ConfigFormat',
    'ConfigScope',
    
    # 数据模型
    'BrowserConfig',
    'ViewportConfig',
    'ProxyConfig',
    'SecurityConfig',
    'PerformanceConfig',
    'create_default_config',
    'PageElement',
    'ElementAttributes',
    'ElementBounds',
    'ElementState',
    'ElementCollection',
    'ElementType',
    
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