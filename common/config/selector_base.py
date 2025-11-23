"""
选择器配置基类
提供统一的选择器配置管理接口

此基类已被 BaseScrapingConfig 替代，保留用于向后兼容。
新代码应使用 common.config.base_scraping_config.BaseScrapingConfig
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import warnings

@dataclass
class BaseSelectorConfig(ABC):
    """
    选择器配置基类
    
    ⚠️ 已废弃：此类已被 BaseScrapingConfig 替代
    新代码应使用 common.config.base_scraping_config.BaseScrapingConfig
    """
    
    def __post_init__(self):
        """发出废弃警告"""
        warnings.warn(
            "BaseSelectorConfig is deprecated. Use BaseScrapingConfig instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    @abstractmethod
    def get_selector(self, category: str, key: str) -> Optional[str]:
        """
        获取选择器
        
        Args:
            category: 选择器分类
            key: 选择器键名
            
        Returns:
            str: 选择器字符串，如果未找到返回None
        """
        pass

    @abstractmethod
    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        """
        批量获取选择器
        
        Args:
            category: 选择器分类
            
        Returns:
            Dict[str, str]: 选择器字典，如果未找到返回None
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        pass
