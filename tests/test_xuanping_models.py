"""
测试好店筛选系统的数据模型

测试数据结构的创建、验证和转换功能。
"""

import pytest
from datetime import datetime
from apps.xuanping.common.models import (
    StoreInfo, ProductInfo, PriceCalculationResult, CompetitorStore,
    ProductAnalysisResult, StoreAnalysisResult, ExcelStoreData, BatchProcessingResult,
    StoreStatus, GoodStoreFlag, validate_store_id, validate_price, validate_weight,
    clean_price_string, format_currency, calculate_profit_rate,
    DataValidationError, PriceCalculationError
)


class TestStoreInfo:
    """测试店铺信息模型"""
    
    def test_store_info_creation(self):
        """测试店铺信息创建"""
        store = StoreInfo(
            store_id="test_store_123",
            sold_30days=50000.0,
            sold_count_30days=100,
            daily_avg_sold=3.33
        )
        
        assert store.store_id == "test_store_123"
        assert store.sold_30days == 50000.0
        assert store.sold_count_30days == 100
        assert store.daily_avg_sold == 3.33
        assert store.is_good_store == GoodStoreFlag.EMPTY
        assert store.status == StoreStatus.EMPTY
    
    def test_store_info_validation(self):
        """测试店铺信息验证"""
        # 测试空店铺ID
        with pytest.raises(ValueError, match="店铺ID不能为空"):
            StoreInfo(store_id="")
        
        with pytest.raises(ValueError, match="店铺ID不能为空"):
            StoreInfo(store_id="   ")
    
    def test_store_info_defaults(self):
        """测试默认值"""
        store = StoreInfo(store_id="test_store")
        
        assert store.profitable_products_count == 0
        assert store.total_products_checked == 0
        assert store.needs_split == False


class TestProductInfo:
    """测试商品信息模型"""
    
    def test_product_info_creation(self):
        """测试商品信息创建"""
        product = ProductInfo(
            product_id="product_123",
            image_url="https://example.com/image.jpg",
            brand_name="TestBrand",
            sku="SKU123",
            green_price=100.0,
            black_price=120.0,
            commission_rate=0.15,
            weight=500.0
        )
        
        assert product.product_id == "product_123"
        assert product.image_url == "https://example.com/image.jpg"
        assert product.brand_name == "TestBrand"
        assert product.sku == "SKU123"
        assert product.green_price == 100.0
        assert product.black_price == 120.0
        assert product.commission_rate == 0.15
        assert product.weight == 500.0
        assert product.source_matched == False
    
    def test_product_info_validation(self):
        """测试商品信息验证"""
        # 测试空商品ID
        with pytest.raises(ValueError, match="商品ID不能为空"):
            ProductInfo(product_id="")
        
        with pytest.raises(ValueError, match="商品ID不能为空"):
            ProductInfo(product_id="   ")


class TestPriceCalculationResult:
    """测试价格计算结果模型"""
    
    def test_price_calculation_result_creation(self):
        """测试价格计算结果创建"""
        result = PriceCalculationResult(
            real_selling_price=120.0,
            product_pricing=114.0,
            profit_amount=6.0,
            profit_rate=25.0,
            is_profitable=True,
            calculation_details={"test": "data"}
        )
        
        assert result.real_selling_price == 120.0
        assert result.product_pricing == 114.0
        assert result.profit_amount == 6.0
        assert result.profit_rate == 25.0
        assert result.is_profitable == True
        assert result.calculation_details == {"test": "data"}
    
    def test_price_calculation_result_auto_profitable(self):
        """测试自动判断是否有利润"""
        # 测试负利润率
        result = PriceCalculationResult(
            real_selling_price=100.0,
            product_pricing=110.0,
            profit_amount=-10.0,
            profit_rate=-10.0,
            is_profitable=True,  # 这个会被覆盖
            calculation_details={}
        )
        
        assert result.is_profitable == False
        
        # 测试正利润率但低于阈值
        result = PriceCalculationResult(
            real_selling_price=100.0,
            product_pricing=95.0,
            profit_amount=5.0,
            profit_rate=15.0,  # 低于默认20%阈值
            is_profitable=True,
            calculation_details={}
        )
        
        assert result.is_profitable == False
        
        # 测试高于阈值的利润率
        result = PriceCalculationResult(
            real_selling_price=100.0,
            product_pricing=80.0,
            profit_amount=20.0,
            profit_rate=25.0,  # 高于默认20%阈值
            is_profitable=False,
            calculation_details={}
        )
        
        assert result.is_profitable == True


class TestStoreAnalysisResult:
    """测试店铺分析结果模型"""
    
    def test_store_analysis_result_creation(self):
        """测试店铺分析结果创建"""
        store_info = StoreInfo(store_id="test_store")
        
        # 创建商品分析结果
        product1 = ProductInfo(product_id="product1")
        price_calc1 = PriceCalculationResult(
            real_selling_price=100.0,
            product_pricing=80.0,
            profit_amount=20.0,
            profit_rate=25.0,
            is_profitable=True,
            calculation_details={}
        )
        product_result1 = ProductAnalysisResult(
            product_info=product1,
            price_calculation=price_calc1
        )
        
        product2 = ProductInfo(product_id="product2")
        price_calc2 = PriceCalculationResult(
            real_selling_price=100.0,
            product_pricing=95.0,
            profit_amount=5.0,
            profit_rate=5.0,
            is_profitable=False,
            calculation_details={}
        )
        product_result2 = ProductAnalysisResult(
            product_info=product2,
            price_calculation=price_calc2
        )
        
        # 创建店铺分析结果
        store_result = StoreAnalysisResult(
            store_info=store_info,
            products=[product_result1, product_result2],
            profit_rate_threshold=20.0,
            good_store_threshold=50.0  # 50%的商品有利润才算好店
        )
        
        # 验证自动计算的统计信息
        assert store_result.total_products == 2
        assert store_result.profitable_products == 1
        assert store_result.store_info.total_products_checked == 2
        assert store_result.store_info.profitable_products_count == 1
        
        # 验证好店判定（1/2 = 50%，达到阈值）
        assert store_result.store_info.needs_split == True
        assert store_result.store_info.is_good_store == GoodStoreFlag.YES
        assert store_result.store_info.status == StoreStatus.PROCESSED


class TestExcelStoreData:
    """测试Excel店铺数据模型"""
    
    def test_excel_store_data_creation(self):
        """测试Excel店铺数据创建"""
        excel_data = ExcelStoreData(
            row_index=2,
            store_id="test_store",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        assert excel_data.row_index == 2
        assert excel_data.store_id == "test_store"
        assert excel_data.is_good_store == GoodStoreFlag.YES
        assert excel_data.status == StoreStatus.PROCESSED
    
    def test_to_store_info_conversion(self):
        """测试转换为StoreInfo对象"""
        excel_data = ExcelStoreData(
            row_index=2,
            store_id="test_store",
            is_good_store=GoodStoreFlag.NO,
            status=StoreStatus.PENDING
        )
        
        store_info = excel_data.to_store_info()
        
        assert isinstance(store_info, StoreInfo)
        assert store_info.store_id == "test_store"
        assert store_info.is_good_store == GoodStoreFlag.NO
        assert store_info.status == StoreStatus.PENDING


class TestBatchProcessingResult:
    """测试批量处理结果模型"""
    
    def test_batch_processing_result_creation(self):
        """测试批量处理结果创建"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        result = BatchProcessingResult(
            total_stores=10,
            processed_stores=8,
            good_stores=3,
            failed_stores=2,
            processing_time=120.5,
            start_time=start_time,
            end_time=end_time
        )
        
        assert result.total_stores == 10
        assert result.processed_stores == 8
        assert result.good_stores == 3
        assert result.failed_stores == 2
        assert result.processing_time == 120.5
        assert result.start_time == start_time
        assert result.end_time == end_time
        assert result.store_results == []
        assert result.error_logs == []


class TestUtilityFunctions:
    """测试工具函数"""
    
    def test_validate_store_id(self):
        """测试店铺ID验证"""
        assert validate_store_id("valid_store_123") == True
        assert validate_store_id("") == False
        assert validate_store_id("   ") == False
        assert validate_store_id(None) == False
        assert validate_store_id(123) == False
    
    def test_validate_price(self):
        """测试价格验证"""
        assert validate_price(100.0) == True
        assert validate_price(0.0) == True
        assert validate_price(None) == True  # 允许为空
        assert validate_price(-10.0) == False
        assert validate_price("100") == False
    
    def test_validate_weight(self):
        """测试重量验证"""
        assert validate_weight(500.0) == True
        assert validate_weight(None) == True  # 允许为空
        assert validate_weight(0.0) == False  # 重量必须大于0
        assert validate_weight(-100.0) == False
        assert validate_weight("500") == False
    
    def test_clean_price_string(self):
        """测试价格字符串清理"""
        assert clean_price_string("₽123.45") == 123.45
        assert clean_price_string("¥1,234.56") == 1234.56
        assert clean_price_string("$99.99") == 99.99
        assert clean_price_string("  123.45  ") == 123.45
        assert clean_price_string("invalid") == None
        assert clean_price_string("") == None
        assert clean_price_string(None) == None
    
    def test_format_currency(self):
        """测试货币格式化"""
        assert format_currency(123.45) == "¥123.45"
        assert format_currency(123.45, "$") == "$123.45"
        assert format_currency(123.456) == "¥123.46"  # 四舍五入到2位小数
    
    def test_calculate_profit_rate(self):
        """测试利润率计算"""
        assert calculate_profit_rate(20.0, 100.0) == 20.0
        assert calculate_profit_rate(0.0, 100.0) == 0.0
        assert calculate_profit_rate(20.0, 0.0) == 0.0  # 成本为0时返回0
        assert calculate_profit_rate(-10.0, 100.0) == -10.0  # 允许负利润率


class TestEnums:
    """测试枚举类型"""
    
    def test_store_status_enum(self):
        """测试店铺状态枚举"""
        assert StoreStatus.PENDING == "未处理"
        assert StoreStatus.PROCESSED == "已处理"
        assert StoreStatus.EMPTY == ""
    
    def test_good_store_flag_enum(self):
        """测试好店标记枚举"""
        assert GoodStoreFlag.YES == "是"
        assert GoodStoreFlag.NO == "否"
        assert GoodStoreFlag.EMPTY == ""


class TestExceptions:
    """测试异常类"""
    
    def test_custom_exceptions(self):
        """测试自定义异常"""
        # 测试异常可以正常创建和抛出
        with pytest.raises(DataValidationError):
            raise DataValidationError("数据验证失败")
        
        with pytest.raises(PriceCalculationError):
            raise PriceCalculationError("价格计算失败")
        
        # 测试异常继承关系
        from apps.xuanping.common.models import GoodStoreSelectorError
        
        assert issubclass(DataValidationError, GoodStoreSelectorError)
        assert issubclass(PriceCalculationError, GoodStoreSelectorError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])