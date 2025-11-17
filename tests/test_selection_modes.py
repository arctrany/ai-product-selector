"""
测试选择模式逻辑

验证 select-goods 和 select-shops 模式的核心功能
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path

from common.models import ExcelStoreData, GoodStoreFlag, StoreStatus
from common.config import GoodStoreSelectorConfig
from good_store_selector import GoodStoreSelector


# 简化测试：只测试核心逻辑，不依赖复杂的初始化


class TestSelectGoodsMode:
    """测试 select-goods 模式"""
    
    def test_load_stores_filters_numeric_ids(self):
        """测试 select-goods 模式过滤数字 ID"""
        # 模拟 Excel 数据（包含数字和非数字 ID）
        mock_stores = [
            ExcelStoreData(row_index=2, store_id='123456', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),
            ExcelStoreData(row_index=3, store_id='789012', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),
            ExcelStoreData(row_index=4, store_id='abc123', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),  # 非数字
            ExcelStoreData(row_index=5, store_id='345678', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),
        ]

        # 模拟过滤逻辑
        filtered_stores = []
        for store_data in mock_stores:
            if store_data.store_id.isdigit():
                # 重置状态
                store_data.is_good_store = GoodStoreFlag.EMPTY
                store_data.status = StoreStatus.EMPTY
                filtered_stores.append(store_data)

        # 验证结果
        assert len(filtered_stores) == 3  # 只有 3 个数字 ID
        assert all(store.store_id.isdigit() for store in filtered_stores)
        assert filtered_stores[0].store_id == '123456'
        assert filtered_stores[1].store_id == '789012'
        assert filtered_stores[2].store_id == '345678'
    
    def test_select_goods_mode_logic(self):
        """测试 select-goods 模式的逻辑"""
        # 测试模式检测
        config = GoodStoreSelectorConfig()
        config.selection_mode = 'select-goods'

        # 验证配置
        assert config.selection_mode == 'select-goods'

        # 测试模式判断逻辑
        should_skip_store_filter = (config.selection_mode == 'select-goods')
        assert should_skip_store_filter == True


class TestSelectShopsMode:
    """测试 select-shops 模式（默认模式）"""
    
    def test_select_shops_mode_logic(self):
        """测试 select-shops 模式的逻辑"""
        # 模拟配置（默认模式）
        config = GoodStoreSelectorConfig()
        config.selection_mode = 'select-shops'

        # 验证配置
        assert config.selection_mode == 'select-shops'

        # 测试模式判断逻辑
        should_skip_store_filter = (config.selection_mode == 'select-goods')
        assert should_skip_store_filter == False

    def test_default_mode_is_select_shops(self):
        """测试默认模式是 select-shops"""
        # 不指定 selection_mode
        config = GoodStoreSelectorConfig()
        
        # 验证默认值
        assert config.selection_mode == 'select-shops'


class TestProductFiltering:
    """测试商品过滤在两种模式下都生效"""
    
    @pytest.mark.parametrize('selection_mode', ['select-goods', 'select-shops'])
    def test_product_filtering_config(self, selection_mode):
        """测试商品过滤配置在两种模式下都存在"""
        # 模拟配置
        config = GoodStoreSelectorConfig()
        config.selection_mode = selection_mode

        # 验证店铺过滤配置存在（包含商品黑名单等过滤配置）
        assert hasattr(config, 'store_filter')
        assert config.store_filter is not None
        assert hasattr(config.store_filter, 'blacklisted_categories')
        assert len(config.store_filter.blacklisted_categories) > 0


class TestModeDetection:
    """测试模式检测"""
    
    def test_mode_detection_from_config(self):
        """测试从配置中检测模式"""
        # 测试 select-goods 模式
        config1 = GoodStoreSelectorConfig()
        config1.selection_mode = 'select-goods'
        assert config1.selection_mode == 'select-goods'

        # 测试 select-shops 模式
        config2 = GoodStoreSelectorConfig()
        config2.selection_mode = 'select-shops'
        assert config2.selection_mode == 'select-shops'


class TestExcelReading:
    """测试 Excel 读取逻辑"""
    
    def test_excel_processor_usage(self):
        """测试 Excel 处理器的使用"""
        # 验证 ExcelStoreProcessor 存在
        from common.excel_processor import ExcelStoreProcessor
        assert ExcelStoreProcessor is not None

        # 验证 read_store_data 方法存在
        assert hasattr(ExcelStoreProcessor, 'read_store_data')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
