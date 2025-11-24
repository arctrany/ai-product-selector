"""
测试URL硬编码修复的端到端集成测试

这个测试验证：
1. GoodStoreSelector不再使用硬编码的ozon URL
2. 正确传递store_id参数到ScrapingOrchestrator
3. ScrapingOrchestrator优先使用store_id参数
4. 完整的调用链路工作正常
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from common.models.excel_models import ExcelStoreData
from common.models.enums import StoreStatus, GoodStoreFlag
from common.models.scraping_result import ScrapingResult
from common.services.scraping_orchestrator import ScrapingMode
from good_store_selector import GoodStoreSelector
from common.config.base_config import GoodStoreSelectorConfig


class TestURLFixIntegration:
    """测试URL硬编码修复的完整集成"""

    def setup_method(self):
        """测试初始化"""
        self.config = GoodStoreSelectorConfig()
        self.config.selection_mode = 'select-goods'
        
        # 创建测试用的店铺数据 - 使用纯数字ID以通过isdigit()检查
        self.test_store_data = ExcelStoreData(
            row_index=1,
            store_id='123456789',  # 纯数字ID，通过isdigit()检查
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PENDING
        )

    @patch('good_store_selector.get_global_scraping_orchestrator')
    def test_no_hardcoded_url_in_goodstoreselector(self, mock_get_orchestrator):
        """测试GoodStoreSelector不再使用硬编码URL"""

        # Mock ScrapingOrchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.scrape_with_orchestration.return_value = ScrapingResult(
            success=True,
            data={
                'store_sales_data': {
                    'store_id': '123456789',
                    'monthly_sales': 50000.0,
                    'products': []
                }
            }
        )
        mock_get_orchestrator.return_value = mock_orchestrator

        # 创建GoodStoreSelector，直接Mock其依赖
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class:

            # Mock Excel处理器实例
            mock_excel_instance = Mock()
            mock_excel_instance.read_store_data.return_value = [self.test_store_data]
            mock_excel_instance.update_store_analysis.return_value = None
            mock_excel_class.return_value = mock_excel_instance

            # Mock利润评估器实例
            mock_profit_instance = Mock()
            mock_profit_class.return_value = mock_profit_instance

            # 创建GoodStoreSelector
            selector = GoodStoreSelector(
                excel_file_path='test.xlsx',
                profit_calculator_path='calc.xlsx',
                config=self.config
            )

            # 执行选品
            result = selector.process_stores()

        # 验证关键点：确保没有传递硬编码的ozon URL
        mock_orchestrator.scrape_with_orchestration.assert_called_once()
        call_args = mock_orchestrator.scrape_with_orchestration.call_args

        # 验证调用参数
        assert call_args[1]['mode'] == ScrapingMode.STORE_ANALYSIS
        assert call_args[1]['url'] == ''  # 应该是空URL，不是硬编码的ozon URL
        assert call_args[1]['store_id'] == '123456789'  # 应该传递store_id

        # 验证不包含硬编码URL（应该使用seerfar.cn而不是ozon.ru）
        assert 'https://www.ozon.ru/seller/' not in str(call_args)

        # 验证使用的是正确的seerfar URL格式（在实际实现中应该生成这样的URL）
        # 正确格式：https://seerfar.cn/admin/store-detail.html?storeId=${store_id}&platform=OZON

        print("✅ 验证通过：GoodStoreSelector不再使用硬编码URL")

    @patch('common.scrapers.seerfar_scraper.SeerfarScraper')
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def test_orchestrator_uses_store_id_parameter(self, mock_browser_service, mock_seerfar_class):
        """测试ScrapingOrchestrator优先使用store_id参数"""

        from common.services.scraping_orchestrator import ScrapingOrchestrator

        # Mock SeerfarScraper
        mock_seerfar = Mock()
        mock_seerfar.scrape_store_sales_data.return_value = ScrapingResult(
            success=True,
            data={'sales': 50000.0}
        )
        mock_seerfar_class.return_value = mock_seerfar

        # Mock浏览器服务
        mock_browser_service.return_value = Mock()

        # 创建ScrapingOrchestrator
        orchestrator = ScrapingOrchestrator()

        # 测试我的修复：传递store_id参数，URL为空
        result = orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.STORE_ANALYSIS,
            url='',  # 空URL
            store_id='123456789'  # 传递store_id
        )

        # 验证调用
        assert result.success
        mock_seerfar.scrape_store_sales_data.assert_called_once_with(
            '123456789',
            30,
            options=None
        )

        print("✅ 验证通过：ScrapingOrchestrator正确使用store_id参数")

    @patch('common.scrapers.seerfar_scraper.SeerfarScraper')
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def test_orchestrator_rejects_missing_store_id(self, mock_browser_service, mock_seerfar_class):
        """测试ScrapingOrchestrator在缺少store_id时返回错误"""

        from common.services.scraping_orchestrator import ScrapingOrchestrator

        # Mock SeerfarScraper
        mock_seerfar_class.return_value = Mock()
        mock_browser_service.return_value = Mock()

        # 创建ScrapingOrchestrator
        orchestrator = ScrapingOrchestrator()

        # 测试缺少store_id的情况
        result = orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.STORE_ANALYSIS,
            url='https://some-url.com'  # 有URL但没有store_id
            # 注意：没有传递store_id参数
        )

        # 验证返回错误
        assert not result.success
        assert '缺少必需的store_id参数' in result.error_message

        print("✅ 验证通过：ScrapingOrchestrator正确处理缺少store_id的情况")

    @patch('good_store_selector.get_global_scraping_orchestrator')
    def test_end_to_end_store_id_flow(self, mock_get_orchestrator):
        """测试完整的端到端store_id流程"""

        # Mock ScrapingOrchestrator - 关键：验证接收到的参数
        mock_orchestrator = Mock()
        received_calls = []

        def capture_call(*args, **kwargs):
            received_calls.append((args, kwargs))
            return ScrapingResult(
                success=True,
                data={'store_sales_data': {'store_id': kwargs.get('store_id')}}
            )

        mock_orchestrator.scrape_with_orchestration.side_effect = capture_call
        mock_get_orchestrator.return_value = mock_orchestrator

        # 创建GoodStoreSelector，使用统一的Mock策略
        with patch('good_store_selector.ExcelStoreProcessor') as mock_excel_class, \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class:

            # Mock Excel处理器实例
            mock_excel_instance = Mock()
            mock_excel_instance.read_store_data.return_value = [self.test_store_data]
            mock_excel_instance.update_store_analysis.return_value = None
            mock_excel_class.return_value = mock_excel_instance

            # Mock利润评估器实例
            mock_profit_instance = Mock()
            mock_profit_class.return_value = mock_profit_instance

            # 创建GoodStoreSelector
            selector = GoodStoreSelector(
                excel_file_path='test.xlsx',
                profit_calculator_path='calc.xlsx',
                config=self.config
            )

            # 执行选品
            result = selector.process_stores()
        
        # 验证完整的调用链
        assert len(received_calls) == 1
        call_args, call_kwargs = received_calls[0]
        
        # 验证关键参数传递正确
        assert call_kwargs['mode'] == ScrapingMode.STORE_ANALYSIS
        assert call_kwargs['url'] == ''  # 不是硬编码URL  
        assert call_kwargs['store_id'] == '123456789'  # 正确的store_id
        
        # 验证没有硬编码URL，而是使用正确的seerfar URL格式
        full_call_str = str(call_args) + str(call_kwargs)
        assert 'ozon.ru/seller' not in full_call_str

        # 在实际实现中，应该使用这种格式的URL：
        # https://seerfar.cn/admin/store-detail.html?storeId=123456789&platform=OZON
        
        print("✅ 验证通过：完整的端到端流程正确传递store_id而非硬编码URL")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
