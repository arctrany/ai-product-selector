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
    # 性能优化：重新排序选择器，按实际命中率和性能排序
    erp_container_selectors: List[str] = field(default_factory=lambda: [
        '.mz-widget-product',                        # 🚀 实际组件类名 - 最可能存在，排第一
        'div[data-widget]',                          # 🚀 OZON通用data-widget - 第二选择
        'div[data-widget*="web"]',                   # 🚀 Web组件变体 - 第三选择
        '[data-v-efec3aa9]'                          # ⚠️ Vue组件 - 可能不稳定，排最后
        # 🚫 完全移除无效选择器以提升性能：
        # '#custom-insertion-point'                  # 已确认不存在，移除避免浪费时间
        # 移除其他低效选择器：
        # '[class*="mz-widget"]', '#custom-insertion-point [data-v-efec3aa9]',
        # '.mz-widget-product [data-v-efec3aa9]'
    ])
    
    # ========== ERP数据选择器配置 ==========
    erp_data_selectors: List[str] = field(default_factory=lambda: [
        '[data-erp-field]',                          # 原有选择器
        '.erp-data',                                  # 原有选择器
        '[class*="erp-field"]',                       # 原有选择器
        '[data-field]',                               # 原有选择器
        'span',                                       # 基于OZON实际DOM结构：大部分数据在span中
        'div',                                        # 基于OZON实际DOM结构：容器div
        '[data-testid]'                               # 基于OZON实际使用的testid模式
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
