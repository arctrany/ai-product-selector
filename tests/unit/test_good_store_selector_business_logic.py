"""
GoodStoreSelector 业务逻辑单元测试

测试新增的合并逻辑和数据处理方法
"""
import unittest
from unittest.mock import patch

from common.services.good_store_selector import GoodStoreSelector, _evaluate_profit_calculation_completeness
from common.models.business_models import ProductInfo
from common.models.scraping_result import ScrapingResult
from common.config.base_config import GoodStoreSelectorConfig


class TestGoodStoreSelectorBusinessLogic(unittest.TestCase):
    """GoodStoreSelector 业务逻辑测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = GoodStoreSelectorConfig()
        
        # Mock 依赖组件，但保持 ProfitEvaluator 的 prepare_for_profit_calculation 方法可用
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_evaluator, \
             patch('good_store_selector.get_global_scraping_orchestrator'):
            
            # 创建真实的 ProfitEvaluator 实例用于测试
            from common.business.profit_evaluator import ProfitEvaluator
            real_profit_evaluator = ProfitEvaluator(self.config)
            mock_profit_evaluator.return_value = real_profit_evaluator
            
            self.selector = GoodStoreSelector(
                excel_file_path="/tmp/test.xlsx",
                config=self.config
            )
            
            # 初始化组件以设置 profit_evaluator
            self.selector._initialize_components()
    
    def test_evaluate_profit_calculation_completeness_full(self):
        """测试完整数据的利润计算完整性评估"""
        # 创建完整的商品数据（8个必需字段）
        complete_product = ProductInfo(
            green_price=100.0,
            black_price=120.0,
            source_price=50.0,
            commission_rate=0.15,
            weight=500.0,
            length=10.0,
            width=8.0,
            height=5.0
        )
        
        completeness = _evaluate_profit_calculation_completeness(complete_product)
        
        # 验证完整度为100%（8/8）
        self.assertEqual(completeness, 1.0)
    
    def test_evaluate_profit_calculation_completeness_partial(self):
        """测试部分数据的利润计算完整性评估"""
        # 创建部分商品数据（只有4个必需字段）
        partial_product = ProductInfo(
            green_price=100.0,
            black_price=120.0,
            source_price=50.0,
            commission_rate=0.15
            # 缺少 weight, length, width, height
        )
        
        completeness = _evaluate_profit_calculation_completeness(partial_product)
        
        # 验证完整度为50%（4/8）
        self.assertEqual(completeness, 0.5)
    
    def test_evaluate_profit_calculation_completeness_minimal(self):
        """测试最少数据的利润计算完整性评估"""
        # 创建最少商品数据（只有2个必需字段）
        minimal_product = ProductInfo(
            green_price=100.0,
            source_price=50.0
        )
        
        completeness = _evaluate_profit_calculation_completeness(minimal_product)
        
        # 验证完整度为25%（2/8）
        self.assertEqual(completeness, 0.25)
    
    def test_prepare_for_profit_calculation_with_green_price(self):
        """测试基于绿标价格的利润计算准备"""
        product = ProductInfo(
            green_price=100.0,
            black_price=120.0
        )
        
        prepared = self.selector.profit_evaluator.prepare_for_profit_calculation(product)
        
        # 验证定价计算（绿标价格 * 0.95）
        self.assertEqual(prepared.list_price, 95.0)
    
    def test_prepare_for_profit_calculation_with_black_price_only(self):
        """测试仅有黑标价格时的利润计算准备"""
        product = ProductInfo(
            black_price=120.0
        )
        
        prepared = self.selector.profit_evaluator.prepare_for_profit_calculation(product)
        
        # 验证定价计算（黑标价格 * 0.95）
        self.assertEqual(prepared.list_price, 114.0)
    
    def test_prepare_for_profit_calculation_no_price(self):
        """测试无价格数据时的利润计算准备"""
        product = ProductInfo(
            product_id="123"
        )
        
        prepared = self.selector.profit_evaluator.prepare_for_profit_calculation(product)
        
        # 验证无价格时 list_price 为 None
        self.assertIsNone(prepared.list_price)
    
    def test_merge_and_compute_select_competitor(self):
        """测试选择跟卖商品的合并逻辑"""
        # 创建不完整的原商品
        primary_product = ProductInfo(
            product_id="123",
            green_price=100.0,
            source_price=50.0
            # 缺少其他ERP字段
        )
        
        # 创建完整的跟卖商品
        competitor_product = ProductInfo(
            product_id="comp-456",
            green_price=80.0,
            black_price=95.0,
            source_price=45.0,
            commission_rate=0.15,
            weight=500.0,
            length=10.0,
            width=8.0,
            height=5.0
        )
        
        # 模拟抓取结果
        scraping_result = ScrapingResult.create_success({
            'primary_product': primary_product,
            'competitor_product': competitor_product,
            'competitors_list': [{'product_id': 'comp-456'}]
        })
        
        # 执行合并逻辑
        merged_product = self.selector.merge_and_compute(scraping_result)
        
        # 验证选择了完整度更高的跟卖商品
        self.assertEqual(merged_product.product_id, "comp-456")
        self.assertTrue(merged_product.is_competitor_selected)
        self.assertEqual(merged_product.list_price, 76.0)  # 80 * 0.95
    
    def test_merge_and_compute_select_primary(self):
        """测试选择原商品的合并逻辑"""
        # 创建完整的原商品
        primary_product = ProductInfo(
            product_id="123",
            green_price=100.0,
            black_price=120.0,
            source_price=50.0,
            commission_rate=0.15,
            weight=500.0,
            length=10.0,
            width=8.0,
            height=5.0
        )
        
        # 创建不完整的跟卖商品
        competitor_product = ProductInfo(
            product_id="comp-456",
            green_price=80.0,
            source_price=45.0
            # 缺少其他ERP字段
        )
        
        # 模拟抓取结果
        scraping_result = ScrapingResult.create_success({
            'primary_product': primary_product,
            'competitor_product': competitor_product,
            'competitors_list': [{'product_id': 'comp-456'}]
        })
        
        # 执行合并逻辑
        merged_product = self.selector.merge_and_compute(scraping_result)
        
        # 验证选择了完整度更高的原商品
        self.assertEqual(merged_product.product_id, "123")
        self.assertFalse(merged_product.is_competitor_selected)
        self.assertEqual(merged_product.list_price, 95.0)  # 100 * 0.95
    
    def test_merge_and_compute_no_competitor(self):
        """测试无跟卖商品时的合并逻辑"""
        # 创建原商品
        primary_product = ProductInfo(
            product_id="123",
            green_price=100.0,
            source_price=50.0
        )
        
        # 模拟无跟卖的抓取结果
        scraping_result = ScrapingResult.create_success({
            'primary_product': primary_product,
            'competitor_product': None,
            'competitors_list': []
        })
        
        # 执行合并逻辑
        merged_product = self.selector.merge_and_compute(scraping_result)
        
        # 验证直接返回原商品
        self.assertEqual(merged_product.product_id, "123")
        self.assertFalse(merged_product.is_competitor_selected)
        self.assertEqual(merged_product.list_price, 95.0)  # 100 * 0.95
    
    def test_merge_and_compute_missing_primary_product(self):
        """测试缺少原商品数据时的错误处理"""
        # 模拟缺少原商品的抓取结果
        scraping_result = ScrapingResult.create_success({
            'primary_product': None,
            'competitor_product': None,
            'competitors_list': []
        })
        
        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.selector.merge_and_compute(scraping_result)
        
        self.assertIn("缺少原商品数据", str(context.exception))
    
    def test_completeness_evaluation_edge_cases(self):
        """测试完整性评估的边界情况"""
        # 测试零值字段
        product_with_zeros = ProductInfo(
            green_price=0.0,  # 零值应该被视为无效
            black_price=120.0,
            source_price=50.0,
            commission_rate=0.0,  # 零值应该被视为无效
            weight=500.0,
            length=10.0,
            width=8.0,
            height=5.0
        )
        
        completeness = _evaluate_profit_calculation_completeness(product_with_zeros)
        
        # 验证零值字段不被计算在内（6个有效字段/8个总字段）
        self.assertEqual(completeness, 0.75)
    
    def test_prepare_calculation_preserves_original_data(self):
        """测试利润计算准备不会修改原始数据"""
        original_product = ProductInfo(
            product_id="123",
            green_price=100.0,
            source_price=50.0
        )
        
        # 保存原始值
        original_green_price = original_product.green_price
        original_list_price = original_product.list_price
        
        # 执行准备操作（现在通过 profit_evaluator）
        prepared = self.selector.profit_evaluator.prepare_for_profit_calculation(original_product)
        
        # 验证返回的是同一个对象（修改了 list_price）
        self.assertIs(prepared, original_product)
        self.assertEqual(prepared.green_price, original_green_price)
        self.assertEqual(prepared.list_price, 95.0)
        
        # 验证 list_price 被正确设置
        self.assertNotEqual(original_list_price, prepared.list_price)


if __name__ == '__main__':
    unittest.main()