"""
配置模块

统一导出所有配置相关的类和函数，支持模块化配置管理
"""

# 新的模块化配置
from .base_config import (
    GoodStoreSelectorConfig,
    get_config,
    set_config,
    load_config,
    create_default_config_file
)

from .browser_config import (
    BrowserConfig,
    ScrapingConfig  # 向后兼容
)

from .business_config import (
    SelectorFilterConfig,
    PriceCalculationConfig,
    ExcelConfig
)

from .system_config import (
    LoggingConfig,
    PerformanceConfig
)

# 原有的选择器配置（保持兼容）
from .timeout_config import TimeoutConfig, RetryConfig, TimingConfig
from .base_scraping_config import BaseScrapingConfig
from .ozon_selectors_config import get_ozon_selectors_config, OzonSelectorsConfig
from .seerfar_selectors import get_seerfar_selectors
from .erp_selectors_config import get_erp_selectors_config
from .currency_config import get_currency_config
from .language_config import get_language_config

__all__ = [
    # 新的模块化配置
    'GoodStoreSelectorConfig',
    'get_config',
    'set_config', 
    'load_config',
    'create_default_config_file',
    # 配置类
    'BrowserConfig',
    'ScrapingConfig',
    'SelectorFilterConfig',
    'PriceCalculationConfig',
    'ExcelConfig',
    'LoggingConfig',
    'PerformanceConfig',
    # 原有的选择器配置（保持兼容）
    'TimeoutConfig',
    'RetryConfig',
    'TimingConfig',
    'BaseScrapingConfig',
    'get_ozon_selectors_config',
    'OzonSelectorsConfig',
    'get_seerfar_selectors',
    'get_erp_selectors_config',
    'get_currency_config',
    'get_language_config',
]
