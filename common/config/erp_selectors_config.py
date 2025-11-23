"""
ERP插件选择器配置
统一管理ERP插件相关的选择器配置
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .base_scraping_config import BaseScrapingConfig

@dataclass
class ERPSelectorsConfig(BaseScrapingConfig):
    """ERP插件选择器配置"""
    
    # ========== ERP容器选择器配置 ==========
    erp_container_selectors: List[str] = field(default_factory=lambda: [
        '[data-v-efec3aa9]',  # 从HTML中观察到的特征属性
        '.erp-plugin',
        '[class*="erp"]',
        '[id*="erp"]',
        '[data-widget="erpPlugin"]',
        '[class*="plugin"]'
    ])
    
    # ========== ERP数据选择器配置 ==========
    erp_data_selectors: List[str] = field(default_factory=lambda: [
        '[data-erp-field]',
        '.erp-data',
        '[class*="erp-field"]',
        '[data-field]'
    ])
    
    # ========== ERP状态指示器选择器 ==========
    erp_status_selectors: List[str] = field(default_factory=lambda: [
        '.erp-status',
        '[data-erp-status]',
        '[class*="status"]'
    ])
    
    # ========== ERP加载指示器选择器 ==========
    erp_loading_selectors: List[str] = field(default_factory=lambda: [
        '.erp-loading',
        '[data-erp-loading]',
        '.loading',
        '[class*="loading"]'
    ])

    def get_selector(self, category: str, key: str) -> Optional[str]:
        """
        获取选择器
        
        Args:
            category: 选择器分类
            key: 选择器键名
            
        Returns:
            str: 选择器字符串，如果未找到返回None
        """
        selectors_dict = {
            'erp_container': {f'selector_{i}': sel for i, sel in enumerate(self.erp_container_selectors)},
            'erp_data': {f'selector_{i}': sel for i, sel in enumerate(self.erp_data_selectors)},
            'erp_status': {f'selector_{i}': sel for i, sel in enumerate(self.erp_status_selectors)},
            'erp_loading': {f'selector_{i}': sel for i, sel in enumerate(self.erp_loading_selectors)}
        }
        
        category_selectors = selectors_dict.get(category)
        if category_selectors:
            return category_selectors.get(key)
        return None
    
    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        """
        批量获取选择器
        
        Args:
            category: 选择器分类
            
        Returns:
            Dict[str, str]: 选择器字典，如果未找到返回None
        """
        selectors_dict = {
            'erp_container': {f'selector_{i}': sel for i, sel in enumerate(self.erp_container_selectors)},
            'erp_data': {f'selector_{i}': sel for i, sel in enumerate(self.erp_data_selectors)},
            'erp_status': {f'selector_{i}': sel for i, sel in enumerate(self.erp_status_selectors)},
            'erp_loading': {f'selector_{i}': sel for i, sel in enumerate(self.erp_loading_selectors)}
        }
        
        return selectors_dict.get(category)
    
    def validate(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        # 检查所有选择器列表是否不为空
        if not self.erp_container_selectors:
            return False
        if not self.erp_data_selectors:
            return False
        if not self.erp_status_selectors:
            return False
        if not self.erp_loading_selectors:
            return False
            
        # 检查选择器是否为有效字符串
        all_selectors = (
            self.erp_container_selectors + 
            self.erp_data_selectors + 
            self.erp_status_selectors + 
            self.erp_loading_selectors
        )
        
        for selector in all_selectors:
            if not isinstance(selector, str) or not selector.strip():
                return False
                
        return True

# 全局默认配置实例
DEFAULT_ERP_SELECTORS = ERPSelectorsConfig()

def get_erp_selectors_config():
    """获取ERP选择器配置实例"""
    return DEFAULT_ERP_SELECTORS
