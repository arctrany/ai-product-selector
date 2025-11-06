"""
好店筛选系统配置管理

管理系统的所有可调整参数，支持运行时配置和环境变量覆盖。
遵循配置外部化原则，便于不同环境的部署和参数调优。
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import logging


@dataclass
class StoreFilterConfig:
    """店铺筛选配置"""
    # 店铺初筛条件
    min_sales_30days: float = 500000.0  # 最小30天销售额（卢布）
    min_orders_30days: int = 250  # 最小30天销量
    
    # 好店判定阈值
    profit_rate_threshold: float = 20.0  # 利润率阈值（百分比）
    good_store_ratio_threshold: float = 20.0  # 好店判定比例阈值（百分比）
    max_products_to_check: int = 10  # 每个店铺最多检查的商品数量


@dataclass
class PriceCalculationConfig:
    """价格计算配置"""
    # 真实售价计算规则
    price_adjustment_threshold_1: float = 90.0  # 第一个价格调整阈值（人民币）
    price_adjustment_threshold_2: float = 120.0  # 第二个价格调整阈值（人民币）
    price_adjustment_amount: float = 5.0  # 价格调整金额
    price_multiplier: float = 2.2  # 价格倍数
    
    # 商品定价
    pricing_discount_rate: float = 0.95  # 定价折扣率（95折）
    
    # 汇率转换
    rub_to_cny_rate: float = 0.11  # 卢布转人民币汇率（示例值）
    
    # 佣金率计算规则
    commission_rate_low_threshold: float = 1500.0  # 低价商品阈值（卢布）
    commission_rate_high_threshold: float = 5000.0  # 高价商品阈值（卢布）
    commission_rate_default: float = 12.0  # 默认佣金率（百分比）


@dataclass
class ScrapingConfig:
    """网页抓取配置"""
    # 浏览器配置
    browser_type: str = "edge"  # 浏览器类型
    headless: bool = False  # 是否无头模式
    window_width: int = 1920
    window_height: int = 1080
    
    # 超时和重试配置
    page_load_timeout: int = 30  # 页面加载超时（秒）
    element_wait_timeout: int = 10  # 元素等待超时（秒）
    max_retry_attempts: int = 3  # 最大重试次数
    retry_delay: float = 2.0  # 重试延迟（秒）
    
    # Seerfar平台配置
    seerfar_base_url: str = "https://seerfar.cn"
    seerfar_store_detail_path: str = "/admin/store-detail.html"
    
    # OZON平台配置
    ozon_base_url: str = "https://www.ozon.ru"
    
    # 抓取间隔
    request_delay: float = 1.0  # 请求间隔（秒）
    random_delay_range: tuple = (0.5, 2.0)  # 随机延迟范围


@dataclass
class ExcelConfig:
    """Excel处理配置"""
    # 默认Excel文件路径
    default_excel_path: str = "uploads/store_list.xlsx"
    profit_calculator_path: str = "uploads/profit_calculator.xlsx"
    
    # Excel列配置
    store_id_column: str = "A"  # 店铺ID列
    good_store_column: str = "B"  # 是否为好店列
    status_column: str = "C"  # 状态列
    
    # 数据验证
    max_rows_to_process: int = 10000  # 最大处理行数
    skip_empty_rows: bool = True  # 跳过空行


@dataclass
class LoggingConfig:
    """日志配置"""
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None  # 日志文件路径，None表示只输出到控制台
    max_log_file_size: int = 10 * 1024 * 1024  # 最大日志文件大小（字节）
    backup_count: int = 5  # 日志文件备份数量


@dataclass
class PerformanceConfig:
    """性能配置"""
    # 并发配置
    max_concurrent_stores: int = 5  # 最大并发处理店铺数
    max_concurrent_products: int = 10  # 最大并发处理商品数
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 缓存过期时间（秒）
    
    # 批处理配置
    batch_size: int = 100  # 批处理大小


@dataclass
class GoodStoreSelectorConfig:
    """好店筛选系统主配置"""
    store_filter: StoreFilterConfig = field(default_factory=StoreFilterConfig)
    price_calculation: PriceCalculationConfig = field(default_factory=PriceCalculationConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    excel: ExcelConfig = field(default_factory=ExcelConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # 全局配置
    debug_mode: bool = False
    dryrun: bool = False  # 试运行模式，执行抓取但不写入文件，不调用1688接口
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GoodStoreSelectorConfig':
        """从字典创建配置对象"""
        config = cls()
        
        # 更新各个子配置
        if 'store_filter' in config_dict:
            for key, value in config_dict['store_filter'].items():
                if hasattr(config.store_filter, key):
                    setattr(config.store_filter, key, value)
        
        if 'price_calculation' in config_dict:
            for key, value in config_dict['price_calculation'].items():
                if hasattr(config.price_calculation, key):
                    setattr(config.price_calculation, key, value)
        
        if 'scraping' in config_dict:
            for key, value in config_dict['scraping'].items():
                if hasattr(config.scraping, key):
                    setattr(config.scraping, key, value)
        
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
        for key in ['debug_mode', 'dryrun']:
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
            config.store_filter.min_sales_30days = float(os.getenv('MIN_SALES_30DAYS'))
        if os.getenv('MIN_ORDERS_30DAYS'):
            config.store_filter.min_orders_30days = int(os.getenv('MIN_ORDERS_30DAYS'))
        if os.getenv('PROFIT_RATE_THRESHOLD'):
            config.store_filter.profit_rate_threshold = float(os.getenv('PROFIT_RATE_THRESHOLD'))
        
        # 价格计算配置
        if os.getenv('RUB_TO_CNY_RATE'):
            config.price_calculation.rub_to_cny_rate = float(os.getenv('RUB_TO_CNY_RATE'))
        if os.getenv('PRICING_DISCOUNT_RATE'):
            config.price_calculation.pricing_discount_rate = float(os.getenv('PRICING_DISCOUNT_RATE'))
        
        # 抓取配置
        if os.getenv('BROWSER_TYPE'):
            config.scraping.browser_type = os.getenv('BROWSER_TYPE')
        if os.getenv('HEADLESS'):
            config.scraping.headless = os.getenv('HEADLESS').lower() == 'true'
        if os.getenv('PAGE_LOAD_TIMEOUT'):
            config.scraping.page_load_timeout = int(os.getenv('PAGE_LOAD_TIMEOUT'))
        
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
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'store_filter': {
                'min_sales_30days': self.store_filter.min_sales_30days,
                'min_orders_30days': self.store_filter.min_orders_30days,
                'profit_rate_threshold': self.store_filter.profit_rate_threshold,
                'good_store_ratio_threshold': self.store_filter.good_store_ratio_threshold,
                'max_products_to_check': self.store_filter.max_products_to_check,
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
            'scraping': {
                'browser_type': self.scraping.browser_type,
                'headless': self.scraping.headless,
                'window_width': self.scraping.window_width,
                'window_height': self.scraping.window_height,
                'page_load_timeout': self.scraping.page_load_timeout,
                'element_wait_timeout': self.scraping.element_wait_timeout,
                'max_retry_attempts': self.scraping.max_retry_attempts,
                'retry_delay': self.scraping.retry_delay,
                'seerfar_base_url': self.scraping.seerfar_base_url,
                'seerfar_store_detail_path': self.scraping.seerfar_store_detail_path,
                'ozon_base_url': self.scraping.ozon_base_url,
                'request_delay': self.scraping.request_delay,
                'random_delay_range': self.scraping.random_delay_range,
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
        }
    
    def save_to_json_file(self, file_path: str):
        """保存配置到JSON文件"""
        config_dict = self.to_dict()
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        try:
            # 验证数值范围
            assert 0 < self.store_filter.min_sales_30days
            assert 0 < self.store_filter.min_orders_30days
            assert 0 <= self.store_filter.profit_rate_threshold <= 100
            assert 0 <= self.store_filter.good_store_ratio_threshold <= 100
            assert 0 < self.store_filter.max_products_to_check <= 1000
            
            assert 0 < self.price_calculation.price_adjustment_threshold_1
            assert 0 < self.price_calculation.price_adjustment_threshold_2
            assert 0 < self.price_calculation.price_multiplier
            assert 0 < self.price_calculation.pricing_discount_rate <= 1
            assert 0 < self.price_calculation.rub_to_cny_rate
            
            assert 0 < self.scraping.page_load_timeout <= 300
            assert 0 < self.scraping.element_wait_timeout <= 60
            assert 0 < self.scraping.max_retry_attempts <= 10
            assert 0 <= self.scraping.retry_delay <= 10
            
            assert 0 < self.excel.max_rows_to_process <= 100000
            
            assert self.performance.max_concurrent_stores > 0
            assert self.performance.max_concurrent_products > 0
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