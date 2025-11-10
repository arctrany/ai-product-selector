"""
测试好店筛选系统的主流程编排

测试完整的好店筛选工作流程和系统集成。
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from openpyxl import Workbook

from apps.xuanping.common.good_store_selector import GoodStoreSelector
from apps.xuanping.common.models import (
    StoreInfo, ProductInfo, PriceCalculationResult, ProductAnalysisResult,
    StoreAnalysisResult, BatchProcessingResult, StoreStatus, GoodStoreFlag
)
from apps.xuanping.common.config import GoodStoreSelectorConfig


class TestGoodStoreSelector:
    """测试好店筛选系统主控制器"""
    
    def setup_method(self):
        """测试前的设置"""
        self.config = GoodStoreSelectorConfig()
        self.selector = GoodStoreSelector(self.config)
    
    def test_good_store_selector_initialization(self):
        """测试好店筛选系统初始化"""
        assert self.selector.config is not None
        assert self.selector.logger is not None
        assert self.selector.excel_processor is not None
        assert self.selector.pricing_calculator is not None
        assert self.selector.profit_evaluator is not None
        assert self.selector.store_evaluator is not None
        assert self.selector.source_matcher is not None
        
        # 测试使用默认配置初始化
        selector_default = GoodStoreSelector()
        assert selector_default.config is not None
    
    def create_test_excel_file(self, store_data=None):
        """创建测试用的Excel文件"""
        wb = Workbook()
        ws = wb.active
        
        # 设置表头
        headers = ['店铺ID', '是否为好店', '状态', '销售额', '订单数', '评估时间']
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # 添加测试数据
        if store_data:
            for row, data in enumerate(store_data, 2):
                for col, value in enumerate(data, 1):
                    ws.cell(row=row, column=col, value=value)
        
        # 保存到临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(temp_file.name)
        temp_file.close()
        return temp_file.name
    
    @patch('apps.xuanping.common.good_store_selector.SeerfarScraper')
    @patch('apps.xuanping.common.good_store_selector.OzonScraper')
    @patch('apps.xuanping.common.good_store_selector.ErpPluginScraper')
    def test_process_single_store_success(self, mock_erp_scraper, mock_ozon_scraper, mock_seerfar_scraper):
        """测试成功处理单个店铺"""
        # 模拟抓取器
        mock_seerfar = mock_seerfar_scraper.return_value
        mock_ozon = mock_ozon_scraper.return_value
        mock_erp = mock_erp_plugin_scraper.return_value
        
        # 模拟店铺销售数据抓取
        mock_seerfar.scrape_store_sales_data.return_value = {
            'sales_30days': 600000.0,
            'orders_30days': 300,
            'success': True
        }
        
        # 模拟商品列表抓取
        mock_seerfar.scrape_store_products.return_value = [
            ProductInfo(
                product_id='PROD001',
                title='测试商品1',
                price_rub=2000.0,
                image_url='http://example.com/1.jpg'
            ),
            ProductInfo(
                product_id='PROD002',
                title='测试商品2',
                price_rub=1500.0,
                image_url='http://example.com/2.jpg'
            )
        ]
        
        # 模拟OZON价格抓取
        mock_ozon.scrape_product_prices.return_value = {
            'green_price_rub': 1800.0,
            'black_price_rub': 2000.0,
            'success': True
        }
        
        # 模拟ERP插件数据抓取
        mock_erp.scrape_product_attributes.return_value = {
            'commission_rate': 12.0,
            'weight': 500.0,
            'success': True
        }
        
        # 创建测试店铺
        store = StoreInfo(
            store_id='TEST_STORE_001',
            status=StoreStatus.PENDING
        )
        
        # 处理店铺
        result = self.selector.process_single_store(store)
        
        # 验证结果
        assert isinstance(result, StoreAnalysisResult)
        assert result.store_info.store_id == 'TEST_STORE_001'
        assert len(result.products) > 0
        
        # 验证抓取器被调用
        mock_seerfar.scrape_store_sales_data.assert_called_once()
        mock_seerfar.scrape_store_products.assert_called_once()
    
    @patch('apps.xuanping.common.good_store_selector.SeerfarScraper')
    def test_process_single_store_initial_filter_fail(self, mock_seerfar_scraper):
        """测试店铺初筛失败"""
        # 模拟抓取器
        mock_seerfar = mock_seerfar_scraper.return_value
        
        # 模拟销售数据不满足初筛条件
        mock_seerfar.scrape_store_sales_data.return_value = {
            'sales_30days': 100000.0,  # 低于阈值
            'orders_30days': 50,       # 低于阈值
            'success': True
        }
        
        # 创建测试店铺
        store = StoreInfo(
            store_id='TEST_STORE_002',
            status=StoreStatus.PENDING
        )
        
        # 处理店铺
        result = self.selector.process_single_store(store)
        
        # 验证结果
        assert isinstance(result, StoreAnalysisResult)
        assert result.store_info.store_id == 'TEST_STORE_002'
        assert len(result.products) == 0  # 没有商品数据
        assert result.total_products == 0
        assert result.is_good_store == False
    
    @patch('apps.xuanping.common.good_store_selector.SeerfarScraper')
    def test_process_single_store_scraping_error(self, mock_seerfar_scraper):
        """测试抓取过程中的错误处理"""
        # 模拟抓取器
        mock_seerfar = mock_seerfar_scraper.return_value
        
        # 模拟抓取失败
        mock_seerfar.scrape_store_sales_data.side_effect = Exception("网络错误")
        
        # 创建测试店铺
        store = StoreInfo(
            store_id='TEST_STORE_003',
            status=StoreStatus.PENDING
        )
        
        # 处理店铺应该不会抛出异常
        result = self.selector.process_single_store(store)
        
        # 验证错误处理
        assert isinstance(result, StoreAnalysisResult)
        assert result.store_info.store_id == 'TEST_STORE_003'
        assert result.has_error == True
    
    def test_process_stores_from_excel(self):
        """测试从Excel文件处理店铺"""
        # 创建测试Excel文件
        store_data = [
            ['STORE001', '', '待处理', 600000, 300, ''],
            ['STORE002', '', '待处理', 800000, 400, '']
        ]
        
        excel_file = self.create_test_excel_file(store_data)
        
        try:
            # 模拟process_single_store方法
            with patch.object(self.selector, 'process_single_store') as mock_process:
                mock_process.return_value = StoreAnalysisResult(
                    store_info=StoreInfo(store_id='STORE001'),
                    products=[],
                    total_products=0,
                    profitable_products=0,
                    profit_rate=0.0,
                    is_good_store=False
                )
                
                # 处理Excel文件
                result = self.selector.process_stores_from_excel(excel_file)
                
                # 验证结果
                assert isinstance(result, BatchProcessingResult)
                assert result.total_stores == 2
                assert result.processed_stores == 2
                
                # 验证process_single_store被调用了2次
                assert mock_process.call_count == 2
                
        finally:
            os.unlink(excel_file)
    
    def test_process_stores_from_excel_with_limit(self):
        """测试限制处理店铺数量"""
        # 创建测试Excel文件
        store_data = [
            ['STORE001', '', '待处理', 600000, 300, ''],
            ['STORE002', '', '待处理', 800000, 400, ''],
            ['STORE003', '', '待处理', 700000, 350, '']
        ]
        
        excel_file = self.create_test_excel_file(store_data)
        
        try:
            # 模拟process_single_store方法
            with patch.object(self.selector, 'process_single_store') as mock_process:
                mock_process.return_value = StoreAnalysisResult(
                    store_info=StoreInfo(store_id='STORE001'),
                    products=[],
                    total_products=0,
                    profitable_products=0,
                    profit_rate=0.0,
                    is_good_store=False
                )
                
                # 限制处理2个店铺
                result = self.selector.process_stores_from_excel(excel_file, max_stores=2)
                
                # 验证结果
                assert isinstance(result, BatchProcessingResult)
                assert result.total_stores == 3  # 总共3个店铺
                assert result.processed_stores == 2  # 只处理了2个
                
                # 验证process_single_store被调用了2次
                assert mock_process.call_count == 2
                
        finally:
            os.unlink(excel_file)
    
    def test_validate_store_filter_conditions(self):
        """测试店铺筛选条件验证"""
        # 测试满足条件的销售数据
        sales_data_pass = {
            'sales_30days': 600000.0,
            'orders_30days': 300
        }
        
        result = self.selector._validate_store_filter_conditions(sales_data_pass)
        assert result == True
        
        # 测试不满足销售额条件
        sales_data_fail_sales = {
            'sales_30days': 400000.0,  # 低于500000阈值
            'orders_30days': 300
        }
        
        result = self.selector._validate_store_filter_conditions(sales_data_fail_sales)
        assert result == False
        
        # 测试不满足订单数条件
        sales_data_fail_orders = {
            'sales_30days': 600000.0,
            'orders_30days': 200  # 低于250阈值
        }
        
        result = self.selector._validate_store_filter_conditions(sales_data_fail_orders)
        assert result == False
    
    # 🔧 已删除：_convert_image_url_to_product_url 方法已删除，因为商品页面通过点击打开，不需要URL转换
    
    def test_generate_processing_summary(self):
        """测试生成处理摘要"""
        # 创建测试结果
        result = BatchProcessingResult(
            total_stores=10,
            processed_stores=8,
            good_stores=3,
            failed_stores=2,
            start_time='2024-01-01 10:00:00',
            end_time='2024-01-01 12:00:00',
            processing_time_seconds=7200.0
        )
        
        summary = self.selector.generate_processing_summary(result)
        
        # 验证摘要内容
        assert "总店铺数: 10" in summary
        assert "处理成功: 8" in summary
        assert "好店数量: 3" in summary
        assert "失败数量: 2" in summary
        assert "处理时长: 2.00小时" in summary
    
    def test_cleanup_resources(self):
        """测试资源清理"""
        # 模拟抓取器
        mock_scrapers = [Mock(), Mock(), Mock()]
        self.selector._active_scrapers = mock_scrapers
        
        # 执行清理
        self.selector.cleanup_resources()
        
        # 验证所有抓取器都被关闭
        for scraper in mock_scrapers:
            scraper.close.assert_called_once()
        
        # 验证活跃抓取器列表被清空
        assert len(self.selector._active_scrapers) == 0
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with patch.object(self.selector, 'cleanup_resources') as mock_cleanup:
            with self.selector as selector:
                assert selector is self.selector
            
            # 验证退出时调用了cleanup_resources
            mock_cleanup.assert_called_once()
    
    def test_error_recovery(self):
        """测试错误恢复机制"""
        # 创建测试Excel文件
        store_data = [
            ['STORE001', '', '待处理', 600000, 300, ''],
            ['STORE002', '', '待处理', 800000, 400, '']
        ]
        
        excel_file = self.create_test_excel_file(store_data)
        
        try:
            # 模拟第一个店铺处理失败，第二个成功
            def side_effect(store):
                if store.store_id == 'STORE001':
                    raise Exception("处理失败")
                else:
                    return StoreAnalysisResult(
                        store_info=store,
                        products=[],
                        total_products=0,
                        profitable_products=0,
                        profit_rate=0.0,
                        is_good_store=False
                    )
            
            with patch.object(self.selector, 'process_single_store', side_effect=side_effect):
                result = self.selector.process_stores_from_excel(excel_file)
                
                # 验证错误恢复
                assert result.total_stores == 2
                assert result.processed_stores == 1  # 只有一个成功
                assert result.failed_stores == 1     # 一个失败
                
        finally:
            os.unlink(excel_file)


class TestGoodStoreSelectorIntegration:
    """测试好店筛选系统的集成场景"""
    
    def test_complete_workflow_simulation(self):
        """测试完整工作流程模拟"""
        config = GoodStoreSelectorConfig()
        config.store_filter.max_products_to_check = 5  # 限制商品数量以加快测试
        
        selector = GoodStoreSelector(config)
        
        # 创建测试Excel文件
        store_data = [
            ['STORE001', '', '待处理', 600000, 300, '']
        ]
        
        wb = Workbook()
        ws = wb.active
        
        # 设置表头
        headers = ['店铺ID', '是否为好店', '状态', '销售额', '订单数', '评估时间']
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # 添加数据
        for row, data in enumerate(store_data, 2):
            for col, value in enumerate(data, 1):
                ws.cell(row=row, column=col, value=value)
        
        # 保存文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        wb.save(temp_file.name)
        temp_file.close()
        
        try:
            # 模拟所有外部依赖
            with patch('apps.xuanping.common.good_store_selector.SeerfarScraper') as mock_seerfar_class, \
                 patch('apps.xuanping.common.good_store_selector.OzonScraper') as mock_ozon_class, \
                 patch('apps.xuanping.common.good_store_selector.ErpPluginScraper') as mock_erp_class:
                
                # 设置模拟抓取器
                mock_seerfar = mock_seerfar_class.return_value
                mock_ozon = mock_ozon_class.return_value
                mock_erp = mock_erp_class.return_value
                
                # 模拟销售数据抓取（满足初筛条件）
                mock_seerfar.scrape_store_sales_data.return_value = {
                    'sales_30days': 600000.0,
                    'orders_30days': 300,
                    'success': True
                }
                
                # 模拟商品列表抓取
                mock_seerfar.scrape_store_products.return_value = [
                    ProductInfo(
                        product_id='PROD001',
                        title='测试商品',
                        price_rub=2000.0,
                        image_url='http://example.com/image.jpg'
                    )
                ]
                
                # 模拟价格抓取
                mock_ozon.scrape_product_prices.return_value = {
                    'green_price_rub': 1800.0,
                    'black_price_rub': 2000.0,
                    'success': True
                }
                
                # 模拟ERP数据抓取
                mock_erp.scrape_product_attributes.return_value = {
                    'commission_rate': 12.0,
                    'weight': 500.0,
                    'success': True
                }
                
                # 执行完整流程
                with selector:
                    result = selector.process_stores_from_excel(temp_file.name)
                
                # 验证结果
                assert isinstance(result, BatchProcessingResult)
                assert result.total_stores == 1
                assert result.processed_stores == 1
                
                # 验证各个抓取器都被调用
                mock_seerfar.scrape_store_sales_data.assert_called()
                mock_seerfar.scrape_store_products.assert_called()
                
        finally:
            os.unlink(temp_file.name)
    
    def test_performance_monitoring(self):
        """测试性能监控"""
        config = GoodStoreSelectorConfig()
        selector = GoodStoreSelector(config)
        
        # 创建测试数据
        store = StoreInfo(store_id='PERF_TEST_STORE')
        
        # 模拟处理过程
        with patch.object(selector, '_scrape_store_sales_data') as mock_sales, \
             patch.object(selector, '_validate_store_filter_conditions') as mock_validate:
            
            mock_sales.return_value = {'sales_30days': 600000.0, 'orders_30days': 300}
            mock_validate.return_value = False  # 不满足条件，快速结束
            
            import time
            start_time = time.time()
            
            result = selector.process_single_store(store)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证性能（处理时间应该很短，因为在初筛阶段就结束了）
            assert processing_time < 1.0  # 应该在1秒内完成
            assert isinstance(result, StoreAnalysisResult)
    
    def test_configuration_impact(self):
        """测试配置对系统行为的影响"""
        # 测试不同的配置设置
        config1 = GoodStoreSelectorConfig()
        config1.store_filter.min_sales_30days = 1000000.0  # 更高的销售额要求
        
        config2 = GoodStoreSelectorConfig()
        config2.store_filter.min_sales_30days = 100000.0   # 更低的销售额要求
        
        selector1 = GoodStoreSelector(config1)
        selector2 = GoodStoreSelector(config2)
        
        # 测试相同的销售数据在不同配置下的结果
        sales_data = {'sales_30days': 500000.0, 'orders_30days': 300}
        
        result1 = selector1._validate_store_filter_conditions(sales_data)
        result2 = selector2._validate_store_filter_conditions(sales_data)
        
        # 验证配置影响
        assert result1 == False  # 不满足高要求
        assert result2 == True   # 满足低要求


if __name__ == "__main__":
    pytest.main([__file__, "-v"])