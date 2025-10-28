"""
配置管理模块

提供统一的配置管理功能，包括：
- 配置管理器
- 组件配置类
- 预设配置
"""

from .config import (
    BrowserServiceConfig,
    PaginatorConfig,
    DOMAnalyzerConfig,
    ConfigManager,
    create_default_browser_service_config,
    create_browser_service_config_from_dict,
    create_config_manager,
    get_headless_config,
    get_debug_config,
    get_fast_config
)

__all__ = [
    'BrowserServiceConfig',
    'PaginatorConfig',
    'DOMAnalyzerConfig',
    'ConfigManager',
    'create_default_browser_service_config',
    'create_browser_service_config_from_dict',
    'create_config_manager',
    'get_headless_config',
    'get_debug_config',
    'get_fast_config'
]