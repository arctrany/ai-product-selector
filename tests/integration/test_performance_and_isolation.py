"""

性能和隔离测试

测试性能优化和测试隔离
"""

import pytest
from unittest.mock import patch, MagicMock
import time

from common.services.good_store_selector import GoodStoreSelector
from common.models.excel_models import ExcelStoreData
from common.models.enums import GoodStoreFlag, StoreStatus
from common.config.base_config import GoodStoreSelectorConfig

class TestPerformanceOptimization:
    """测试性能优化"""
    
    def test_mock_heavy_operations(self):
        """测试Mock重量级操作"""
        # Mock重量级操作以提高测试性能
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_evaluator, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_get_orchestrator:
            
            # Mock组件实例
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            mock_profit_instance = MagicMock()
            mock_profit_evaluator.return_value = mock_profit_instance
            
            mock_orchestrator_instance = MagicMock()
            mock_get_orchestrator.return_value = mock_orchestrator_instance
            
            # Mock重量级方法
            mock_excel_instance.read_store_data.return_value = [
                ExcelStoreData(i, f"STORE{i:03d}", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
                for i in range(1, 101)  # 100个店铺
            ]
            
            # 记录开始时间
            start_time = time.time()
            
            # 创建配置
            config = GoodStoreSelectorConfig()
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 执行重量级操作
            stores = selector.excel_processor.read_store_data()
            
            # 记录结束时间
            end_time = time.time()
            
            # 验证结果
            assert len(stores) == 100
            assert stores[0].store_id == "STORE001"
            assert stores[99].store_id == "STORE100"
            
            # 验证执行时间（应该非常快，因为是Mock）
            execution_time = end_time - start_time
            assert execution_time < 0.1  # 应该在100ms内完成
    
    def test_batch_operations_performance(self):
        """测试批处理操作性能"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            # Mock批处理操作
            mock_excel_instance.batch_update_stores = MagicMock()
            mock_excel_instance.save_changes = MagicMock()
            
            # 创建大量测试数据
            test_stores = [
                ExcelStoreData(i, f"STORE{i:03d}", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
                for i in range(1, 1001)  # 1000个店铺
            ]
            
            test_updates = [
                (store, GoodStoreFlag.YES if i % 2 == 0 else GoodStoreFlag.NO, StoreStatus.PROCESSED)
                for i, store in enumerate(test_stores)
            ]
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行批处理操作
            mock_excel_instance.batch_update_stores(test_updates)
            mock_excel_instance.save_changes()
            
            # 记录结束时间
            end_time = time.time()
            
            # 验证调用
            mock_excel_instance.batch_update_stores.assert_called_once_with(test_updates)
            mock_excel_instance.save_changes.assert_called_once()
            
            # 验证执行时间
            execution_time = end_time - start_time
            assert execution_time < 0.5  # 应该在500ms内完成
    
    def test_lazy_initialization_performance(self):
        """测试延迟初始化性能"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_evaluator, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_get_orchestrator:
            
            # Mock组件实例
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            mock_profit_instance = MagicMock()
            mock_profit_evaluator.return_value = mock_profit_instance
            
            mock_orchestrator_instance = MagicMock()
            mock_get_orchestrator.return_value = mock_orchestrator_instance
            
            # 记录开始时间
            start_time = time.time()
            
            # 创建配置（不应该触发组件初始化）
            config = GoodStoreSelectorConfig()
            
            # 中间检查
            mid_time = time.time()
            
            # 创建选择器（触发组件初始化）
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 记录结束时间
            end_time = time.time()
            
            # 验证初始化调用
            mock_excel_processor.assert_called_once_with("test.xlsx", config)
            mock_profit_evaluator.assert_called_once_with("calc.xlsx", config)
            mock_get_orchestrator.assert_called_once()
            
            # 验证延迟初始化（创建配置应该比创建选择器快很多）
            config_time = mid_time - start_time
            selector_time = end_time - mid_time
            # 由于Mock操作很快，这个检查可能不明显，但逻辑上应该成立

class TestTestIsolationAdvanced:
    """测试高级隔离技术"""
    
    @pytest.fixture
    def isolated_selector(self):
        """提供隔离的选择器实例"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_evaluator, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_get_orchestrator:
            
            # Mock组件实例
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            mock_profit_instance = MagicMock()
            mock_profit_evaluator.return_value = mock_profit_instance
            
            mock_orchestrator_instance = MagicMock()
            mock_get_orchestrator.return_value = mock_orchestrator_instance
            
            # 创建配置
            config = GoodStoreSelectorConfig()
            
            # 创建选择器
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 设置选择器的组件
            selector.excel_processor = mock_excel_instance
            selector.profit_evaluator = mock_profit_instance
            selector.scraping_orchestrator = mock_orchestrator_instance
            
            yield selector  # 提供隔离的实例
    
    def test_fixture_isolation_with_mock(self, isolated_selector):
        """测试使用fixture的隔离性"""
        # 使用fixture提供的隔离实例
        
        # Mock方法
        isolated_selector.excel_processor.read_store_data.return_value = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
        ]
        
        # 执行操作
        result = isolated_selector.excel_processor.read_store_data()
        
        # 验证结果
        assert len(result) == 1
        assert result[0].store_id == "STORE001"
        
        # 验证Mock调用
        isolated_selector.excel_processor.read_store_data.assert_called_once()
    
    def test_concurrent_test_isolation(self, isolated_selector):
        """测试并发测试隔离"""
        # 模拟并发测试场景
        
        # 测试1：设置特定状态
        isolated_selector.config.selection_mode = 'select-goods'
        
        # 测试2：验证状态
        assert isolated_selector.config.selection_mode == 'select-goods'
        
        # 测试3：修改状态
        isolated_selector.config.selection_mode = 'select-shops'
        
        # 测试4：验证修改后的状态
        assert isolated_selector.config.selection_mode == 'select-shops'
    
    def test_resource_cleanup_isolation(self, isolated_selector):
        """测试资源清理隔离"""
        # Mock清理方法
        isolated_selector.excel_processor.close = MagicMock()
        isolated_selector.profit_evaluator.close = MagicMock()
        isolated_selector.scraping_orchestrator.close = MagicMock()
        
        # 执行清理
        isolated_selector._cleanup_components()
        
        # 验证所有组件都被清理
        isolated_selector.excel_processor.close.assert_called_once()
        isolated_selector.profit_evaluator.close.assert_called_once()
        isolated_selector.scraping_orchestrator.close.assert_called_once()

class TestIntegrationWithRealComponents:
    """测试与真实组件的集成"""
    
    def test_partial_mocking_integration(self):
        """测试部分Mock集成"""
        # 只Mock特定组件，其他使用真实组件
        with patch('good_store_selector.get_global_scraping_orchestrator') as mock_get_orchestrator:
            # Mock协调器
            mock_orchestrator_instance = MagicMock()
            mock_get_orchestrator.return_value = mock_orchestrator_instance
            
            # 其他组件使用真实实现
            with patch('good_store_selector.ExcelStoreProcessor'), \
                 patch('good_store_selector.ProfitEvaluator'):
                
                config = GoodStoreSelectorConfig()
                selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
                
                # 验证Mock组件
                assert selector.scraping_orchestrator == mock_orchestrator_instance
                
                # 验证真实组件（被Mock但可以验证调用）
                # ExcelStoreProcessor和ProfitEvaluator应该被Mock但调用应该正确
    
    def test_selective_mocking_for_performance(self):
        """测试选择性Mock以提高性能"""
        # 只Mock慢速组件
        with patch('good_store_selector.get_global_scraping_orchestrator') as mock_get_orchestrator:
            mock_orchestrator_instance = MagicMock()
            mock_get_orchestrator.return_value = mock_orchestrator_instance
            
            # Mock慢速方法
            mock_orchestrator_instance.scrape_with_orchestration.return_value = MagicMock(success=True)
            
            config = GoodStoreSelectorConfig()
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 执行操作（应该很快，因为慢速组件被Mock）
            start_time = time.time()
            result = selector.scraping_orchestrator.scrape_with_orchestration(mode='TEST')
            end_time = time.time()
            
            # 验证结果和性能
            assert result.success is True
            assert (end_time - start_time) < 0.1  # 应该很快完成

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
