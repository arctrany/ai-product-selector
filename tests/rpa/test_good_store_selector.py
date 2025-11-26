"""
GoodStoreSelector测试

测试good_store_selector.py的核心功能，包括店铺处理、商品处理、Excel操作等
"""

import pytest
import sys
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime

from good_store_selector import GoodStoreSelector, BatchProcessingResult
from common.models.excel_models import ExcelStoreData
from common.models.business_models import StoreInfo, ProductInfo, StoreAnalysisResult
from common.models.enums import GoodStoreFlag, StoreStatus
from common.config.base_config import GoodStoreSelectorConfig

class TestGoodStoreSelectorInitialization:
    """测试GoodStoreSelector初始化"""
    
    @patch('good_store_selector.ExcelStoreProcessor')
    @patch('good_store_selector.ProfitEvaluator')
    @patch('good_store_selector.get_global_scraping_orchestrator')
    def test_initialization_success(self, mock_get_orchestrator, mock_profit_evaluator, mock_excel_processor):
        """测试成功初始化"""
        # Mock组件
        mock_excel_instance = MagicMock()
        mock_excel_processor.return_value = mock_excel_instance
        
        mock_profit_instance = MagicMock()
        mock_profit_evaluator.return_value = mock_profit_instance
        
        mock_orchestrator_instance = MagicMock()
        mock_get_orchestrator.return_value = mock_orchestrator_instance
        
        # 创建配置
        config = GoodStoreSelectorConfig()
        
        # 执行测试
        selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
        
        # 验证
        assert selector.excel_file_path == "test.xlsx"
        assert selector.profit_calculator_path == "calc.xlsx"
        assert selector.config == config
        mock_excel_processor.assert_called_once_with("test.xlsx", config)
        mock_profit_evaluator.assert_called_once_with("calc.xlsx", config)
        mock_get_orchestrator.assert_called_once()
    
    @patch('good_store_selector.ExcelStoreProcessor')
    def test_initialization_failure(self, mock_excel_processor):
        """测试初始化失败"""
        # Mock异常
        mock_excel_processor.side_effect = Exception("初始化失败")
        
        # 创建配置
        config = GoodStoreSelectorConfig()
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="初始化失败"):
            GoodStoreSelector("test.xlsx", "calc.xlsx", config)

class TestStoreProcessing:
    """测试店铺处理功能"""
    
    def setup_method(self):
        """测试前准备"""
        # Mock配置
        self.config = GoodStoreSelectorConfig()
        
        # Mock组件
        self.mock_excel_processor = MagicMock()
        self.mock_profit_evaluator = MagicMock()
        self.mock_orchestrator = MagicMock()
        self.mock_store_evaluator = MagicMock()
        self.mock_error_factory = MagicMock()
        
        # 创建selector实例
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'), \
             patch('good_store_selector.get_global_scraping_orchestrator'), \
             patch('good_store_selector.StoreEvaluator'), \
             patch('good_store_selector.ErrorResultFactory'):
            
            self.selector = GoodStoreSelector("test.xlsx", "calc.xlsx", self.config)
            
            # 手动设置mock组件
            self.selector.excel_processor = self.mock_excel_processor
            self.selector.profit_evaluator = self.mock_profit_evaluator
            self.selector.scraping_orchestrator = self.mock_orchestrator
            self.selector.store_evaluator = self.mock_store_evaluator
            self.selector.error_factory = self.mock_error_factory
    
    def test_load_pending_stores_select_shops_mode(self):
        """测试select-shops模式加载待处理店铺"""
        # 设置模式
        self.selector.config.selection_mode = 'select-shops'
        
        # Mock数据
        mock_stores = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.EMPTY, StoreStatus.PENDING)
        ]
        
        self.mock_excel_processor.read_store_data.return_value = mock_stores
        self.mock_excel_processor.filter_pending_stores.return_value = [mock_stores[1]]
        
        # 执行测试
        result = self.selector._load_pending_stores()
        
        # 验证
        self.mock_excel_processor.read_store_data.assert_called_once()
        self.mock_excel_processor.filter_pending_stores.assert_called_once_with(mock_stores)
        assert len(result) == 1
        assert result[0].store_id == "STORE002"
    
    def test_load_pending_stores_select_goods_mode(self):
        """测试select-goods模式加载待处理店铺"""
        # 设置模式
        self.selector.config.selection_mode = 'select-goods'
        
        # Mock数据
        mock_stores = [
            ExcelStoreData(1, "123456", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),  # 数字ID
            ExcelStoreData(2, "abc123", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),  # 非数字ID
            ExcelStoreData(3, "789012", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)   # 数字ID
        ]
        
        self.mock_excel_processor.read_store_data.return_value = mock_stores
        
        # 执行测试
        result = self.selector._load_pending_stores()
        
        # 验证
        self.mock_excel_processor.read_store_data.assert_called_once()
        assert len(result) == 2  # 只有数字ID的店铺
        assert result[0].store_id == "123456"
        assert result[1].store_id == "789012"
        # 验证状态被重置
        assert all(store.is_good_store == GoodStoreFlag.EMPTY for store in result)
        assert all(store.status == StoreStatus.EMPTY for store in result)
    
    def test_process_single_store_select_shops_success(self):
        """测试select-shops模式成功处理单个店铺"""
        # 设置模式
        self.selector.config.selection_mode = 'select-shops'
        
        # Mock数据
        store_data = ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        
        # Mock抓取结果
        mock_scrape_result = MagicMock()
        mock_scrape_result.success = True
        mock_scrape_result.data = {
            'sales_data': {
                'sold_30days': 1000000.0,
                'sold_count_30days': 500,
                'daily_avg_sold': 16666.67
            },
            'products': [
                {
                    'product_id': 'P001',
                    'image_url': 'http://example.com/image1.jpg',
                    'brand_name': 'Brand1',
                    'sku': 'SKU001'
                }
            ]
        }
        self.mock_orchestrator.scrape_with_orchestration.return_value = mock_scrape_result
        
        # Mock商品处理结果
        mock_product_evaluations = [
            {
                'product_id': 'P001',
                'is_profitable': True,
                'profit_rate': 25.0
            }
        ]
        self.selector._process_products = MagicMock(return_value=mock_product_evaluations)
        
        # Mock店铺评估结果
        mock_store_result = MagicMock()
        mock_store_result.store_info.is_good_store = GoodStoreFlag.YES
        mock_store_result.store_info.status = StoreStatus.PROCESSED
        self.mock_store_evaluator.evaluate_store.return_value = mock_store_result
        
        # 执行测试
        result = self.selector._process_single_store(store_data)
        
        # 验证
        assert result == mock_store_result
        self.mock_orchestrator.scrape_with_orchestration.assert_called_once()
        self.selector._process_products.assert_called_once()
        self.mock_store_evaluator.evaluate_store.assert_called_once()
    
    def test_process_single_store_select_goods_success(self):
        """测试select-goods模式成功处理单个店铺"""
        # 设置模式
        self.selector.config.selection_mode = 'select-goods'
        
        # Mock数据
        store_data = ExcelStoreData(1, "123456", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        
        # Mock抓取结果
        mock_scrape_result = MagicMock()
        mock_scrape_result.success = True
        mock_scrape_result.data = {
            'products': [
                {
                    'product_id': 'P001',
                    'image_url': 'http://example.com/image1.jpg',
                    'brand_name': 'Brand1',
                    'sku': 'SKU001'
                }
            ]
        }
        self.mock_orchestrator.scrape_with_orchestration.return_value = mock_scrape_result
        
        # Mock商品处理结果
        mock_product_evaluations = [
            {
                'product_id': 'P001',
                'is_profitable': True,
                'profit_rate': 25.0
            }
        ]
        self.selector._process_products = MagicMock(return_value=mock_product_evaluations)
        
        # Mock店铺评估结果
        mock_store_result = MagicMock()
        mock_store_result.store_info.is_good_store = GoodStoreFlag.YES
        mock_store_result.store_info.status = StoreStatus.PROCESSED
        self.mock_store_evaluator.evaluate_store.return_value = mock_store_result
        
        # 执行测试
        result = self.selector._process_single_store(store_data)
        
        # 验证
        assert result == mock_store_result
        self.mock_orchestrator.scrape_with_orchestration.assert_called_once()
        self.selector._process_products.assert_called_once()
        self.mock_store_evaluator.evaluate_store.assert_called_once()
    
    def test_process_single_store_scraping_failure(self):
        """测试抓取失败时处理单个店铺"""
        # Mock数据
        store_data = ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        
        # Mock抓取失败
        mock_scrape_result = MagicMock()
        mock_scrape_result.success = False
        mock_scrape_result.error_message = "抓取失败"
        self.mock_orchestrator.scrape_with_orchestration.return_value = mock_scrape_result
        
        # Mock错误工厂
        mock_error_result = MagicMock()
        self.mock_error_factory.create_failed_store_result.return_value = mock_error_result
        
        # 执行测试
        result = self.selector._process_single_store(store_data)
        
        # 验证
        assert result == mock_error_result
        self.mock_error_factory.create_failed_store_result.assert_called_once_with("STORE001")
    
    # def test_process_products_success(self):
    #     """测试成功处理商品列表"""
    #     # Mock商品数据
    #     products = [
    #         ProductInfo(
    #             product_id='P001',
    #             image_url='http://example.com/image1.jpg',
    #             brand_name='Brand1',
    #             sku='SKU001'
    #         ),
    #         ProductInfo(
    #             product_id='P002',
    #             image_url='http://example.com/image2.jpg',
    #             brand_name='Brand2',
    #             sku='SKU002'
    #         )
    #     ]
    #
    #     # Mock价格抓取
    #     self.selector._scrape_product_basics = MagicMock()
    #
    #     # Mock ERP数据抓取
    #     self.selector._scrape_erp_data = MagicMock()
    #
    #     # 执行测试
    #     result = self.selector._process_products(products)
    #
    #     # 验证
    #     assert result == []  # 当前实现中未完成利润评估部分
    #     self.selector._scrape_erp_data.assert_any_call(products[0])
    #     self.selector._scrape_erp_data.assert_any_call(products[1])
    
    def test_process_products_empty_list(self):
        """测试处理空商品列表"""
        # 执行测试
        result = self.selector._process_products([])
        
        # 验证
        assert result == []
    
    def test_process_products_with_missing_image_url(self):
        """测试处理缺少图片URL的商品"""
        # Mock商品数据
        products = [
            ProductInfo(
                product_id='P001',
                image_url='',  # 空图片URL
                brand_name='Brand1',
                sku='SKU001'
            )
        ]
        
        # 执行测试
        result = self.selector._process_products(products)
        
        # 验证
        assert result == []


class TestExcelOperations:
    """测试Excel操作功能"""
    
    def setup_method(self):
        """测试前准备"""
        # Mock配置
        self.config = GoodStoreSelectorConfig()
        
        # Mock组件
        self.mock_excel_processor = MagicMock()
        
        # 创建selector实例
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'), \
             patch('good_store_selector.get_global_scraping_orchestrator'), \
             patch('good_store_selector.StoreEvaluator'), \
             patch('good_store_selector.ErrorResultFactory'):
            
            self.selector = GoodStoreSelector("test.xlsx", "calc.xlsx", self.config)
            self.selector.excel_processor = self.mock_excel_processor
    
    def test_update_excel_results_success(self):
        """测试成功更新Excel结果"""
        # Mock数据
        pending_stores = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.YES, StoreStatus.PROCESSED),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.NO, StoreStatus.PROCESSED)
        ]
        
        store_results = []
        for store_data in pending_stores:
            mock_result = MagicMock()
            mock_result.store_info = store_data
            store_results.append(mock_result)
        
        # 执行测试
        self.selector._update_excel_results(pending_stores, store_results)
        
        # 验证
        self.mock_excel_processor.batch_update_stores.assert_called_once()
        self.mock_excel_processor.save_changes.assert_called_once()
    
    def test_simulate_excel_update_dryrun(self):
        """测试模拟Excel更新（dryrun模式）"""
        # Mock数据
        pending_stores = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.YES, StoreStatus.PROCESSED),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.NO, StoreStatus.PROCESSED)
        ]
        
        store_results = []
        for store_data in pending_stores:
            mock_result = MagicMock()
            mock_result.store_info = store_data
            store_results.append(mock_result)
        
        # 执行测试
        self.selector._simulate_excel_update(pending_stores, store_results)
        
        # 验证
        self.mock_excel_processor.batch_update_stores.assert_not_called()
        self.mock_excel_processor.save_changes.assert_not_called()

class TestBatchProcessing:
    """测试批量处理功能"""
    
    def setup_method(self):
        """测试前准备"""
        # Mock配置
        self.config = GoodStoreSelectorConfig()
        
        # 创建selector实例
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'), \
             patch('good_store_selector.get_global_scraping_orchestrator'), \
             patch('good_store_selector.StoreEvaluator'), \
             patch('good_store_selector.ErrorResultFactory'):
            
            self.selector = GoodStoreSelector("test.xlsx", "calc.xlsx", self.config)
    
    @patch.object(GoodStoreSelector, '_initialize_components')
    @patch.object(GoodStoreSelector, '_load_pending_stores')
    @patch.object(GoodStoreSelector, '_process_single_store')
    @patch.object(GoodStoreSelector, '_update_excel_results')
    @patch.object(GoodStoreSelector, '_cleanup_components')
    def test_process_stores_success(self, mock_cleanup, mock_update_excel, mock_process_single, 
                                   mock_load_stores, mock_initialize):
        """测试成功批量处理店铺"""
        # Mock组件初始化
        self.selector.excel_processor = MagicMock()
        self.selector.profit_evaluator = MagicMock()
        self.selector.scraping_orchestrator = MagicMock()
        
        # Mock加载待处理店铺
        mock_pending_stores = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        ]
        mock_load_stores.return_value = mock_pending_stores
        
        # Mock处理单个店铺结果
        mock_store_result1 = MagicMock()
        mock_store_result1.store_info.status = StoreStatus.PROCESSED
        mock_store_result1.store_info.is_good_store = GoodStoreFlag.YES
        mock_store_result1.total_products = 10
        mock_store_result1.profitable_products = 5
        
        mock_store_result2 = MagicMock()
        mock_store_result2.store_info.status = StoreStatus.PROCESSED
        mock_store_result2.store_info.is_good_store = GoodStoreFlag.NO
        mock_store_result2.total_products = 8
        mock_store_result2.profitable_products = 2
        
        mock_process_single.side_effect = [mock_store_result1, mock_store_result2]
        
        # 执行测试
        result = self.selector.process_stores()
        
        # 验证
        assert isinstance(result, BatchProcessingResult)
        assert result.total_stores == 2
        assert result.processed_stores == 2
        assert result.good_stores == 1
        assert result.failed_stores == 0
        assert result.total_products == 18
        assert result.profitable_products == 7
        assert len(result.store_results) == 2
    
    @patch.object(GoodStoreSelector, '_initialize_components')
    @patch.object(GoodStoreSelector, '_load_pending_stores')
    @patch.object(GoodStoreSelector, '_process_single_store')
    @patch.object(GoodStoreSelector, '_update_excel_results')
    @patch.object(GoodStoreSelector, '_cleanup_components')
    def test_process_stores_with_failures(self, mock_cleanup, mock_update_excel, mock_process_single, 
                                         mock_load_stores, mock_initialize):
        """测试批量处理店铺时有失败情况"""
        # Mock组件初始化
        self.selector.excel_processor = MagicMock()
        self.selector.profit_evaluator = MagicMock()
        self.selector.scraping_orchestrator = MagicMock()
        
        # Mock加载待处理店铺
        mock_pending_stores = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        ]
        mock_load_stores.return_value = mock_pending_stores
        
        # Mock处理单个店铺结果 - 第一个成功，第二个失败
        mock_store_result1 = MagicMock()
        mock_store_result1.store_info.status = StoreStatus.PROCESSED
        mock_store_result1.store_info.is_good_store = GoodStoreFlag.YES
        mock_store_result1.total_products = 10
        mock_store_result1.profitable_products = 5
        
        mock_process_single.side_effect = [mock_store_result1, Exception("处理失败")]
        
        # 执行测试
        result = self.selector.process_stores()
        
        # 验证
        assert isinstance(result, BatchProcessingResult)
        assert result.total_stores == 2
        assert result.processed_stores == 1
        assert result.good_stores == 1
        assert result.failed_stores == 1
        assert result.total_products == 10
        assert result.profitable_products == 5
        assert len(result.store_results) == 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
