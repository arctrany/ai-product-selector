"""
业务模型测试

测试 common/models/business_models.py 中定义的业务领域数据模型
"""

import pytest
from datetime import datetime
from common.models.business_models import StoreInfo, ProductInfo
from common.models.enums import StoreStatus, GoodStoreFlag


class TestStoreInfo:
    """店铺信息模型测试"""
    
    def test_store_info_creation(self):
        """测试店铺信息创建"""
        store = StoreInfo(store_id="12345")
        
        assert store.store_id == "12345"
        assert store.is_good_store == GoodStoreFlag.EMPTY
        assert store.status == StoreStatus.EMPTY
        assert store.sold_30days is None
        assert store.sold_count_30days is None
        assert store.daily_avg_sold is None
        assert store.profitable_products_count == 0
        assert store.total_products_checked == 0
        assert store.needs_split is False
    
    def test_store_info_with_sales_data(self):
        """测试包含销售数据的店铺信息"""
        store = StoreInfo(
            store_id="67890",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED,
            sold_30days=15000.50,
            sold_count_30days=500,
            daily_avg_sold=16.67
        )
        
        assert store.store_id == "67890"
        assert store.is_good_store == GoodStoreFlag.YES
        assert store.status == StoreStatus.PROCESSED
        assert store.sold_30days == 15000.50
        assert store.sold_count_30days == 500
        assert store.daily_avg_sold == 16.67
    
    def test_store_info_processing_results(self):
        """测试店铺处理结果字段"""
        store = StoreInfo(
            store_id="11111",
            profitable_products_count=25,
            total_products_checked=100,
            needs_split=True
        )
        
        assert store.profitable_products_count == 25
        assert store.total_products_checked == 100
        assert store.needs_split is True
    
    def test_store_info_validation_empty_id(self):
        """测试空店铺ID验证"""
        with pytest.raises(ValueError, match="店铺ID不能为空"):
            StoreInfo(store_id="")
        
        with pytest.raises(ValueError, match="店铺ID不能为空"):
            StoreInfo(store_id="   ")  # 只有空白字符
        
        with pytest.raises(ValueError, match="店铺ID不能为空"):
            StoreInfo(store_id=None)  # None值
    
    def test_store_info_validation_valid_id(self):
        """测试有效店铺ID"""
        # 正常ID应该可以创建
        store = StoreInfo(store_id="valid123")
        assert store.store_id == "valid123"
        
        # 包含空白但非空的ID也应该可以创建
        store_with_spaces = StoreInfo(store_id=" 123 ")
        assert store_with_spaces.store_id == " 123 "
    
    def test_store_info_enum_integration(self):
        """测试与枚举类型的集成"""
        store = StoreInfo(
            store_id="enum_test",
            is_good_store=GoodStoreFlag.NO,
            status=StoreStatus.FAILED
        )
        
        assert store.is_good_store == GoodStoreFlag.NO
        assert store.status == StoreStatus.FAILED
        
        # 测试枚举值比较
        assert store.is_good_store != GoodStoreFlag.YES
        assert store.status != StoreStatus.PROCESSED


class TestProductInfo:
    """商品信息模型测试"""
    
    def test_product_info_creation_empty(self):
        """测试空商品信息创建"""
        product = ProductInfo()
        
        assert product.product_id is None
        assert product.product_url is None
        assert product.image_url is None
        assert product.brand_name is None
        assert product.sku is None
    
    def test_product_info_creation_with_data(self):
        """测试包含数据的商品信息创建"""
        product = ProductInfo(
            product_id="PROD123",
            product_url="https://example.com/product/123",
            image_url="https://example.com/image/123.jpg",
            brand_name="测试品牌",
            sku="SKU-ABC-123"
        )
        
        assert product.product_id == "PROD123"
        assert product.product_url == "https://example.com/product/123"
        assert product.image_url == "https://example.com/image/123.jpg"
        assert product.brand_name == "测试品牌"
        assert product.sku == "SKU-ABC-123"
    
    def test_product_info_partial_data(self):
        """测试部分数据的商品信息"""
        product = ProductInfo(
            product_id="PARTIAL123",
            brand_name="部分品牌"
        )
        
        assert product.product_id == "PARTIAL123"
        assert product.brand_name == "部分品牌"
        assert product.product_url is None
        assert product.image_url is None
        assert product.sku is None
    
    def test_product_info_url_handling(self):
        """测试URL处理"""
        # 测试各种URL格式
        urls = [
            "https://ozon.ru/product/123",
            "https://www.ozon.ru/context/detail/id/123/",
            "http://example.com/product/123?param=value",
            "/relative/path/to/product"
        ]
        
        for url in urls:
            product = ProductInfo(product_url=url)
            assert product.product_url == url
    
    def test_product_info_field_types(self):
        """测试字段类型"""
        product = ProductInfo(
            product_id="TYPE_TEST",
            product_url="https://test.com",
            image_url="https://test.com/image.jpg",
            brand_name="类型测试品牌",
            sku="TYPE-SKU-001"
        )
        
        # 验证所有字段都是字符串类型或None
        assert isinstance(product.product_id, str)
        assert isinstance(product.product_url, str)
        assert isinstance(product.image_url, str)
        assert isinstance(product.brand_name, str)
        assert isinstance(product.sku, str)


class TestModelInteractions:
    """模型间交互测试"""
    
    def test_store_product_relationship(self):
        """测试店铺和商品的关系"""
        # 创建店铺
        store = StoreInfo(
            store_id="STORE001",
            profitable_products_count=10,
            total_products_checked=50
        )
        
        # 创建商品列表
        products = [
            ProductInfo(product_id=f"PROD{i:03d}", brand_name=f"品牌{i}")
            for i in range(1, 11)
        ]
        
        # 验证关系
        assert len(products) == store.profitable_products_count
        assert all(isinstance(p, ProductInfo) for p in products)
        assert all(p.product_id.startswith("PROD") for p in products)
    
    def test_business_logic_calculations(self):
        """测试业务逻辑计算"""
        store = StoreInfo(
            store_id="CALC001",
            sold_30days=30000.0,
            sold_count_30days=1000,
            profitable_products_count=25,
            total_products_checked=100
        )
        
        # 计算利润商品比例
        profit_ratio = store.profitable_products_count / store.total_products_checked
        assert profit_ratio == 0.25
        
        # 计算日均销量
        daily_avg = store.sold_count_30days / 30
        assert abs(daily_avg - 33.33) < 0.01
        
        # 计算平均客单价
        avg_order_value = store.sold_30days / store.sold_count_30days
        assert avg_order_value == 30.0
    
    def test_model_serialization(self):
        """测试模型序列化"""
        store = StoreInfo(
            store_id="SERIAL001",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED,
            sold_30days=10000.0
        )
        
        product = ProductInfo(
            product_id="PROD_SERIAL",
            brand_name="序列化品牌"
        )
        
        # 模拟序列化为字典
        store_dict = {
            'store_id': store.store_id,
            'is_good_store': store.is_good_store.value,
            'status': store.status.value,
            'sold_30days': store.sold_30days
        }
        
        product_dict = {
            'product_id': product.product_id,
            'brand_name': product.brand_name,
            'product_url': product.product_url
        }
        
        assert store_dict['store_id'] == "SERIAL001"
        assert store_dict['is_good_store'] == "是"
        assert store_dict['status'] == "已处理"
        assert product_dict['product_id'] == "PROD_SERIAL"
        assert product_dict['brand_name'] == "序列化品牌"


class TestModelEdgeCases:
    """模型边界情况测试"""
    
    def test_store_info_extreme_values(self):
        """测试极端数值"""
        # 测试零值
        store_zero = StoreInfo(
            store_id="ZERO",
            sold_30days=0.0,
            sold_count_30days=0,
            daily_avg_sold=0.0
        )
        
        assert store_zero.sold_30days == 0.0
        assert store_zero.sold_count_30days == 0
        assert store_zero.daily_avg_sold == 0.0
        
        # 测试大数值
        store_large = StoreInfo(
            store_id="LARGE",
            sold_30days=1000000.99,
            sold_count_30days=999999,
            profitable_products_count=9999
        )
        
        assert store_large.sold_30days == 1000000.99
        assert store_large.sold_count_30days == 999999
        assert store_large.profitable_products_count == 9999
    
    def test_product_info_unicode_handling(self):
        """测试Unicode字符处理"""
        product = ProductInfo(
            product_id="测试产品ID_123",
            brand_name="品牌名称™®",
            sku="产品编码-中文-123"
        )
        
        assert product.product_id == "测试产品ID_123"
        assert product.brand_name == "品牌名称™®"
        assert product.sku == "产品编码-中文-123"
    
    def test_model_defaults_behavior(self):
        """测试模型默认值行为"""
        # 测试StoreInfo默认值
        store = StoreInfo(store_id="DEFAULT_TEST")
        
        # 确保数值类型的默认值是0而不是None
        assert store.profitable_products_count == 0
        assert store.total_products_checked == 0
        assert store.needs_split is False
        
        # 确保可选字段的默认值是None
        assert store.sold_30days is None
        assert store.sold_count_30days is None
        assert store.daily_avg_sold is None
        
        # 测试ProductInfo默认值
        product = ProductInfo()
        assert product.product_id is None
        assert product.product_url is None
        assert product.image_url is None
        assert product.brand_name is None
        assert product.sku is None
