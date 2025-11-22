"""
ERP插件选择器配置
统一管理ERP插件相关的选择器配置
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ERPSelectorsConfig:
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


# 全局默认配置实例
DEFAULT_ERP_SELECTORS = ERPSelectorsConfig()

def get_erp_selectors_config():
    """获取ERP选择器配置实例"""
    return DEFAULT_ERP_SELECTORS
