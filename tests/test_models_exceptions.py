"""
系统异常模型测试

测试 common/models/exceptions.py 中定义的异常类
"""

import pytest
from common.models.exceptions import (
    GoodStoreSelectorError,
    DataValidationError,
    ScrapingError,
    CriticalBrowserError,
    ExcelProcessingError,
    PriceCalculationError,
    ConfigurationError
)


class TestGoodStoreSelectorError:
    """好店筛选系统基础异常测试"""
    
    def test_good_store_selector_error_creation(self):
        """测试基础异常创建"""
        message = "基础系统错误"
        error = GoodStoreSelectorError(message)
        
        assert str(error) == message
        assert isinstance(error, Exception)
        assert error.args == (message,)
    
    def test_good_store_selector_error_inheritance(self):
        """测试异常继承关系"""
        error = GoodStoreSelectorError("测试")
        
        assert isinstance(error, Exception)
        assert issubclass(GoodStoreSelectorError, Exception)
    
    def test_good_store_selector_error_empty_message(self):
        """测试空消息异常"""
        error = GoodStoreSelectorError("")
        assert str(error) == ""
    
    def test_good_store_selector_error_unicode_message(self):
        """测试Unicode消息"""
        message = "系统错误：无法处理中文字符™®©"
        error = GoodStoreSelectorError(message)
        assert str(error) == message
    
    def test_good_store_selector_error_multiple_args(self):
        """测试多参数异常"""
        error = GoodStoreSelectorError("错误", "详细信息", 123)
        assert error.args == ("错误", "详细信息", 123)
        assert str(error) == "错误"


class TestDataValidationError:
    """数据验证异常测试"""
    
    def test_data_validation_error_creation(self):
        """测试数据验证异常创建"""
        message = "数据验证失败"
        error = DataValidationError(message)
        
        assert str(error) == message
        assert isinstance(error, GoodStoreSelectorError)
        assert isinstance(error, Exception)
    
    def test_data_validation_error_inheritance(self):
        """测试继承关系"""
        error = DataValidationError("测试")
        
        assert isinstance(error, GoodStoreSelectorError)
        assert issubclass(DataValidationError, GoodStoreSelectorError)
        assert issubclass(DataValidationError, Exception)
    
    def test_data_validation_error_specific_cases(self):
        """测试具体数据验证场景"""
        validation_cases = [
            "店铺ID格式无效",
            "价格数据超出范围",
            "必填字段为空",
            "数据类型不匹配",
            "字符串长度超限"
        ]
        
        for case in validation_cases:
            error = DataValidationError(case)
            assert str(error) == case
            assert isinstance(error, DataValidationError)


class TestScrapingError:
    """网页抓取异常测试"""
    
    def test_scraping_error_creation(self):
        """测试抓取异常创建"""
        message = "网页抓取失败"
        error = ScrapingError(message)
        
        assert str(error) == message
        assert isinstance(error, GoodStoreSelectorError)
    
    def test_scraping_error_inheritance(self):
        """测试继承关系"""
        error = ScrapingError("测试")
        
        assert isinstance(error, GoodStoreSelectorError)
        assert issubclass(ScrapingError, GoodStoreSelectorError)
    
    def test_scraping_error_common_scenarios(self):
        """测试常见抓取错误场景"""
        scraping_scenarios = [
            "网络连接超时",
            "页面元素未找到",
            "登录失败",
            "反爬虫检测",
            "数据解析错误",
            "浏览器崩溃"
        ]
        
        for scenario in scraping_scenarios:
            error = ScrapingError(scenario)
            assert str(error) == scenario
            assert isinstance(error, ScrapingError)


class TestCriticalBrowserError:
    """致命浏览器异常测试"""
    
    def test_critical_browser_error_creation(self):
        """测试致命浏览器异常创建"""
        message = "致命浏览器错误，需要重启"
        error = CriticalBrowserError(message)
        
        assert str(error) == message
        assert isinstance(error, GoodStoreSelectorError)
    
    def test_critical_browser_error_inheritance(self):
        """测试继承关系"""
        error = CriticalBrowserError("测试")
        
        assert isinstance(error, GoodStoreSelectorError)
        assert issubclass(CriticalBrowserError, GoodStoreSelectorError)
    
    def test_critical_browser_error_severity(self):
        """测试致命错误的严重性场景"""
        critical_scenarios = [
            "浏览器进程崩溃",
            "内存不足导致浏览器无响应",
            "驱动程序异常",
            "系统资源耗尽",
            "浏览器配置损坏"
        ]
        
        for scenario in critical_scenarios:
            error = CriticalBrowserError(scenario)
            assert str(error) == scenario
            assert isinstance(error, CriticalBrowserError)


class TestExcelProcessingError:
    """Excel处理异常测试"""
    
    def test_excel_processing_error_creation(self):
        """测试Excel处理异常创建"""
        message = "Excel文件处理失败"
        error = ExcelProcessingError(message)
        
        assert str(error) == message
        assert isinstance(error, GoodStoreSelectorError)
    
    def test_excel_processing_error_inheritance(self):
        """测试继承关系"""
        error = ExcelProcessingError("测试")
        
        assert isinstance(error, GoodStoreSelectorError)
        assert issubclass(ExcelProcessingError, GoodStoreSelectorError)
    
    def test_excel_processing_error_scenarios(self):
        """测试Excel处理错误场景"""
        excel_scenarios = [
            "文件不存在",
            "文件格式不支持",
            "工作表未找到",
            "单元格数据格式错误",
            "文件被锁定",
            "权限不足",
            "磁盘空间不足"
        ]
        
        for scenario in excel_scenarios:
            error = ExcelProcessingError(scenario)
            assert str(error) == scenario
            assert isinstance(error, ExcelProcessingError)


class TestPriceCalculationError:
    """价格计算异常测试"""
    
    def test_price_calculation_error_creation(self):
        """测试价格计算异常创建"""
        message = "价格计算错误"
        error = PriceCalculationError(message)
        
        assert str(error) == message
        assert isinstance(error, GoodStoreSelectorError)
    
    def test_price_calculation_error_inheritance(self):
        """测试继承关系"""
        error = PriceCalculationError("测试")
        
        assert isinstance(error, GoodStoreSelectorError)
        assert issubclass(PriceCalculationError, GoodStoreSelectorError)
    
    def test_price_calculation_error_scenarios(self):
        """测试价格计算错误场景"""
        calculation_scenarios = [
            "除零错误",
            "负价格异常",
            "汇率数据缺失",
            "利润率计算溢出",
            "成本数据无效",
            "税率配置错误"
        ]
        
        for scenario in calculation_scenarios:
            error = PriceCalculationError(scenario)
            assert str(error) == scenario
            assert isinstance(error, PriceCalculationError)


class TestConfigurationError:
    """配置异常测试"""
    
    def test_configuration_error_creation(self):
        """测试配置异常创建"""
        message = "配置参数错误"
        error = ConfigurationError(message)
        
        assert str(error) == message
        assert isinstance(error, GoodStoreSelectorError)
    
    def test_configuration_error_inheritance(self):
        """测试继承关系"""
        error = ConfigurationError("测试")
        
        assert isinstance(error, GoodStoreSelectorError)
        assert issubclass(ConfigurationError, GoodStoreSelectorError)
    
    def test_configuration_error_scenarios(self):
        """测试配置错误场景"""
        config_scenarios = [
            "配置文件不存在",
            "JSON格式错误",
            "必需配置项缺失",
            "配置值超出范围",
            "环境变量未设置",
            "配置文件权限不足"
        ]
        
        for scenario in config_scenarios:
            error = ConfigurationError(scenario)
            assert str(error) == scenario
            assert isinstance(error, ConfigurationError)


class TestExceptionHierarchy:
    """异常层次结构测试"""
    
    def test_exception_inheritance_tree(self):
        """测试完整的异常继承树"""
        # 测试所有异常都继承自GoodStoreSelectorError
        exception_classes = [
            DataValidationError,
            ScrapingError,
            CriticalBrowserError,
            ExcelProcessingError,
            PriceCalculationError,
            ConfigurationError
        ]
        
        for exception_class in exception_classes:
            assert issubclass(exception_class, GoodStoreSelectorError)
            assert issubclass(exception_class, Exception)
    
    def test_exception_type_checking(self):
        """测试异常类型检查"""
        errors = [
            DataValidationError("数据验证错误"),
            ScrapingError("抓取错误"),
            CriticalBrowserError("浏览器错误"),
            ExcelProcessingError("Excel错误"),
            PriceCalculationError("计算错误"),
            ConfigurationError("配置错误")
        ]
        
        # 所有错误都应该是GoodStoreSelectorError的实例
        for error in errors:
            assert isinstance(error, GoodStoreSelectorError)
            assert isinstance(error, Exception)
    
    def test_exception_polymorphism(self):
        """测试异常多态性"""
        def handle_error(error: GoodStoreSelectorError) -> str:
            """异常处理函数"""
            return f"处理异常: {type(error).__name__} - {str(error)}"
        
        errors = [
            DataValidationError("验证失败"),
            ScrapingError("抓取失败"),
            ExcelProcessingError("Excel失败")
        ]
        
        results = [handle_error(error) for error in errors]
        
        assert "DataValidationError" in results[0]
        assert "ScrapingError" in results[1]
        assert "ExcelProcessingError" in results[2]


class TestExceptionHandlingPatterns:
    """异常处理模式测试"""
    
    def test_exception_catch_specific(self):
        """测试捕获特定异常"""
        def raise_data_validation_error():
            raise DataValidationError("数据无效")
        
        with pytest.raises(DataValidationError) as exc_info:
            raise_data_validation_error()
        
        assert str(exc_info.value) == "数据无效"
        assert isinstance(exc_info.value, DataValidationError)
        assert isinstance(exc_info.value, GoodStoreSelectorError)
    
    def test_exception_catch_base_class(self):
        """测试捕获基类异常"""
        def raise_various_errors(error_type: str):
            if error_type == "validation":
                raise DataValidationError("验证错误")
            elif error_type == "scraping":
                raise ScrapingError("抓取错误")
            elif error_type == "excel":
                raise ExcelProcessingError("Excel错误")
        
        # 使用基类捕获所有子类异常
        for error_type in ["validation", "scraping", "excel"]:
            with pytest.raises(GoodStoreSelectorError):
                raise_various_errors(error_type)
    
    def test_exception_chaining(self):
        """测试异常链"""
        def inner_function():
            raise ValueError("原始错误")
        
        def outer_function():
            try:
                inner_function()
            except ValueError as e:
                raise ScrapingError("抓取过程中发生错误") from e
        
        with pytest.raises(ScrapingError) as exc_info:
            outer_function()
        
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert str(exc_info.value.__cause__) == "原始错误"
    
    def test_exception_context_manager(self):
        """测试异常上下文管理"""
        class ErrorContext:
            def __init__(self, error_type):
                self.error_type = error_type
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type and issubclass(exc_type, GoodStoreSelectorError):
                    # 记录异常但不抑制
                    return False
                return False
        
        with pytest.raises(DataValidationError):
            with ErrorContext("validation"):
                raise DataValidationError("上下文中的错误")


class TestExceptionCustomization:
    """异常定制化测试"""
    
    def test_exception_with_additional_attributes(self):
        """测试带有额外属性的异常"""
        class ExtendedScrapingError(ScrapingError):
            def __init__(self, message: str, url: str = None, status_code: int = None):
                super().__init__(message)
                self.url = url
                self.status_code = status_code
        
        error = ExtendedScrapingError(
            "页面加载失败",
            url="https://example.com",
            status_code=404
        )
        
        assert str(error) == "页面加载失败"
        assert error.url == "https://example.com"
        assert error.status_code == 404
        assert isinstance(error, ScrapingError)
        assert isinstance(error, GoodStoreSelectorError)
    
    def test_exception_repr_customization(self):
        """测试异常字符串表示定制"""
        class DetailedConfigError(ConfigurationError):
            def __init__(self, message: str, config_key: str = None):
                super().__init__(message)
                self.config_key = config_key
            
            def __repr__(self):
                if self.config_key:
                    return f"{self.__class__.__name__}(message='{self}', config_key='{self.config_key}')"
                return f"{self.__class__.__name__}(message='{self}')"
        
        error = DetailedConfigError("配置值无效", config_key="database.timeout")
        
        assert str(error) == "配置值无效"
        assert "config_key='database.timeout'" in repr(error)
        assert isinstance(error, ConfigurationError)
