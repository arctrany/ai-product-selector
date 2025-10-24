"""
Core Interfaces Module

包含所有核心接口定义
"""

from .browser_driver import (
    IBrowserDriver,
    IPageManager,
    IResourceManager as IBrowserResourceManager
)

from .page_analyzer import (
    IPageAnalyzer,
    IContentExtractor,
    IElementMatcher,
    IPageValidator
)

from .paginator import (
    IPaginator,
    IDataExtractor,
    IPaginationStrategy,
    IScrollPaginator,
    ILoadMorePaginator,
    PaginationType,
    PaginationDirection
)

from .runner import (
    IRunner,
    IRunnerStep,
    IRunnerOrchestrator,
    IActionExecutor,
    IRunnerValidator,
    RunnerStatus,
    ActionType
)

from .resource_manager import (
    IResourceManager,
    IConnectionPool,
    ICacheManager,
    IMemoryManager,
    IFileManager,
    ResourceType,
    ResourceStatus
)

from .config_manager import (
    IConfigManager,
    IConfigValidator,
    IConfigTransformer,
    IEnvironmentManager,
    ConfigFormat,
    ConfigScope
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
    'ConfigScope'
]