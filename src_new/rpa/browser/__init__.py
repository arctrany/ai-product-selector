"""
RPA Browser Module

浏览器自动化模块的主入口
提供完整的浏览器自动化功能
"""

# 导入核心模块
from .core import *

# 导入实现模块
from .implementations import *

# 导入服务模块（将在后续阶段实现）
# from .services import *

# 导入工具模块（将在后续阶段实现）
# from .utils import *

__version__ = "1.0.0"
__author__ = "RPA Browser Team"

__all__ = [
    # 从核心模块导出的所有内容
    # 浏览器驱动接口
    'IBrowserDriver',
    'IPageManager',
    'IBrowserResourceManager',
    
    # 实现类
    'PlaywrightBrowserDriver',

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