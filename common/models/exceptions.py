"""
系统异常类定义

定义好店筛选系统中的各种异常类型，提供清晰的错误分类和处理机制
"""


class GoodStoreSelectorError(Exception):
    """好店筛选系统基础异常"""
    pass


class DataValidationError(GoodStoreSelectorError):
    """数据验证异常"""
    pass


class ScrapingError(GoodStoreSelectorError):
    """网页抓取异常"""
    pass


class CriticalBrowserError(GoodStoreSelectorError):
    """致命浏览器错误，需要退出程序"""
    pass


class ExcelProcessingError(GoodStoreSelectorError):
    """Excel处理异常"""
    pass


class PriceCalculationError(GoodStoreSelectorError):
    """价格计算异常"""
    pass


class ConfigurationError(GoodStoreSelectorError):
    """配置异常"""
    pass


class ExcelCalculatorError(GoodStoreSelectorError):
    """Excel计算器异常类"""
    pass


class EngineError(GoodStoreSelectorError):
    """Engine-specific errors"""
    pass
