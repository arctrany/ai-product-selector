"""
浏览器RPA模块实现层

本模块包含所有接口的具体实现：
- PlaywrightBrowserDriver: Playwright浏览器驱动实现
- DOMPageAnalyzer: DOM页面分析器实现
- UniversalPaginator: 通用分页器实现
- ConfigManager: 配置管理器实现
- EnvironmentManager: 环境变量管理器实现
- StructuredLogger: 结构化日志记录器实现
- LoggerSystem: 日志系统管理器实现
"""

from .playwright_browser_driver import PlaywrightBrowserDriver
from .dom_page_analyzer import DOMPageAnalyzer, DOMContentExtractor, DOMElementMatcher, DOMPageValidator
from .universal_paginator import UniversalPaginator, UniversalDataExtractor, SequentialPaginationStrategy
from .config_manager import ConfigManager, EnvironmentManager
from .logger_system import (
    StructuredLogger,
    LoggerSystem,
    PerformanceLogger,
    get_logger_system,
    get_logger,
    set_debug_mode
)

__all__ = [
    # 浏览器驱动
    'PlaywrightBrowserDriver',

    # DOM分析器
    'DOMPageAnalyzer',
    'DOMContentExtractor',
    'DOMElementMatcher',
    'DOMPageValidator',

    # 分页器
    'UniversalPaginator',
    'UniversalDataExtractor',
    'SequentialPaginationStrategy',

    # 配置管理
    'ConfigManager',
    'EnvironmentManager',

    # 日志系统
    'StructuredLogger',
    'LoggerSystem',
    'PerformanceLogger',
    'get_logger_system',
    'get_logger',
    'set_debug_mode'
]