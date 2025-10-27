"""
浏览器服务配置系统

提供直观易用的配置管理，包括：
- 浏览器服务配置
- 分页器配置  
- DOM分析器配置
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..models.browser_config import BrowserConfig, BrowserType, ViewportConfig, create_default_config
from ..exceptions.browser_exceptions import ConfigurationError

@dataclass
class PaginatorConfig:
    """分页器配置"""
    # 基础配置
    max_pages: int = 10
    page_timeout: int = 30000
    wait_between_pages: float = 1.0
    
    # 分页检测配置
    pagination_selectors: Dict[str, str] = field(default_factory=lambda: {
        'next_button': 'a[aria-label*="next"], .next, .pagination-next',
        'page_numbers': '.pagination a, .page-numbers a',
        'current_page': '.current, .active, [aria-current="page"]',
        'load_more': '.load-more, .show-more, [data-action="load-more"]'
    })
    
    # 滚动分页配置
    scroll_pause_time: float = 2.0
    scroll_step: int = 1000
    max_scroll_attempts: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'max_pages': self.max_pages,
            'page_timeout': self.page_timeout,
            'wait_between_pages': self.wait_between_pages,
            'pagination_selectors': self.pagination_selectors,
            'scroll_pause_time': self.scroll_pause_time,
            'scroll_step': self.scroll_step,
            'max_scroll_attempts': self.max_scroll_attempts
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'PaginatorConfig':
        """从字典创建配置"""
        return cls(**{k: v for k, v in config_dict.items() if hasattr(cls, k)})

@dataclass
class DOMAnalyzerConfig:
    """DOM分析器配置"""
    # 基础配置
    analysis_timeout: int = 30000
    max_elements: int = 1000
    include_hidden_elements: bool = False
    
    # 元素提取配置
    element_selectors: Dict[str, str] = field(default_factory=lambda: {
        'links': 'a[href]',
        'buttons': 'button, input[type="button"], input[type="submit"]',
        'forms': 'form',
        'images': 'img[src]',
        'text_inputs': 'input[type="text"], input[type="email"], textarea'
    })
    
    # 内容提取配置
    extract_attributes: bool = True
    extract_text_content: bool = True
    extract_computed_styles: bool = False
    
    # 性能配置
    batch_size: int = 50
    use_parallel_processing: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'analysis_timeout': self.analysis_timeout,
            'max_elements': self.max_elements,
            'include_hidden_elements': self.include_hidden_elements,
            'element_selectors': self.element_selectors,
            'extract_attributes': self.extract_attributes,
            'extract_text_content': self.extract_text_content,
            'extract_computed_styles': self.extract_computed_styles,
            'batch_size': self.batch_size,
            'use_parallel_processing': self.use_parallel_processing
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'DOMAnalyzerConfig':
        """从字典创建配置"""
        return cls(**{k: v for k, v in config_dict.items() if hasattr(cls, k)})

@dataclass
class BrowserServiceConfig:
    """浏览器服务配置"""
    # 浏览器配置
    browser_config: BrowserConfig = field(default_factory=create_default_config)
    
    # 组件配置
    paginator_config: PaginatorConfig = field(default_factory=PaginatorConfig)
    dom_analyzer_config: DOMAnalyzerConfig = field(default_factory=DOMAnalyzerConfig)
    
    # 服务配置
    auto_initialize: bool = True
    debug_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'browser_config': self.browser_config.to_dict(),
            'paginator_config': self.paginator_config.to_dict(),
            'dom_analyzer_config': self.dom_analyzer_config.to_dict(),
            'auto_initialize': self.auto_initialize,
            'debug_mode': self.debug_mode
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BrowserServiceConfig':
        """从字典创建配置"""
        browser_config = BrowserConfig.from_dict(config_dict.get('browser_config', {}))
        paginator_config = PaginatorConfig.from_dict(config_dict.get('paginator_config', {}))
        dom_analyzer_config = DOMAnalyzerConfig.from_dict(config_dict.get('dom_analyzer_config', {}))
        
        return cls(
            browser_config=browser_config,
            paginator_config=paginator_config,
            dom_analyzer_config=dom_analyzer_config,
            auto_initialize=config_dict.get('auto_initialize', True),
            debug_mode=config_dict.get('debug_mode', False)
        )
    
    def validate(self) -> list[str]:
        """验证配置"""
        errors = []
        
        # 验证浏览器配置
        browser_errors = self.browser_config.validate()
        errors.extend(browser_errors)
        
        # 验证分页器配置
        if self.paginator_config.max_pages <= 0:
            errors.append("分页器最大页数必须大于0")
        
        if self.paginator_config.page_timeout <= 0:
            errors.append("分页器超时时间必须大于0")
        
        # 验证DOM分析器配置
        if self.dom_analyzer_config.analysis_timeout <= 0:
            errors.append("DOM分析器超时时间必须大于0")
        
        if self.dom_analyzer_config.max_elements <= 0:
            errors.append("DOM分析器最大元素数必须大于0")
        
        return errors

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, debug_mode: bool = False):
        """
        初始化配置管理器
        
        Args:
            debug_mode: 是否启用调试模式
        """
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        self._config: Optional[BrowserServiceConfig] = None
        
        if self.debug_mode:
            self.logger.info("🔧 配置管理器初始化完成")
    
    def load_config(self, config: Optional[Dict[str, Any]] = None) -> BrowserServiceConfig:
        """
        加载配置 - 只支持字典类型
        
        Args:
            config: 配置字典，None时使用默认配置
            
        Returns:
            BrowserServiceConfig: 加载的配置
        """
        try:
            if config is None:
                # 使用默认配置
                self._config = BrowserServiceConfig()
                if self.debug_mode:
                    self.logger.info("✅ 使用默认配置")
            
            elif isinstance(config, dict):
                # 从字典创建配置
                self._config = BrowserServiceConfig.from_dict(config)
                if self.debug_mode:
                    self.logger.info("✅ 从字典创建配置")
            
            else:
                raise ConfigurationError(f"不支持的配置类型: {type(config)}")
            
            # 验证配置
            errors = self._config.validate()
            if errors:
                error_msg = f"配置验证失败: {errors}"
                self.logger.error(error_msg)
                raise ConfigurationError(error_msg)
            
            if self.debug_mode:
                self.logger.info("✅ 配置加载和验证完成")
            
            return self._config
            
        except Exception as e:
            self.logger.error(f"❌ 配置加载失败: {e}")
            raise ConfigurationError(f"配置加载失败: {e}")
    
    def get_config(self) -> Optional[BrowserServiceConfig]:
        """获取当前配置"""
        return self._config
    
    def get_browser_config(self) -> Optional[BrowserConfig]:
        """获取浏览器配置"""
        return self._config.browser_config if self._config else None
    
    def get_paginator_config(self) -> Optional[PaginatorConfig]:
        """获取分页器配置"""
        return self._config.paginator_config if self._config else None
    
    def get_dom_analyzer_config(self) -> Optional[DOMAnalyzerConfig]:
        """获取DOM分析器配置"""
        return self._config.dom_analyzer_config if self._config else None
    
    def update_config(self, key: str, value: Any) -> bool:
        """
        更新配置项
        
        Args:
            key: 配置键 (支持点分隔的嵌套键，如 'browser_config.headless')
            value: 配置值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not self._config:
                self.logger.error("❌ 配置未初始化")
                return False
            
            keys = key.split('.')
            current = self._config
            
            # 导航到目标对象
            for k in keys[:-1]:
                if hasattr(current, k):
                    current = getattr(current, k)
                else:
                    self.logger.error(f"❌ 配置键不存在: {k}")
                    return False
            
            # 设置值
            final_key = keys[-1]
            if hasattr(current, final_key):
                setattr(current, final_key, value)
                
                # 重新验证配置
                errors = self._config.validate()
                if errors:
                    self.logger.warning(f"⚠️ 配置更新后验证警告: {errors}")
                
                if self.debug_mode:
                    self.logger.info(f"✅ 配置更新成功: {key} = {value}")
                
                return True
            else:
                self.logger.error(f"❌ 配置键不存在: {final_key}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 配置更新失败: {key} - {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置信息
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        if not self._config:
            return {'config_loaded': False}
        
        return {
            'config_loaded': True,
            'debug_mode': self._config.debug_mode,
            'auto_initialize': self._config.auto_initialize,
            'browser_type': self._config.browser_config.browser_type.value,
            'headless': self._config.browser_config.headless,
            'viewport': f"{self._config.browser_config.viewport.width}x{self._config.browser_config.viewport.height}",
            'paginator_max_pages': self._config.paginator_config.max_pages,
            'dom_analyzer_max_elements': self._config.dom_analyzer_config.max_elements
        }

# ==================== 工厂函数 ====================

def create_default_browser_service_config(debug_mode: bool = False) -> BrowserServiceConfig:
    """创建默认的浏览器服务配置"""
    return BrowserServiceConfig(debug_mode=debug_mode)

def create_browser_service_config_from_dict(config_dict: Dict[str, Any]) -> BrowserServiceConfig:
    """从字典创建浏览器服务配置"""
    return BrowserServiceConfig.from_dict(config_dict)

def create_config_manager(debug_mode: bool = False) -> ConfigManager:
    """创建配置管理器"""
    return ConfigManager(debug_mode=debug_mode)

# ==================== 预设配置 ====================

def get_headless_config() -> BrowserServiceConfig:
    """获取无头浏览器配置"""
    config = create_default_browser_service_config()
    config.browser_config.headless = True
    return config

def get_debug_config() -> BrowserServiceConfig:
    """获取调试配置"""
    config = create_default_browser_service_config(debug_mode=True)
    config.browser_config.headless = False
    config.browser_config.devtools = True
    return config

def get_fast_config() -> BrowserServiceConfig:
    """获取快速配置（适合批量处理）"""
    config = create_default_browser_service_config()
    config.browser_config.headless = True
    config.paginator_config.wait_between_pages = 0.5
    config.dom_analyzer_config.max_elements = 500
    return config