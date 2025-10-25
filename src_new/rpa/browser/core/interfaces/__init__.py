"""
Core Interfaces Module

包含所有核心接口定义
"""



from .browser_driver import IBrowserDriver

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
    
    # 配置管理接口
    'IConfigManager',
    'IConfigValidator',
    'IConfigTransformer',
    'IEnvironmentManager',
    'ConfigFormat',
    'ConfigScope'
]