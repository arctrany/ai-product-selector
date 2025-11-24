"""
选择模式集成测试

测试select-goods和select-shops模式的集成功能
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

from good_store_selector import GoodStoreSelector
from common.models.excel_models import ExcelStoreData
from common.models.enums import GoodStoreFlag, StoreStatus
from common.config.base_config import GoodStoreSelectorConfig

class TestSelectionModesIntegration:
    """测试选择模式集成"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建selector实例
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'), \
             patch('good_store_selector.get_global_scraping_orchestrator'), \
             patch('good_store_selector.StoreEvaluator'), \
             patch('good_store_selector.ErrorResultFactory'):
            
            self.config = GoodStoreSelectorConfig()
            self.selector = GoodStoreSelector("test.xlsx", "calc.xlsx", self.config)
    
    def test_select_shops_mode_full_flow(self):
        """测试select-shops模式完整流程"""
        # 设置模式
        self.selector.config.selection_mode = 'select-shops'
        
        # Mock组件
        self.selector.excel_processor = MagicMock()
        self.selector.scraping_orchestrator = MagicMock()
        self.selector.store_evaluator = MagicMock()
        
        # Mock加载待处理店铺
        mock_pending_stores = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        ]
        self.selector.excel_processor.read_store_data.return_value = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.EMPTY, StoreStatus.PENDING),
            ExcelStoreData(3, "STORE003", GoodStoreFlag.YES, StoreStatus.PROCESSED)
        ]
        self.selector.excel_processor.filter_pending_stores.return_value = mock_pending_stores
        
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
                    'image_url': 'http://example.com/image1.jpg'
                }
            ]
        }
        self.selector.scraping_orchestrator.scrape_with_orchestration.return_value = mock_scrape_result
        
        # Mock处理结果
        mock_store_result = MagicMock()
        mock_store_result.store_info.is_good_store = GoodStoreFlag.YES
        mock_store_result.store_info.status = StoreStatus.PROCESSED
        mock_store_result.total_products = 10
        mock_store_result.profitable_products = 5
        self.selector._process_single_store = MagicMock(return_value=mock_store_result)
        
        # 执行测试
        result = self.selector.process_stores()
        
        # 验证
        assert result.total_stores == 2
        assert result.processed_stores == 2
        assert result.good_stores == 2  # 两个店铺都是好店
        self.selector.scraping_orchestrator.scrape_with_orchestration.assert_called()
        # 验证使用了店铺过滤器
        call_args = self.selector.scraping_orchestration.call_args
        if call_args:
            assert 'store_filter_func' in call_args.kwargs
            assert call_args.kwargs['store_filter_func'] is not None
    
    def test_select_goods_mode_full_flow(self):
        """测试select-goods模式完整流程"""
        # 设置模式
        self.selector.config.selection_mode = 'select-goods'
        
        # Mock组件
        self.selector.excel_processor = MagicMock()
        self.selector.scraping_orchestrator = MagicMock()
        self.selector.store_evaluator = MagicMock()
        
        # Mock加载待处理店铺（只加载数字ID的店铺）
        mock_pending_stores = [
            ExcelStoreData(1, "123456", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
            ExcelStoreData(3, "789012", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        ]
        self.selector.excel_processor.read_store_data.return_value = [
            ExcelStoreData(1, "123456", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
            ExcelStoreData(2, "abc123", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),  # 非数字ID，应该被过滤
            ExcelStoreData(3, "789012", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        ]
        
        # Mock抓取结果
        mock_scrape_result = MagicMock()
        mock_scrape_result.success = True
        mock_scrape_result.data = {
            'products': [
                {
                    'product_id': 'P001',
                    'image_url': 'http://example.com/image1.jpg'
                }
            ]
        }
        self.selector.scraping_orchestrator.scrape_with_orchestration.return_value = mock_scrape_result
        
        # Mock处理结果
        mock_store_result = MagicMock()
        mock_store_result.store_info.is_good_store = GoodStoreFlag.YES
        mock_store_result.store_info.status = StoreStatus.PROCESSED
        mock_store_result.total_products = 8
        mock_store_result.profitable_products = 4
        self.selector._process_single_store = MagicMock(return_value=mock_store_result)
        
        # 执行测试
        result = self.selector.process_stores()
        
        # 验证
        assert result.total_stores == 2
        assert result.processed_stores == 2
        assert result.good_stores == 2  # 两个店铺都是好店
        self.selector.scraping_orchestrator.scrape_with_orchestration.assert_called()
        # 验证没有使用店铺过滤器（select-goods模式跳过店铺过滤）
        call_args = self.selector.scraping_orchestrator.scrape_with_orchestration.call_args
        if call_args:
            assert call_args.kwargs.get('store_filter_func') is None
    
    def test_mode_configuration_propagation(self):
        """测试模式配置传播"""
        # 测试select-shops模式
        config1 = GoodStoreSelectorConfig()
        config1.selection_mode = 'select-shops'
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'), \
             patch('good_store_selector.get_global_scraping_orchestrator'), \
             patch('good_store_selector.StoreEvaluator'), \
             patch('good_store_selector.ErrorResultFactory'):
            
            selector1 = GoodStoreSelector("test.xlsx", "calc.xlsx", config1)
            assert selector1.config.selection_mode == 'select-shops'
        
        # 测试select-goods模式
        config2 = GoodStoreSelectorConfig()
        config2.selection_mode = 'select-goods'
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'), \
             patch('good_store_selector.get_global_scraping_orchestrator'), \
             patch('good_store_selector.StoreEvaluator'), \
             patch('good_store_selector.ErrorResultFactory'):
            
            selector2 = GoodStoreSelector("test.xlsx", "calc.xlsx", config2)
            assert selector2.config.selection_mode == 'select-goods'
    
    def test_default_mode_is_select_shops(self):
        """测试默认模式是select-shops"""
        config = GoodStoreSelectorConfig()
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'), \
             patch('good_store_selector.get_global_scraping_orchestrator'), \
             patch('good_store_selector.StoreEvaluator'), \
             patch('good_store_selector.ErrorResultFactory'):
            
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            assert selector.config.selection_mode == 'select-shops'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
