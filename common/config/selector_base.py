"""
选择器配置基类
提供统一的选择器配置管理接口
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

@dataclass
class BaseSelectorConfig(ABC):
    """选择器配置基类"""
    
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
