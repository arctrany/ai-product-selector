"""
测试选择模式逻辑 - 真实场景测试

验证 select-goods 和 select-shops 模式的实际业务流程
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from pathlib import Path

from common.models import (
    ExcelStoreData, StoreInfo, ProductInfo, GoodStoreFlag, StoreStatus,
    ScrapingResult, StoreAnalysisResult, ProductAnalysisResult
)
from common.config import GoodStoreSelectorConfig
from good_store_selector import GoodStoreSelector


class TestSelectGoodsModeReal:
    """测试 select-goods 模式的真实场景"""
    
    @patch('good_store_selector.Path')
    def test_load_stores_for_goods_selection_with_real_flow(self, mock_path):
        """测试 select-goods 模式的完整店铺加载流程"""
        # 配置
        config = GoodStoreSelectorConfig()
        config.selection_mode = 'select-goods'
        
        # Mock 文件存在
        mock_path.return_value.exists.return_value = True
        
        # 创建 selector
        selector = GoodStoreSelector(
            excel_file_path='test.xlsx',
            profit_calculator_path='calc.xlsx',
            config=config
        )
        
        # Mock ExcelStoreProcessor
        mock_excel_processor = MagicMock()
        selector.excel_processor = mock_excel_processor
        
        # 模拟 Excel 数据（包含数字和非数字 ID）
        mock_stores = [
            ExcelStoreData(row_index=2, store_id='123456', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),
            ExcelStoreData(row_index=3, store_id='789012', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),
            ExcelStoreData(row_index=4, store_id='abc123', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),  # 非数字
            ExcelStoreData(row_index=5, store_id='', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),  # 空ID
            ExcelStoreData(row_index=6, store_id='345678', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),
        ]
        mock_excel_processor.read_store_data.return_value = mock_stores
        
        # 调用加载方法
        result = selector._load_stores_for_goods_selection()
        
        # 验证结果
        assert len(result) == 3  # 只有 3 个数字 ID
        assert all(store.store_id.isdigit() for store in result)
        assert result[0].store_id == '123456'
        assert result[1].store_id == '789012'
        assert result[2].store_id == '345678'
        
        # 验证状态被重置为 EMPTY（待处理）
        assert all(store.is_good_store == GoodStoreFlag.EMPTY for store in result)
        assert all(store.status == StoreStatus.EMPTY for store in result)
        
        # 验证调用了 read_store_data
        mock_excel_processor.read_store_data.assert_called_once()
    
    @patch('good_store_selector.Path')
    def test_process_single_store_skips_store_filtering(self, mock_path):
        """测试 select-goods 模式跳过店铺过滤"""
        # 配置
        config = GoodStoreSelectorConfig()
        config.selection_mode = 'select-goods'
        
        # Mock 文件存在
        mock_path.return_value.exists.return_value = True
        
        # 创建 selector
        selector = GoodStoreSelector(
            excel_file_path='test.xlsx',
            profit_calculator_path='calc.xlsx',
            config=config
        )
        
        # Mock 依赖
        selector.seerfar_scraper = MagicMock()
        selector.ozon_scraper = MagicMock()
        selector.erp_scraper = MagicMock()
        selector.store_evaluator = MagicMock()
        
        # 模拟店铺数据
        store_data = ExcelStoreData(
            row_index=2,
            store_id='123456',
            is_good_store=GoodStoreFlag.EMPTY,
            status=StoreStatus.EMPTY
        )
        
        # Mock _scrape_store_products 返回空列表（触发无商品逻辑）
        with patch.object(selector, '_scrape_store_products', return_value=([], None)):
            result = selector._process_single_store(store_data)
        
        # 验证 seerfar_scraper.scrape_store_sales_data 没有被调用（跳过店铺过滤）
        selector.seerfar_scraper.scrape_store_sales_data.assert_not_called()
        
        # 验证返回了无商品结果（无商品时状态为 PROCESSED）
        assert result.store_info.store_id == '123456'
        assert result.store_info.is_good_store == GoodStoreFlag.NO
        # 注意：无商品时状态应该是 PROCESSED，而不是 FAILED
        assert result.store_info.status == StoreStatus.PROCESSED


class TestSelectShopsModeReal:
    """测试 select-shops 模式的真实场景"""
    
    @patch('good_store_selector.Path')
    def test_load_pending_stores_with_filtering(self, mock_path):
        """测试 select-shops 模式使用过滤加载店铺"""
        # 配置（默认模式）
        config = GoodStoreSelectorConfig()
        config.selection_mode = 'select-shops'
        
        # Mock 文件存在
        mock_path.return_value.exists.return_value = True
        
        # 创建 selector
        selector = GoodStoreSelector(
            excel_file_path='test.xlsx',
            profit_calculator_path='calc.xlsx',
            config=config
        )
        
        # Mock ExcelStoreProcessor
        mock_excel_processor = MagicMock()
        selector.excel_processor = mock_excel_processor
        
        # 模拟所有店铺数据
        all_stores = [
            ExcelStoreData(row_index=2, store_id='123456', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.PENDING),
            ExcelStoreData(row_index=3, store_id='789012', is_good_store=GoodStoreFlag.YES, status=StoreStatus.PROCESSED),
            ExcelStoreData(row_index=4, store_id='345678', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.PENDING),
        ]
        mock_excel_processor.read_store_data.return_value = all_stores
        
        # 模拟过滤后的待处理店铺
        pending_stores = [
            ExcelStoreData(row_index=2, store_id='123456', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.PENDING),
            ExcelStoreData(row_index=4, store_id='345678', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.PENDING),
        ]
        mock_excel_processor.filter_pending_stores.return_value = pending_stores
        
        # 调用加载方法
        result = selector._load_pending_stores()
        
        # 验证结果
        assert len(result) == 2
        assert result[0].store_id == '123456'
        assert result[1].store_id == '345678'
        
        # 验证调用了过滤方法
        mock_excel_processor.read_store_data.assert_called_once()
        mock_excel_processor.filter_pending_stores.assert_called_once_with(all_stores)
    
    @patch('good_store_selector.FilterManager')
    @patch('good_store_selector.Path')
    def test_process_single_store_performs_store_filtering(self, mock_path, mock_filter_manager_class):
        """测试 select-shops 模式执行店铺过滤"""
        # 配置（默认模式）
        config = GoodStoreSelectorConfig()
        config.selection_mode = 'select-shops'
        
        # Mock 文件存在
        mock_path.return_value.exists.return_value = True
        
        # 创建 selector
        selector = GoodStoreSelector(
            excel_file_path='test.xlsx',
            profit_calculator_path='calc.xlsx',
            config=config
        )
        
        # Mock FilterManager
        mock_filter_manager = MagicMock()
        mock_filter_manager_class.return_value = mock_filter_manager
        mock_filter_manager.get_store_filter_func.return_value = MagicMock()
        
        # Mock 依赖
        selector.seerfar_scraper = MagicMock()
        
        # 模拟店铺销售数据抓取失败
        mock_result = ScrapingResult(
            success=False,
            data={},  # ScrapingResult 需要 data 参数
            error_message="店铺不符合筛选条件"
        )
        selector.seerfar_scraper.scrape_store_sales_data.return_value = mock_result
        
        # 模拟店铺数据
        store_data = ExcelStoreData(
            row_index=2,
            store_id='123456',
            is_good_store=GoodStoreFlag.EMPTY,
            status=StoreStatus.PENDING
        )
        
        # 调用处理方法
        result = selector._process_single_store(store_data)
        
        # 验证 seerfar_scraper.scrape_store_sales_data 被调用（执行店铺过滤）
        selector.seerfar_scraper.scrape_store_sales_data.assert_called_once()
        
        # 验证返回了失败结果
        assert result.store_info.store_id == '123456'
        assert result.store_info.is_good_store == GoodStoreFlag.NO
        assert result.store_info.status == StoreStatus.FAILED


class TestProductFilteringReal:
    """测试商品过滤在两种模式下的真实场景"""
    
    @pytest.mark.parametrize('selection_mode', ['select-goods', 'select-shops'])
    @patch('good_store_selector.FilterManager')
    @patch('good_store_selector.Path')
    def test_product_filtering_applies_in_both_modes(self, mock_path, mock_filter_manager_class, selection_mode):
        """测试商品过滤在两种模式下都生效"""
        # 配置
        config = GoodStoreSelectorConfig()
        config.selection_mode = selection_mode
        
        # Mock 文件存在
        mock_path.return_value.exists.return_value = True
        
        # 创建 selector
        selector = GoodStoreSelector(
            excel_file_path='test.xlsx',
            profit_calculator_path='calc.xlsx',
            config=config
        )
        
        # Mock FilterManager
        mock_filter_manager = MagicMock()
        mock_filter_manager_class.return_value = mock_filter_manager
        mock_product_filter = MagicMock(return_value=True)
        mock_filter_manager.get_product_filter_func.return_value = mock_product_filter
        
        # Mock seerfar_scraper
        selector.seerfar_scraper = MagicMock()
        
        # 模拟商品抓取成功
        mock_result = ScrapingResult(
            success=True,
            data={
                'products': [
                    {
                        'product_id': 'prod1',
                        'image_url': 'https://example.com/image1.jpg',
                        'brand_name': 'Brand1',
                        'sku': 'SKU1'
                    }
                ]
            }
        )
        selector.seerfar_scraper.scrape_store_products.return_value = mock_result
        
        # 创建店铺信息
        store_info = StoreInfo(
            store_id='123456',
            is_good_store=GoodStoreFlag.EMPTY,
            status=StoreStatus.PENDING
        )
        
        # 调用商品抓取方法
        products, error = selector._scrape_store_products(store_info, return_error=True)
        
        # 验证商品过滤函数被创建
        mock_filter_manager.get_product_filter_func.assert_called_once()
        
        # 验证抓取时传入了过滤函数
        call_kwargs = selector.seerfar_scraper.scrape_store_products.call_args[1]
        assert 'product_filter_func' in call_kwargs
        assert call_kwargs['product_filter_func'] == mock_product_filter
        
        # 验证返回了商品列表
        assert len(products) == 1
        assert products[0].product_id == 'prod1'
        assert error is None


class TestModeDetectionReal:
    """测试模式检测的真实场景"""
    
    @patch('good_store_selector.Path')
    def test_mode_detection_affects_load_pending_stores(self, mock_path):
        """测试模式检测影响店铺加载逻辑"""
        # Mock 文件存在
        mock_path.return_value.exists.return_value = True
        
        # 测试 select-goods 模式
        config1 = GoodStoreSelectorConfig()
        config1.selection_mode = 'select-goods'
        
        selector1 = GoodStoreSelector(
            excel_file_path='test.xlsx',
            profit_calculator_path='calc.xlsx',
            config=config1
        )
        
        # Mock excel_processor
        selector1.excel_processor = MagicMock()
        selector1.excel_processor.read_store_data.return_value = [
            ExcelStoreData(row_index=2, store_id='123456', is_good_store=GoodStoreFlag.EMPTY, status=StoreStatus.EMPTY),
        ]
        
        # 调用加载方法
        with patch.object(selector1, '_load_stores_for_goods_selection') as mock_load_goods:
            mock_load_goods.return_value = []
            selector1._load_pending_stores()
            # 验证调用了 select-goods 的加载方法
            mock_load_goods.assert_called_once()
        
        # 测试 select-shops 模式
        config2 = GoodStoreSelectorConfig()
        config2.selection_mode = 'select-shops'
        
        selector2 = GoodStoreSelector(
            excel_file_path='test.xlsx',
            profit_calculator_path='calc.xlsx',
            config=config2
        )
        
        # Mock excel_processor
        selector2.excel_processor = MagicMock()
        selector2.excel_processor.read_store_data.return_value = []
        selector2.excel_processor.filter_pending_stores.return_value = []
        
        # 调用加载方法
        selector2._load_pending_stores()
        
        # 验证调用了 filter_pending_stores
        selector2.excel_processor.filter_pending_stores.assert_called_once()


class TestExcelReadingReal:
    """测试 Excel 读取的真实场景"""
    
    @patch('good_store_selector.ExcelStoreProcessor')
    @patch('good_store_selector.Path')
    def test_excel_processor_initialization(self, mock_path, mock_processor_class):
        """测试 ExcelStoreProcessor 的初始化"""
        # Mock 文件存在
        mock_path.return_value.exists.return_value = True
        
        # Mock ExcelStoreProcessor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # 创建 selector
        config = GoodStoreSelectorConfig()
        selector = GoodStoreSelector(
            excel_file_path='test.xlsx',
            profit_calculator_path='calc.xlsx',
            config=config
        )
        
        # 初始化组件
        selector._initialize_components()
        
        # 验证 ExcelStoreProcessor 被创建
        assert selector.excel_processor is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
