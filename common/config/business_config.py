"""
业务配置模块

定义与业务逻辑相关的配置类，包括筛选、价格计算、Excel处理等配置
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SelectorFilterConfig:
    """选择器过滤配置

    遵循命名规范：
    - 商品级别过滤：item_**_filter
    - 店铺级别过滤：store_**_filter
    """
    # 店铺级别过滤条件
    store_min_sales_30days: float = 500000.0  # 店铺最小30天销售额（卢布）
    store_min_orders_30days: int = 250  # 店铺最小30天销量

    # 好店判定阈值
    profit_rate_threshold: float = 20.0  # 利润率阈值（百分比）
    good_store_ratio_threshold: float = 20.0  # 好店判定比例阈值（百分比）
    max_products_to_check: int = 10  # 每个店铺最多检查的商品数量

    # 商品级别过滤：类目黑名单配置
    item_category_blacklist: List[str] = field(default_factory=lambda: [
        "成人用品", "情趣用品", "医疗器械", "处方药", "烟草制品",
        "危险化学品", "易燃易爆物品", "武器装备", "赌博用具"
    ])  # 商品类目黑名单列表


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
