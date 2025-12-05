"""
GoodStoreSelector 集成测试

测试 GoodStoreSelector 与其他组件的集成，包括新的合并逻辑
"""
import unittest
from unittest.mock import Mock, patch
import tempfile
import os

from common.services.good_store_selector import GoodStoreSelector, _evaluate_profit_calculation_completeness
from common.models.business_models import ProductInfo
from common.models.excel_models import ExcelStoreData
from common.models.scraping_result import ScrapingResult
from common.models.enums import GoodStoreFlag, StoreStatus
from common.config.base_config import GoodStoreSelectorConfig


class TestGoodStoreSelectorIntegration(unittest.TestCase):
    """GoodStoreSelector 集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = GoodStoreSelectorConfig()
        
        # 创建临时文件
        self.temp_excel = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_calc = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        
        self.temp_excel.close()
        self.temp_calc.close()
    
    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.temp_excel.name)
            os.unlink(self.temp_calc.name)
        except:
            pass
    
    def test_full_integration_with_merge_logic(self):
        """测试完整集成流程包含新的合并逻辑"""
        # Mock 所有依赖组件
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func:
            
            # 设置 Excel 处理器 Mock
            mock_excel = Mock()
            mock_excel.read_store_data.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel.filter_pending_stores.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel_class.return_value = mock_excel
            
            # 设置利润评估器 Mock
            mock_profit = Mock()
            mock_profit.evaluate_product_profit.return_value = {
                'profit_rate': 25.0,
                'is_profitable': True,
                'source_price': 45.0,
                'selling_price': 80.0,
                'product_info': ProductInfo(product_id="comp-456")
            }
            mock_profit_class.return_value = mock_profit
            
            # 设置协调器 Mock - 需要处理两种调用：店铺分析和商品分析
            primary_product = ProductInfo(
                product_id="123",
                green_price=100.0,
                source_price=50.0,
                commission_rate=0.15
            )
            
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
            
            mock_orchestrator = Mock()
            
            # 设置不同的返回值：第一次调用（店铺分析），第二次调用（商品分析）
            mock_orchestrator.scrape_with_orchestration.side_effect = [
                # 第一次调用：店铺分析，返回商品列表
                ScrapingResult.create_success({
                    'products': [
                        {
                            'product_id': 'test_product_123',
                            'ozonUrl': 'https://www.ozon.ru/product/test-123/',
                            'brand_name': 'Test Brand',
                            'sku': 'TEST-SKU-001'
                        }
                    ]
                }),
                # 第二次调用：商品分析，返回完整商品数据
                ScrapingResult.create_success({
                    'primary_product': primary_product,
                    'competitor_product': competitor_product,
                    'competitors_list': [{'product_id': 'comp-456'}]
                })
            ]
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 创建 GoodStoreSelector 实例
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 执行完整流程
            result = selector.process_stores()
            
            # 验证结果
            self.assertIsNotNone(result)
            self.assertEqual(result.total_stores, 1)
            
            # 验证调用了新的合并逻辑
            mock_orchestrator.scrape_with_orchestration.assert_called()
            mock_profit.evaluate_product_profit.assert_called()
    
    def test_merge_and_compute_integration_with_profit_evaluator(self):
        """测试 merge_and_compute 与利润评估器的集成"""
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator'):
            
            # 设置真实的 ProfitEvaluator 实例
            from common.business.profit_evaluator import ProfitEvaluator
            real_profit_evaluator = ProfitEvaluator(self.temp_calc.name, self.config)
            mock_profit_class.return_value = real_profit_evaluator
            
            # 创建选择器
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 初始化组件
            selector._initialize_components()
            
            # 创建测试数据 - 跟卖商品完整度更高
            primary_product = ProductInfo(
                product_id="123",
                green_price=100.0,
                source_price=50.0
            )
            
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
            
            scraping_result = ScrapingResult.create_success({
                'primary_product': primary_product,
                'competitor_product': competitor_product,
                'competitors_list': [{'product_id': 'comp-456'}]
            })
            
            # 执行合并逻辑
            merged_product = selector.merge_and_compute(scraping_result)
            
            # 验证选择了完整度更高的跟卖商品
            self.assertEqual(merged_product.product_id, "comp-456")
            self.assertTrue(merged_product.is_competitor_selected)
            self.assertEqual(merged_product.list_price, 76.0)  # 80 * 0.95
            
            # 验证完整性评估
            competitor_completeness = _evaluate_profit_calculation_completeness(competitor_product)
            primary_completeness = _evaluate_profit_calculation_completeness(primary_product)
            
            self.assertEqual(competitor_completeness, 1.0)  # 8/8 = 100%
            self.assertEqual(primary_completeness, 0.25)   # 2/8 = 25%
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func:
            
            # 设置 Excel 处理器返回待处理店铺
            mock_excel = Mock()
            mock_excel.read_store_data.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="error_store",
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel.filter_pending_stores.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="error_store",
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel_class.return_value = mock_excel
            
            
            
            # 设置协调器返回错误 - 第一次调用（店铺分析）失败
            mock_orchestrator = Mock()
            mock_orchestrator.scrape_with_orchestration.return_value = ScrapingResult.create_failure(
                "店铺数据抓取失败"
            )
            mock_orchestrator_func.return_value = mock_orchestrator
            
            mock_profit_class.return_value = Mock()
            
            # 创建选择器
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 执行处理
            result = selector.process_stores()
            
            # 验证错误处理
            self.assertEqual(result.failed_stores, 1)
            self.assertEqual(result.processed_stores, 0)
    
    def test_data_flow_validation(self):
        """测试数据流验证"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func:
            
            # 设置完整的数据流
            mock_excel = Mock()
            mock_excel.read_store_data.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="data_flow_test",
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel.filter_pending_stores.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="data_flow_test",
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel_class.return_value = mock_excel
            
            
            
            # 创建标准化的商品数据
            primary_product = ProductInfo(
                product_id="primary_123",
                green_price=100.0,
                black_price=120.0,
                source_price=50.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0
            )
            
            mock_orchestrator = Mock()
            
            # 设置不同的返回值：第一次调用（店铺分析），第二次调用（商品分析）
            mock_orchestrator.scrape_with_orchestration.side_effect = [
                # 第一次调用：店铺分析，返回商品列表
                ScrapingResult.create_success({
                    'products': [
                        {
                            'product_id': 'primary_123',
                            'ozonUrl': 'https://www.ozon.ru/product/primary-123/',
                            'brand_name': 'Primary Brand',
                            'sku': 'PRIMARY-SKU-001'
                        }
                    ]
                }),
                # 第二次调用：商品分析，返回完整商品数据
                ScrapingResult.create_success({
                    'primary_product': primary_product,
                    'competitor_product': None,
                    'competitors_list': []
                })
            ]
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 设置利润评估返回，同时保持 prepare_for_profit_calculation 方法可用
            mock_profit = Mock()
            mock_profit.evaluate_product_profit.return_value = {
                'profit_rate': 30.0,
                'is_profitable': True,
                'source_price': 50.0,
                'selling_price': 100.0,
                'product_info': primary_product
            }
            
            # 让 prepare_for_profit_calculation 返回真实的处理结果
            def mock_prepare_for_profit_calculation(product):
                if product.green_price:
                    product.list_price = product.green_price * 0.95
                elif product.black_price:
                    product.list_price = product.black_price * 0.95
                return product
            
            mock_profit.prepare_for_profit_calculation.side_effect = mock_prepare_for_profit_calculation
            mock_profit_class.return_value = mock_profit
            
            # 创建选择器
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 执行处理
            result = selector.process_stores()
            
            # 验证数据流
            self.assertEqual(result.total_stores, 1)
            
            # 验证调用链
            mock_orchestrator.scrape_with_orchestration.assert_called()
            mock_profit.evaluate_product_profit.assert_called()
            
            # 验证传递给利润评估器的数据
            call_args = mock_profit.evaluate_product_profit.call_args
            passed_product = call_args[0][0]  # 第一个参数
            
            # 验证数据完整性
            self.assertEqual(passed_product.product_id, "primary_123")
            self.assertEqual(passed_product.list_price, 95.0)  # 100 * 0.95
            self.assertFalse(passed_product.is_competitor_selected)


if __name__ == '__main__':
    unittest.main()