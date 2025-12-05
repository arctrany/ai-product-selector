"""
Mock策略和测试隔离最佳实践测试

测试Mock策略和测试隔离的最佳实践
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.services.good_store_selector import GoodStoreSelector
from common.models.excel_models import ExcelStoreData
from common.models.enums import GoodStoreFlag, StoreStatus
from common.config.base_config import GoodStoreSelectorConfig

class TestMockStrategies:
    """测试Mock策略"""
    
    def test_patch_decorator_isolation(self):
        """测试使用patch装饰器的隔离性"""
        # 使用patch装饰器确保隔离
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
            
            # 执行测试
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 验证Mock被正确调用
            mock_excel_processor.assert_called_once_with("test.xlsx", config)
            mock_profit_evaluator.assert_called_once_with("calc.xlsx", config)
            mock_get_orchestrator.assert_called_once()
            
            # 验证组件被正确设置
            assert selector.excel_processor == mock_excel_instance
            assert selector.profit_evaluator == mock_profit_instance
            assert selector.scraping_orchestrator == mock_orchestrator_instance
    
    def test_context_manager_isolation(self):
        """测试使用context manager的隔离性"""
        # 使用context manager确保隔离
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
            
            # 执行测试
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 验证Mock被正确调用
            mock_excel_processor.assert_called_once_with("test.xlsx", config)
            mock_profit_evaluator.assert_called_once_with("calc.xlsx", config)
            mock_get_orchestrator.assert_called_once()
    
    def test_mock_chaining_and_assertions(self):
        """测试Mock链式调用和断言"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            # Mock链式调用
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_excel_processor.return_value.workbook = mock_workbook
            
            # 创建配置
            config = GoodStoreSelectorConfig()
            
            # 执行测试
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 验证链式调用
            mock_excel_processor.assert_called_once_with("test.xlsx", config)
            assert selector.excel_processor.workbook == mock_workbook
            assert selector.excel_processor.workbook.active == mock_worksheet
    
    def test_mock_return_values_and_side_effects(self):
        """测试Mock返回值和副作用"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            # 设置返回值
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            # 设置方法返回值
            mock_store_data = [
                ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
            ]
            mock_excel_instance.read_store_data.return_value = mock_store_data
            
            # 设置副作用（异常）
            mock_excel_instance.validate_excel_format.side_effect = ValueError("格式错误")
            
            # 创建配置
            config = GoodStoreSelectorConfig()
            
            # 执行测试
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 验证返回值
            result = selector.excel_processor.read_store_data()
            assert result == mock_store_data
            
            # 验证副作用
            with pytest.raises(ValueError, match="格式错误"):
                selector.excel_processor.validate_excel_format()
    
    def test_mock_property_and_attribute_access(self):
        """测试Mock属性和特性访问"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            # Mock属性
            mock_excel_instance = MagicMock()
            mock_excel_instance.file_path = "test.xlsx"
            mock_excel_instance.is_valid = True
            mock_excel_processor.return_value = mock_excel_instance
            
            # 创建配置
            config = GoodStoreSelectorConfig()
            
            # 执行测试
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 验证属性访问
            assert selector.excel_processor.file_path == "test.xlsx"
            assert selector.excel_processor.is_valid is True

class TestTestIsolation:
    """测试隔离性"""
    
    def test_fixture_isolation(self, tmp_path):
        """测试使用pytest fixture的隔离性"""
        # 使用tmp_path fixture创建隔离的临时目录
        test_file = tmp_path / "test.xlsx"
        test_file.write_text("test content")
        
        assert test_file.exists()
        assert test_file.read_text() == "test content"
        
        # 这个文件只在这个测试函数中存在
        # 其他测试函数无法访问这个路径
    
    def test_mock_isolation_between_tests(self):
        """测试Mock在不同测试间的隔离性"""
        # 这个测试不会影响其他测试，因为没有全局Mock
        
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            config = GoodStoreSelectorConfig()
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 验证Mock被正确设置
            assert selector.excel_processor == mock_excel_instance
    
    def test_state_isolation(self):
        """测试状态隔离"""
        # 每个测试函数都应该从干净的状态开始
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'), \
             patch('good_store_selector.get_global_scraping_orchestrator'):
            
            config = GoodStoreSelectorConfig()
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 修改selector的状态
            selector.processing_stats['test_counter'] = 1
            
            # 验证状态修改
            assert selector.processing_stats['test_counter'] == 1
    
    def test_test_data_isolation(self):
        """测试测试数据隔离"""
        # 使用独立的测试数据避免干扰
        
        test_stores = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.EMPTY, StoreStatus.PENDING)
        ]
        
        # 处理测试数据
        processed_stores = [store for store in test_stores 
                           if store.status in [StoreStatus.EMPTY, StoreStatus.PENDING]]
        
        # 验证处理结果不影响原始数据
        assert len(processed_stores) == 2
        assert len(test_stores) == 2  # 原始数据未被修改

class TestAdvancedMockTechniques:
    """测试高级Mock技术"""
    
    def test_mock_multiple_calls_with_different_returns(self):
        """测试多次调用返回不同值"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            # 设置多次调用返回不同值
            mock_excel_instance.get_statistics.side_effect = [
                {'total_stores': 10, 'processed_stores': 5},
                {'total_stores': 10, 'processed_stores': 8},
                {'total_stores': 10, 'processed_stores': 10}
            ]
            
            config = GoodStoreSelectorConfig()
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 验证多次调用返回不同值
            stats1 = selector.excel_processor.get_statistics()
            stats2 = selector.excel_processor.get_statistics()
            stats3 = selector.excel_processor.get_statistics()
            
            assert stats1['processed_stores'] == 5
            assert stats2['processed_stores'] == 8
            assert stats3['processed_stores'] == 10
    
    def test_mock_assert_called_with_specific_args(self):
        """测试Mock断言特定参数调用"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            config = GoodStoreSelectorConfig()
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 调用方法
            test_store = ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
            selector.excel_processor.update_store_status(test_store, GoodStoreFlag.YES, StoreStatus.PROCESSED)
            
            # 验证特定参数调用
            selector.excel_processor.update_store_status.assert_called_with(
                test_store, GoodStoreFlag.YES, StoreStatus.PROCESSED
            )
    
    def test_mock_assert_called_once_with(self):
        """测试Mock断言仅调用一次"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            config = GoodStoreSelectorConfig()
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 调用方法一次
            selector.excel_processor.validate_excel_format()
            
            # 验证仅调用一次
            selector.excel_processor.validate_excel_format.assert_called_once()
    
    def test_mock_reset_mock(self):
        """测试重置Mock"""
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_processor:
            mock_excel_instance = MagicMock()
            mock_excel_processor.return_value = mock_excel_instance
            
            config = GoodStoreSelectorConfig()
            selector = GoodStoreSelector("test.xlsx", "calc.xlsx", config)
            
            # 调用方法
            selector.excel_processor.validate_excel_format()
            
            # 验证调用
            assert selector.excel_processor.validate_excel_format.call_count == 1
            
            # 重置Mock
            selector.excel_processor.validate_excel_format.reset_mock()
            
            # 验证重置后调用计数为0
            assert selector.excel_processor.validate_excel_format.call_count == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
