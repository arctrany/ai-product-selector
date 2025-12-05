"""
Select-goods模式集成测试

测试select-goods模式下的完整流程，包括：
- 跳过跟卖逻辑
- 商品利润筛选
- 商品Excel输出
- dryrun模式
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os

from common.services.good_store_selector import GoodStoreSelector
from common.models.business_models import ProductInfo
from common.models.excel_models import ExcelStoreData, ExcelProductData
from common.models.scraping_result import ScrapingResult
from common.models.enums import GoodStoreFlag, StoreStatus
from common.config.base_config import GoodStoreSelectorConfig
from common.services.scraping_orchestrator import ScrapingMode


class TestSelectGoodsMode(unittest.TestCase):
    """Select-goods模式集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时文件
        self.temp_excel = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_calc = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_product = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        
        self.temp_excel.close()
        self.temp_calc.close()
        self.temp_product.close()
        
        # 创建配置
        self.config = GoodStoreSelectorConfig()
        self.config.selection_mode = 'select-goods'
        self.config.dryrun = False
    
    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.temp_excel.name)
            os.unlink(self.temp_calc.name)
            os.unlink(self.temp_product.name)
        except:
            pass
    
    def test_select_goods_mode_full_flow(self):
        """测试select-goods模式完整流程"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func, \
             patch('good_store_selector.ExcelProductWriter') as mock_product_writer_class:
            
            # 设置店铺Excel处理器
            mock_excel = Mock()
            mock_excel.read_store_data.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",  # 必须是数字ID
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel.filter_pending_stores.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",  # 必须是数字ID
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel_class.return_value = mock_excel
            
            # 创建产品对象
            products = [
                ProductInfo(
                    product_id="prod-001",
                    store_id="123456",
                    green_price=100.0,
                    source_price=50.0
                ),
                ProductInfo(
                    product_id="prod-002",
                    store_id="123456",
                    green_price=100.0,
                    source_price=80.0
                ),
                ProductInfo(
                    product_id="prod-003",
                    store_id="123456",
                    green_price=100.0,
                    source_price=60.0
                )
            ]
            
            # 设置利润评估器
            mock_profit = Mock()
            mock_profit.prepare_for_profit_calculation.side_effect = products
            
            evaluate_results = [
                # 第一个商品：利润率高
                {
                    'profit_rate': 35.0,
                    'is_profitable': True,
                    'source_price': 50.0,
                    'selling_price': 100.0,
                    'product_info': products[0]
                },
                # 第二个商品：利润率低
                {
                    'profit_rate': 10.0,
                    'is_profitable': False,
                    'source_price': 80.0,
                    'selling_price': 100.0,
                    'product_info': products[1]
                },
                # 第三个商品：利润率合格
                {
                    'profit_rate': 25.0,
                    'is_profitable': True,
                    'source_price': 60.0,
                    'selling_price': 100.0,
                    'product_info': products[2]
                }
            ]
            
            # 设置两次，一次用于prepare调用，一次用于evaluate调用
            mock_profit.evaluate_product_profit.side_effect = evaluate_results.copy()
            mock_profit_class.return_value = mock_profit
            
            # 设置协调器 - 需要模拟多次调用
            mock_orchestrator = Mock()
            # 第一次调用是获取店铺商品列表
            first_call = ScrapingResult.create_success({
                'products': [
                    {'product_id': 'prod-001', 'ozonUrl': 'https://ozon.ru/prod-001'},
                    {'product_id': 'prod-002', 'ozonUrl': 'https://ozon.ru/prod-002'},
                    {'product_id': 'prod-003', 'ozonUrl': 'https://ozon.ru/prod-003'}
                ]
            })
            # 后续调用是分析每个商品
            product_calls = []
            
            for i, product_id in enumerate(['prod-001', 'prod-002', 'prod-003']):
                product_calls.append(ScrapingResult.create_success({
                    'primary_product': products[i],
                    'competitor_product': None  # 没有竞品
                }))
            
            mock_orchestrator.scrape_with_orchestration.side_effect = [first_call] + product_calls
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 设置商品写入器
            mock_product_writer = Mock()
            mock_product_writer.batch_write_products.return_value = 2  # 2个商品写入成功
            mock_product_writer_class.return_value = mock_product_writer
            
            # 创建选择器
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 执行处理
            result = selector.process_stores()
            
            # 验证结果
            self.assertEqual(result.total_stores, 1)
            self.assertEqual(result.processed_stores, 1)
            
            # 验证调用了4次协调器（1次店铺分析 + 3次商品分析）
            self.assertEqual(mock_orchestrator.scrape_with_orchestration.call_count, 4)
            
            # 验证第一次协调器调用参数是店铺分析
            first_call_args = mock_orchestrator.scrape_with_orchestration.call_args_list[0]
            self.assertEqual(first_call_args[1]['mode'], ScrapingMode.STORE_ANALYSIS)
            
            # 验证利润评估被调用了3次（3个商品）
            self.assertEqual(mock_profit.evaluate_product_profit.call_count, 3)
            
            # 验证商品写入器被调用
            mock_product_writer.batch_write_products.assert_called_once()
            
            # 验证写入的商品数据（应该只有2个利润合格的商品）
            written_products = mock_product_writer.batch_write_products.call_args[0][0]
            self.assertEqual(len(written_products), 2)
            
            # 验证写入的商品ID
            written_ids = [p.product_id for p in written_products]
            self.assertIn("prod-001", written_ids)
            self.assertIn("prod-003", written_ids)
            self.assertNotIn("prod-002", written_ids)  # 利润率低的商品被过滤
    
    def test_skip_competitor_analysis_in_select_goods_mode(self):
        """测试select-goods模式跳过跟卖分析"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func, \
             patch('good_store_selector.ExcelProductWriter'):
            
            # 设置基本的mock
            mock_excel = Mock()
            mock_excel.read_store_data.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",  # 必须是数字ID
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel.filter_pending_stores.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",  # 必须是数字ID
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel_class.return_value = mock_excel
            
            # 设置协调器
            mock_orchestrator = Mock()
            # 第一次调用获取店铺商品
            first_call = ScrapingResult.create_success({
                'products': [{'product_id': 'prod-001', 'ozonUrl': 'https://ozon.ru/prod-001'}]
            })
            # 第二次调用分析商品
            test_product = ProductInfo(product_id="prod-001", store_id="123456")
            second_call = ScrapingResult.create_success({
                'primary_product': test_product,
                'competitor_product': None
            })
            mock_orchestrator.scrape_with_orchestration.side_effect = [first_call, second_call]
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 设置利润评估器
            mock_profit = Mock()
            mock_profit.prepare_for_profit_calculation.return_value = test_product
            mock_profit.evaluate_product_profit.return_value = {
                'profit_rate': 25.0,
                'is_profitable': True,
                'product_info': test_product
            }
            mock_profit_class.return_value = mock_profit
            
            # 创建选择器
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 执行处理
            result = selector.process_stores()
            
            # 验证调用了2次协调器（1次店铺分析 + 1次商品分析）
            self.assertEqual(mock_orchestrator.scrape_with_orchestration.call_count, 2)
            
            # 验证第一次调用是店铺分析
            first_call_args = mock_orchestrator.scrape_with_orchestration.call_args_list[0]
            self.assertEqual(first_call_args[1]['mode'], ScrapingMode.STORE_ANALYSIS)
            
            # 验证第二次调用是FULL_CHAIN模式（商品完整分析）
            second_call_args = mock_orchestrator.scrape_with_orchestration.call_args_list[1]
            self.assertEqual(second_call_args[0][0], ScrapingMode.FULL_CHAIN)
    
    def test_product_data_conversion(self):
        """测试商品数据转换"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func, \
             patch('good_store_selector.ExcelProductWriter') as mock_product_writer_class:
            
            # 设置基本的mock
            mock_excel = Mock()
            mock_excel.read_store_data.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",  # 必须是数字ID
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel.filter_pending_stores.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",  # 必须是数字ID
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel_class.return_value = mock_excel
            
            # 创建完整的商品信息
            test_product = ProductInfo(
                product_id="prod-001",
                store_id="123456",  # 需要设置store_id
                image_url="http://example.com/image.jpg",
                green_price=100.0,
                black_price=120.0,
                source_price=50.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0
            )
            
            # 设置协调器 - 需要模拟两次调用
            mock_orchestrator = Mock()
            # 第一次调用是获取店铺商品列表
            first_call = ScrapingResult.create_success({
                'products': [{'product_id': 'prod-001', 'ozonUrl': 'http://ozon.ru/product/001'}]
            })
            # 第二次调用是分析商品详情
            second_call = ScrapingResult.create_success({
                'primary_product': test_product,
                'competitor_product': None  # 没有竞品
            })
            mock_orchestrator.scrape_with_orchestration.side_effect = [first_call, second_call]
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 设置利润评估器
            mock_profit = Mock()
            mock_profit.prepare_for_profit_calculation.return_value = test_product
            mock_profit.evaluate_product_profit.return_value = {
                'profit_rate': 30.5,
                'profit_amount': 15.25,
                'is_profitable': True,
                'source_price': 50.0,
                'selling_price': 100.0,
                'product_info': test_product
            }
            mock_profit_class.return_value = mock_profit
            
            # 设置商品写入器
            mock_product_writer = Mock()
            mock_product_writer_class.return_value = mock_product_writer
            
            # 创建选择器
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 执行处理
            result = selector.process_stores()
            
            # 验证商品写入器被调用
            mock_product_writer.batch_write_products.assert_called_once()
            
            # 获取写入的商品数据
            written_products = mock_product_writer.batch_write_products.call_args[0][0]
            self.assertEqual(len(written_products), 1)
            
            # 验证数据转换正确
            product_data = written_products[0]
            self.assertIsInstance(product_data, ExcelProductData)
            self.assertEqual(product_data.store_id, "123456")
            self.assertEqual(product_data.product_id, "prod-001")
            self.assertEqual(product_data.product_name, None)  # ProductInfo没有name属性
            self.assertEqual(product_data.image_url, "http://example.com/image.jpg")
            self.assertEqual(product_data.green_price, 100.0)
            self.assertEqual(product_data.black_price, 120.0)
            self.assertEqual(product_data.source_price, 50.0)
            self.assertEqual(product_data.commission_rate, 0.15)
            self.assertEqual(product_data.weight, 500.0)
            self.assertEqual(product_data.length, 10.0)
            self.assertEqual(product_data.width, 8.0)
            self.assertEqual(product_data.height, 5.0)
            self.assertEqual(product_data.profit_rate, 30.5)
            self.assertEqual(product_data.profit_amount, 15.25)
    
    def test_dryrun_mode(self):
        """测试dryrun模式"""
        # 设置为dryrun模式
        self.config.dryrun = True
        
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func, \
             patch('good_store_selector.ExcelProductWriter') as mock_product_writer_class:
            
            # 设置基本的mock
            mock_excel = Mock()
            mock_excel.read_store_data.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",  # 必须是数字ID
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel.filter_pending_stores.return_value = [
                ExcelStoreData(
                    row_index=1,
                    store_id="123456",  # 必须是数字ID
                    is_good_store=GoodStoreFlag.EMPTY,
                    status=StoreStatus.EMPTY
                )
            ]
            mock_excel_class.return_value = mock_excel
            
            # 设置协调器
            mock_orchestrator = Mock()
            mock_orchestrator.scrape_with_orchestration.return_value = ScrapingResult.create_success({
                'products': [{'product_id': 'prod-001'}]
            })
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 设置利润评估器
            mock_profit = Mock()
            mock_profit.evaluate_product_profit.return_value = {
                'profit_rate': 25.0,
                'is_profitable': True,
                'product_info': ProductInfo(product_id="prod-001")
            }
            mock_profit_class.return_value = mock_profit
            
            # 设置商品写入器
            mock_product_writer = Mock()
            mock_product_writer_class.return_value = mock_product_writer
            
            # 创建选择器，传入dryrun配置
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 执行处理
            result = selector.process_stores()
            
            # 验证商品写入器接收到了dryrun配置
            # 注意：现在使用默认的 /var/folders/.../products_output.xlsx 路径
            mock_product_writer_class.assert_called()
            call_args = mock_product_writer_class.call_args
            # 验证配置参数包含dryrun=True
            self.assertTrue(call_args[0][1].dryrun)
            
            # 验证商品写入器的save_changes在dryrun模式下的行为
            # （这部分已经在ExcelProductWriter的单元测试中验证）
    
    def test_store_status_update_in_select_goods_mode(self):
        """测试select-goods模式下店铺状态更新"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func, \
             patch('good_store_selector.ExcelProductWriter'):
            
            # 设置店铺Excel处理器
            mock_excel = Mock()
            test_store = ExcelStoreData(
                row_index=1,
                store_id="123456",  # 必须是数字ID
                is_good_store=GoodStoreFlag.EMPTY,
                status=StoreStatus.EMPTY
            )
            mock_excel.read_store_data.return_value = [test_store]
            mock_excel.filter_pending_stores.return_value = [test_store]
            mock_excel_class.return_value = mock_excel
            
            # 设置协调器返回商品
            mock_orchestrator = Mock()
            # 第一次调用获取店铺商品
            first_call = ScrapingResult.create_success({
                'products': [
                    {'product_id': 'prod-001', 'ozonUrl': 'https://ozon.ru/prod-001'},
                    {'product_id': 'prod-002', 'ozonUrl': 'https://ozon.ru/prod-002'}
                ]
            })
            
            # 创建产品对象
            products = [
                ProductInfo(product_id="prod-001", store_id="123456"),
                ProductInfo(product_id="prod-002", store_id="123456")
            ]
            
            # 商品分析调用
            product_calls = [
                ScrapingResult.create_success({
                    'primary_product': products[0],
                    'competitor_product': None
                }),
                ScrapingResult.create_success({
                    'primary_product': products[1],
                    'competitor_product': None
                })
            ]
            
            mock_orchestrator.scrape_with_orchestration.side_effect = [first_call] + product_calls
            mock_orchestrator_func.return_value = mock_orchestrator
            
            # 设置利润评估器 - 一个商品利润合格，一个不合格
            mock_profit = Mock()
            mock_profit.prepare_for_profit_calculation.side_effect = products
            mock_profit.evaluate_product_profit.side_effect = [
                {
                    'profit_rate': 25.0,
                    'is_profitable': True,
                    'product_info': products[0]
                },
                {
                    'profit_rate': 10.0,
                    'is_profitable': False,
                    'product_info': products[1]
                }
            ]
            mock_profit_class.return_value = mock_profit
            
            # 创建选择器
            selector = GoodStoreSelector(
                excel_file_path=self.temp_excel.name,
                config=self.config
            )
            
            # 执行处理
            result = selector.process_stores()
            
            # 验证店铺状态更新
            mock_excel.batch_update_stores.assert_called_once()
            
            # 获取更新参数
            update_call = mock_excel.batch_update_stores.call_args[0][0]
            self.assertEqual(len(update_call), 1)
            
            # 验证更新内容
            store_data, flag, status = update_call[0]
            self.assertEqual(store_data.store_id, "123456")
            # 在select-goods模式下，店铺状态标记为NO（因为不是在评估店铺是否为好店）
            self.assertEqual(flag, GoodStoreFlag.NO)
            self.assertEqual(status, StoreStatus.PROCESSED)  # 使用PROCESSED而不是COMPLETED
    
    def test_error_handling_in_select_goods_mode(self):
        """测试select-goods模式下的错误处理"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_orchestrator_func, \
             patch('good_store_selector.ExcelProductWriter'):
            
            # 设置店铺Excel处理器
            mock_excel = Mock()
            test_store = ExcelStoreData(
                row_index=1,
                store_id="123456",  # 必须是数字ID
                is_good_store=GoodStoreFlag.EMPTY,
                status=StoreStatus.EMPTY
            )
            mock_excel.read_store_data.return_value = [test_store]
            mock_excel.filter_pending_stores.return_value = [test_store]
            mock_excel_class.return_value = mock_excel
            
            # 设置协调器返回失败
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
            
            # 验证结果
            self.assertEqual(result.failed_stores, 1)
            self.assertEqual(result.processed_stores, 0)  # 抓取失败的店铺不算已处理
            
            # 验证店铺状态更新为失败
            mock_excel.batch_update_stores.assert_called_once()
            update_call = mock_excel.batch_update_stores.call_args[0][0]
            store_data, flag, status = update_call[0]
            self.assertEqual(status, StoreStatus.FAILED)  # 使用FAILED而不是ERROR


if __name__ == '__main__':
    unittest.main()