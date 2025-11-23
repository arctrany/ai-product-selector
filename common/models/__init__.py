"""
数据模型包

导出所有数据模型类
"""

# 从新的模型定义导入
from .scraping_result import (
    ScrapingStatus,
    CompetitorInfo,
    CompetitorDetectionResult,
    ProductScrapingResult
)

# 从旧模型导入业务相关类
# 使用相对导入从上级目录的 models.py 文件导入
import sys
from pathlib import Path

# 获取当前文件的路径
current_dir = Path(__file__).parent
# 构建 models.py 文件的路径
models_py_path = current_dir.parent / "models.py"

# 动态导入 models.py 文件
if models_py_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("legacy_models", models_py_path)
    legacy_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_models)

    # 重新导出需要的类和函数
    CompetitorStore = legacy_models.CompetitorStore
    clean_price_string = legacy_models.clean_price_string
    ExcelStoreData = legacy_models.ExcelStoreData
    StoreInfo = legacy_models.StoreInfo
    ProductInfo = legacy_models.ProductInfo
    BatchProcessingResult = legacy_models.BatchProcessingResult
    StoreAnalysisResult = legacy_models.StoreAnalysisResult
    GoodStoreFlag = legacy_models.GoodStoreFlag
    StoreStatus = legacy_models.StoreStatus
    PriceCalculationResult = legacy_models.PriceCalculationResult
    ProductAnalysisResult = legacy_models.ProductAnalysisResult

    # 异常类
    GoodStoreSelectorError = legacy_models.GoodStoreSelectorError
    DataValidationError = legacy_models.DataValidationError
    ScrapingError = legacy_models.ScrapingError
    CriticalBrowserError = legacy_models.CriticalBrowserError
    ExcelProcessingError = legacy_models.ExcelProcessingError
    PriceCalculationError = legacy_models.PriceCalculationError
    ConfigurationError = legacy_models.ConfigurationError

# 重新导出 ScrapingResult 以确保使用新的版本
from .scraping_result import ScrapingResult

# 延迟导入 ErrorResultFactory 以避免循环导入
def get_error_result_factory():
    """延迟导入 ErrorResultFactory 以避免循环导入"""
    from utils.result_factory import ErrorResultFactory
    return ErrorResultFactory

__all__ = [
    # 新的抓取结果相关类
    'ScrapingResult',
    'ScrapingStatus',
    'CompetitorInfo',
    'CompetitorDetectionResult',
    'ProductScrapingResult',
    # 旧的业务模型类
    'CompetitorStore',
    'clean_price_string',
    'ExcelStoreData',
    'StoreInfo',
    'ProductInfo',
    'BatchProcessingResult',
    'StoreAnalysisResult',
    'GoodStoreFlag',
    'StoreStatus',
    'PriceCalculationResult',
    'ProductAnalysisResult',
    # 异常类
    'GoodStoreSelectorError',
    'DataValidationError',
    'ScrapingError',
    'CriticalBrowserError',
    'ExcelProcessingError',
    'PriceCalculationError',
    'ConfigurationError',
    # 工具函数
    'get_error_result_factory'
]
