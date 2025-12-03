"""
数据模型包

导出所有数据模型类，支持统一的模型访问接口
"""

# 枚举类型
from .enums import (
    StoreStatus,
    GoodStoreFlag
)

# 业务模型
from .business_models import (
    StoreInfo,
    ProductInfo,
    PriceCalculationResult,
    CompetitorStore,
    ProductAnalysisResult,
    StoreAnalysisResult,
    BatchProcessingResult
)

# 抓取模型
from .scraping_models import (
    ScrapingResult
)

# Excel模型
from .excel_models import (
    ExcelStoreData
)

# 异常类
from .exceptions import (
    GoodStoreSelectorError,
    DataValidationError,
    ScrapingError,
    CriticalBrowserError,
    ExcelProcessingError,
    PriceCalculationError,
    ConfigurationError
)

# 工具函数 - 统一从scraping_utils导入以保持向后兼容性
from ..utils.scraping_utils import (
    validate_store_id,
    validate_price,
    validate_weight,
    format_currency,
    calculate_profit_rate,
    clean_price_string
)

# 延迟导入 ErrorResultFactory 以避免循环导入
def get_error_result_factory():
    """延迟导入 ErrorResultFactory 以避免循环导入"""
    from utils.result_factory import ErrorResultFactory
    return ErrorResultFactory

__all__ = [
    # 枚举类型
    'StoreStatus',
    'GoodStoreFlag',
    # 业务模型类
    'StoreInfo',
    'ProductInfo',
    'PriceCalculationResult',
    'CompetitorStore',
    'ProductAnalysisResult',
    'StoreAnalysisResult',
    'BatchProcessingResult',
    # 抓取模型
    'ScrapingResult',
    # Excel模型
    'ExcelStoreData',
    # 异常类
    'GoodStoreSelectorError',
    'DataValidationError',
    'ScrapingError',
    'CriticalBrowserError',
    'ExcelProcessingError',
    'PriceCalculationError',
    'ConfigurationError',
    # 工具函数
    'validate_store_id',
    'validate_price',
    'validate_weight',
    'clean_price_string',
    'format_currency',
    'calculate_profit_rate',
    'get_error_result_factory'
]
