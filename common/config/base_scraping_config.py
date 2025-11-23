"""
抓取配置基类

提供统一的配置管理接口，所有Scraper配置继承此基类。
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


@dataclass
class BaseScrapingConfig(ABC):
    """
    抓取配置基类
    
    所有Scraper配置类应继承此基类并实现抽象方法
    """
    
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
    
    def get_timeout(self, operation: str, default: int = 30000) -> int:
        """
        获取操作超时时间
        
        Args:
            operation: 操作名称
            default: 默认超时时间（毫秒）
            
        Returns:
            int: 超时时间（毫秒）
        """
        timeouts = getattr(self, 'timeouts', {})
        return timeouts.get(operation, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict: 配置字典
        """
        return self.__dict__.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseScrapingConfig':
        """
        从字典创建配置实例
        
        Args:
            data: 配置字典
            
        Returns:
            BaseScrapingConfig: 配置实例
        """
        return cls(**data)


@dataclass
class BaseTimeoutConfig:
    """基础超时配置"""
    page_load: int = 30000
    element_wait: int = 15000
    network_idle: int = 5000
    data_extraction: int = 60000
    total_operation: int = 600000
    
    def to_dict(self) -> Dict[str, int]:
        """转换为字典"""
        return {
            'page_load': self.page_load,
            'element_wait': self.element_wait,
            'network_idle': self.network_idle,
            'data_extraction': self.data_extraction,
            'total_operation': self.total_operation
        }
