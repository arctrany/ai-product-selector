"""
Core Models Module

包含所有核心数据模型
"""

from .browser_config import (
    BrowserConfig,
    ViewportConfig,
    ProxyConfig,
    SecurityConfig,
    PerformanceConfig,
    create_default_config
)

from .page_element import (
    PageElement,
    ElementAttributes,
    ElementBounds,
    ElementState,
    ElementCollection,
    ElementType
)

__all__ = [
    # 浏览器配置模型
    'BrowserConfig',
    'ViewportConfig',
    'ProxyConfig',
    'SecurityConfig',
    'PerformanceConfig',
    'create_default_config',
    
    # 页面元素模型
    'PageElement',
    'ElementAttributes',
    'ElementBounds',
    'ElementState',
    'ElementCollection',
    'ElementType'
]