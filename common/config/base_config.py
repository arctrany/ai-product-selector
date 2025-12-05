"""
基础配置模块

定义配置系统的基础类和工具函数
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field

from .browser_config import BrowserConfig
from .business_config import (
    SelectorFilterConfig,
    PriceCalculationConfig,
    ExcelConfig
)
from .system_config import (
    LoggingConfig,
    PerformanceConfig
)


@dataclass
class GoodStoreSelectorConfig:
    """好店筛选系统主配置"""
    selector_filter: SelectorFilterConfig = field(default_factory=SelectorFilterConfig)
    price_calculation: PriceCalculationConfig = field(default_factory=PriceCalculationConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)  # 统一使用browser字段
    excel: ExcelConfig = field(default_factory=ExcelConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # 全局配置
    debug_mode: bool = False
    dryrun: bool = False  # 试运行模式，执行抓取但不写入文件，不调用1688接口
    selection_mode: str = 'select-shops'  # 选择模式：'select-goods' 或 'select-shops'（默认）
    product_excel_path: Optional[str] = None  # 商品输出Excel路径（select-goods模式使用）

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GoodStoreSelectorConfig':
        """从字典创建配置对象"""
        config = cls()
        
        # 向后兼容：支持旧的 store_filter 配置
        filter_config_key = 'selector_filter' if 'selector_filter' in config_dict else 'store_filter'

        if filter_config_key in config_dict:
            filter_config = config_dict[filter_config_key]

            # 字段名映射（旧名 -> 新名）
            field_mapping = {
                'min_sales_30days': 'store_min_sales_30days',
                'min_orders_30days': 'store_min_orders_30days',
                'blacklisted_categories': 'item_category_blacklist'
            }

            for key, value in filter_config.items():
                # 使用映射后的字段名
                new_key = field_mapping.get(key, key)
                if hasattr(config.selector_filter, new_key):
                    setattr(config.selector_filter, new_key, value)
                elif hasattr(config.selector_filter, key):
                    # 如果新字段名不存在，尝试使用原字段名
                    setattr(config.selector_filter, key, value)

            # 如果使用了旧配置，显示警告
            if filter_config_key == 'store_filter':
                logging.warning("配置文件使用了已废弃的 'store_filter' 字段，请更新为 'selector_filter'")
        
        if 'price_calculation' in config_dict:
            for key, value in config_dict['price_calculation'].items():
                if hasattr(config.price_calculation, key):
                    setattr(config.price_calculation, key, value)
        
        # 浏览器配置：优先使用 browser，向后兼容 scraping
        browser_config_loaded = False
        if 'browser' in config_dict:
            # 使用新的 browser 配置
            for key, value in config_dict['browser'].items():
                if hasattr(config.browser, key):
                    setattr(config.browser, key, value)
            browser_config_loaded = True

        if 'scraping' in config_dict:
            if browser_config_loaded:
                # 如果已经加载了 browser 配置，忽略 scraping 配置并输出信息
                logging.info("配置文件同时包含 'browser' 和 'scraping' 字段，优先使用 'browser' 配置")
            else:
                # 使用旧的 scraping 配置（向后兼容）
                logging.warning("⚠️ 警告：'scraping' 配置字段已废弃，请迁移到 'browser' 字段")
                logging.warning("迁移方法：将配置文件中的 'scraping' 改为 'browser'")
                for key, value in config_dict['scraping'].items():
                    if hasattr(config.browser, key):
                        setattr(config.browser, key, value)
        
        if 'excel' in config_dict:
            for key, value in config_dict['excel'].items():
                if hasattr(config.excel, key):
                    setattr(config.excel, key, value)
        
        if 'logging' in config_dict:
            for key, value in config_dict['logging'].items():
                if hasattr(config.logging, key):
                    setattr(config.logging, key, value)
        
        if 'performance' in config_dict:
            for key, value in config_dict['performance'].items():
                if hasattr(config.performance, key):
                    setattr(config.performance, key, value)
        
        # 更新全局配置
        for key in ['debug_mode', 'dryrun', 'selection_mode', 'product_excel_path']:
            if key in config_dict:
                setattr(config, key, config_dict[key])
        
        return config
    
    @classmethod
    def from_json_file(cls, file_path: str) -> 'GoodStoreSelectorConfig':
        """从JSON文件加载配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return cls.from_dict(config_dict)
        except FileNotFoundError:
            logging.warning(f"配置文件 {file_path} 不存在，使用默认配置")
            return cls()
        except json.JSONDecodeError as e:
            logging.error(f"配置文件 {file_path} 格式错误: {e}")
            return cls()
    
    @classmethod
    def from_env(cls) -> 'GoodStoreSelectorConfig':
        """从环境变量加载配置"""
        config = cls()
        
        # 店铺筛选配置
        if os.getenv('MIN_SALES_30DAYS'):
            config.selector_filter.store_min_sales_30days = float(os.getenv('MIN_SALES_30DAYS'))
        if os.getenv('MIN_ORDERS_30DAYS'):
            config.selector_filter.store_min_orders_30days = int(os.getenv('MIN_ORDERS_30DAYS'))
        if os.getenv('PROFIT_RATE_THRESHOLD'):
            config.selector_filter.profit_rate_threshold = float(os.getenv('PROFIT_RATE_THRESHOLD'))

        # 价格计算配置
        if os.getenv('RUB_TO_CNY_RATE'):
            config.price_calculation.rub_to_cny_rate = float(os.getenv('RUB_TO_CNY_RATE'))
        if os.getenv('PRICING_DISCOUNT_RATE'):
            config.price_calculation.pricing_discount_rate = float(os.getenv('PRICING_DISCOUNT_RATE'))

        # 抓取配置
        if os.getenv('BROWSER_TYPE'):
            config.browser.browser_type = os.getenv('BROWSER_TYPE')
        if os.getenv('HEADLESS'):
            config.browser.headless = os.getenv('HEADLESS').lower() == 'true'
        if os.getenv('PAGE_LOAD_TIMEOUT_MS'):
            config.browser.page_load_timeout_ms = int(os.getenv('PAGE_LOAD_TIMEOUT_MS'))
        if os.getenv('ELEMENT_WAIT_TIMEOUT_MS'):
            config.browser.element_wait_timeout_ms = int(os.getenv('ELEMENT_WAIT_TIMEOUT_MS'))
        if os.getenv('MAX_RETRIES'):
            config.browser.max_retries = int(os.getenv('MAX_RETRIES'))
        if os.getenv('RETRY_DELAY_MS'):
            config.browser.retry_delay_ms = int(os.getenv('RETRY_DELAY_MS'))
        
        # Excel配置
        if os.getenv('DEFAULT_EXCEL_PATH'):
            config.excel.default_excel_path = os.getenv('DEFAULT_EXCEL_PATH')
        if os.getenv('PROFIT_CALCULATOR_PATH'):
            config.excel.profit_calculator_path = os.getenv('PROFIT_CALCULATOR_PATH')
        
        # 日志配置
        if os.getenv('LOG_LEVEL'):
            config.logging.log_level = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_FILE'):
            config.logging.log_file = os.getenv('LOG_FILE')
        
        # 全局配置
        if os.getenv('DEBUG_MODE'):
            config.debug_mode = os.getenv('DEBUG_MODE').lower() == 'true'
        if os.getenv('DRYRUN'):
            config.dryrun = os.getenv('DRYRUN').lower() == 'true'
        if os.getenv('SELECTION_MODE'):
            config.selection_mode = os.getenv('SELECTION_MODE')

        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'selector_filter': {
                'store_min_sales_30days': self.selector_filter.store_min_sales_30days,
                'store_min_orders_30days': self.selector_filter.store_min_orders_30days,
                'profit_rate_threshold': self.selector_filter.profit_rate_threshold,
                'good_store_ratio_threshold': self.selector_filter.good_store_ratio_threshold,
                'max_products_to_check': self.selector_filter.max_products_to_check,
                'item_category_blacklist': self.selector_filter.item_category_blacklist,
            },
            'price_calculation': {
                'price_adjustment_threshold_1': self.price_calculation.price_adjustment_threshold_1,
                'price_adjustment_threshold_2': self.price_calculation.price_adjustment_threshold_2,
                'price_adjustment_amount': self.price_calculation.price_adjustment_amount,
                'price_multiplier': self.price_calculation.price_multiplier,
                'pricing_discount_rate': self.price_calculation.pricing_discount_rate,
                'rub_to_cny_rate': self.price_calculation.rub_to_cny_rate,
                'commission_rate_low_threshold': self.price_calculation.commission_rate_low_threshold,
                'commission_rate_high_threshold': self.price_calculation.commission_rate_high_threshold,
                'commission_rate_default': self.price_calculation.commission_rate_default,
            },
            'browser': {
                'browser_type': self.browser.browser_type,
                'headless': self.browser.headless,
                'window_width': self.browser.window_width,
                'window_height': self.browser.window_height,
                'default_timeout_ms': self.browser.default_timeout_ms,
                'page_load_timeout_ms': self.browser.page_load_timeout_ms,
                'element_wait_timeout_ms': self.browser.element_wait_timeout_ms,
                'max_retries': self.browser.max_retries,
                'retry_delay_ms': self.browser.retry_delay_ms,
                'required_login_domains': self.browser.required_login_domains,
                'debug_port': self.browser.debug_port,
                'seerfar_base_url': self.browser.seerfar_base_url,
                'seerfar_store_detail_path': self.browser.seerfar_store_detail_path,
                'ozon_base_url': self.browser.ozon_base_url,
                'request_delay': self.browser.request_delay,
                'random_delay_range': self.browser.random_delay_range,
            },
            'excel': {
                'default_excel_path': self.excel.default_excel_path,
                'profit_calculator_path': self.excel.profit_calculator_path,
                'store_id_column': self.excel.store_id_column,
                'good_store_column': self.excel.good_store_column,
                'status_column': self.excel.status_column,
                'max_rows_to_process': self.excel.max_rows_to_process,
                'skip_empty_rows': self.excel.skip_empty_rows,
            },
            'logging': {
                'log_level': self.logging.log_level,
                'log_format': self.logging.log_format,
                'log_file': self.logging.log_file,
                'max_log_file_size': self.logging.max_log_file_size,
                'backup_count': self.logging.backup_count,
            },
            'performance': {
                'max_concurrent_stores': self.performance.max_concurrent_stores,
                'max_concurrent_products': self.performance.max_concurrent_products,
                'enable_cache': self.performance.enable_cache,
                'cache_ttl': self.performance.cache_ttl,
                'batch_size': self.performance.batch_size,
            },
            'debug_mode': self.debug_mode,
            'dryrun': self.dryrun,
            'selection_mode': self.selection_mode,
        }
    
    def save_to_json_file(self, file_path: str):
        """保存配置到JSON文件"""
        config_dict = self.to_dict()
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    @property
    def scraping(self):
        """向后兼容：scraping 属性已废弃，使用 browser 属性代替"""
        import warnings
        warnings.warn("配置属性 'scraping' 已废弃，请使用 'browser' 属性",
                     DeprecationWarning, stacklevel=2)
        return self.browser

    @property
    def store_filter(self):
        """向后兼容：store_filter 属性已废弃，使用 selector_filter 属性代替"""
        import warnings
        warnings.warn("配置属性 'store_filter' 已废弃，请使用 'selector_filter' 属性",
                     DeprecationWarning, stacklevel=2)
        return self.selector_filter

    def validate(self) -> bool:
        """验证配置的有效性"""
        try:
            # 验证数值范围
            assert 0 < self.selector_filter.store_min_sales_30days
            assert 0 < self.selector_filter.store_min_orders_30days
            assert 0 <= self.selector_filter.profit_rate_threshold <= 100
            assert 0 <= self.selector_filter.good_store_ratio_threshold <= 100
            assert 0 < self.selector_filter.max_products_to_check <= 1000
            
            assert 0 < self.price_calculation.price_adjustment_threshold_1
            assert 0 < self.price_calculation.price_adjustment_threshold_2
            assert 0 < self.price_calculation.price_multiplier
            assert 0 < self.price_calculation.pricing_discount_rate <= 1
            assert 0 < self.price_calculation.rub_to_cny_rate
            
            assert 0 < self.browser.page_load_timeout_ms <= 300000
            assert 0 < self.browser.element_wait_timeout_ms <= 60000
            assert 0 < self.browser.max_retries <= 10
            assert 0 <= self.browser.retry_delay_ms <= 10000
            
            assert 0 < self.excel.max_rows_to_process <= 100000
            

            assert self.performance.cache_ttl > 0
            assert self.performance.batch_size > 0
            
            return True
        except AssertionError:
            return False


# 全局配置实例
_global_config: Optional[GoodStoreSelectorConfig] = None

def get_config() -> GoodStoreSelectorConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config

def set_config(config: GoodStoreSelectorConfig):
    """设置全局配置实例"""
    global _global_config
    _global_config = config

def load_config(config_file: Optional[str] = None) -> GoodStoreSelectorConfig:
    """
    加载配置，优先级：
    1. 指定的配置文件
    2. 环境变量
    3. 默认配置
    """
    if config_file and os.path.exists(config_file):
        config = GoodStoreSelectorConfig.from_json_file(config_file)
    else:
        config = GoodStoreSelectorConfig.from_env()
    
    # 验证配置
    if not config.validate():
        logging.warning("配置验证失败，使用默认配置")
        config = GoodStoreSelectorConfig()
    
    return config

def create_default_config_file(file_path: str = "config/good_store_selector.json"):
    """创建默认配置文件"""
    config = GoodStoreSelectorConfig()
    config.save_to_json_file(file_path)
    return file_path
