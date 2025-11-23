"""
ScrapingOrchestrator测试

测试ScrapingOrchestrator的核心功能和接口
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from common.services.scraping_orchestrator import (
    ScrapingOrchestrator, 
    ScrapingMode, 
    OrchestrationConfig
)
from common.models.scraping_result import ScrapingResult

class TestScrapingOrchestratorBasic(unittest.TestCase):
    """ScrapingOrchestrator基础功能测试"""
    
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def setUp(self, mock_get_global_browser_service):
        """测试初始化"""
        # 创建Mock浏览器服务
        self.mock_browser_service = Mock()
        self.mock_browser_service.navigate_to_sync = Mock(return_value=True)
        self.mock_browser_service.evaluate_sync = Mock(return_value="<html></html>")
        self.mock_browser_service.get_current_page = Mock(return_value=Mock())

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建编排器实例
        self.orchestrator = ScrapingOrchestrator()

    def test_orchestrator_initialization(self):
        """测试编排器初始化"""
        self.assertIsNotNone(self.orchestrator)
        self.assertIsNotNone(self.orchestrator.ozon_scraper)
        self.assertIsNotNone(self.orchestrator.seerfar_scraper)
        self.assertIsNotNone(self.orchestrator.competitor_scraper)
        self.assertIsNotNone(self.orchestrator.erp_plugin_scraper)
        self.assertIsNotNone(self.orchestrator.competitor_detection_service)

    def test_orchestrator_config(self):
        """测试编排器配置"""
        config = OrchestrationConfig(
            max_retries=5,
            retry_delay_seconds=1.0,
            timeout_seconds=600,
            enable_monitoring=True,
            enable_detailed_logging=False
        )

        orchestrator = ScrapingOrchestrator(config=config)

        self.assertEqual(orchestrator.config.max_retries, 5)
        self.assertEqual(orchestrator.config.retry_delay_seconds, 1.0)
        self.assertEqual(orchestrator.config.timeout_seconds, 600)
        self.assertTrue(orchestrator.config.enable_monitoring)
        self.assertFalse(orchestrator.config.enable_detailed_logging)

    def test_get_scraper_by_type(self):
        """测试根据类型获取Scraper"""
        ozon_scraper = self.orchestrator.get_scraper_by_type('ozon')
        self.assertEqual(ozon_scraper, self.orchestrator.ozon_scraper)

        seerfar_scraper = self.orchestrator.get_scraper_by_type('seerfar')
        self.assertEqual(seerfar_scraper, self.orchestrator.seerfar_scraper)

        competitor_scraper = self.orchestrator.get_scraper_by_type('competitor')
        self.assertEqual(competitor_scraper, self.orchestrator.competitor_scraper)

        erp_scraper = self.orchestrator.get_scraper_by_type('erp')
        self.assertEqual(erp_scraper, self.orchestrator.erp_plugin_scraper)

        # 测试不支持的类型
        with self.assertRaises(ValueError):
            self.orchestrator.get_scraper_by_type('unsupported')

class TestScrapingOrchestratorModes(unittest.TestCase):
    """ScrapingOrchestrator模式测试"""

    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def setUp(self, mock_get_global_browser_service):
        """测试初始化"""
        # 创建Mock浏览器服务
        self.mock_browser_service = Mock()
        self.mock_browser_service.navigate_to_sync = Mock(return_value=True)
        self.mock_browser_service.evaluate_sync = Mock(return_value="<html></html>")
        self.mock_browser_service.get_current_page = Mock(return_value=Mock())

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建编排器实例
        self.orchestrator = ScrapingOrchestrator()

    @patch('common.scrapers.ozon_scraper.OzonScraper')
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def test_product_info_mode(self, mock_get_global_browser_service, mock_ozon_scraper_class):
        """测试商品信息抓取模式"""
        # 设置Mock
        mock_ozon_scraper = Mock()
        mock_ozon_scraper_class.return_value = mock_ozon_scraper
        mock_ozon_scraper.scrape.return_value = ScrapingResult(
            success=True,
            data={'price': 1000.0},
            error_message=None,
            execution_time=0.1
        )

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建新的编排器实例（使用Mock的OzonScraper）
        orchestrator = ScrapingOrchestrator()

        # 执行测试
        result = orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.PRODUCT_INFO,
            url='https://test.com/product/123'
        )

        # 验证结果
        self.assertTrue(result.success)
        self.assertIn('price', result.data)
        mock_ozon_scraper.scrape.assert_called_once()

    @patch('common.scrapers.seerfar_scraper.SeerfarScraper')
    @patch('common.utils.scraping_utils.ScrapingUtils')
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def test_store_analysis_mode(self, mock_get_global_browser_service, mock_scraping_utils_class, mock_seerfar_scraper_class):
        """测试店铺分析抓取模式"""
        # 设置Mock
        mock_seerfar_scraper = Mock()
        mock_seerfar_scraper_class.return_value = mock_seerfar_scraper
        mock_seerfar_scraper.scrape_store_sales_data.return_value = ScrapingResult(
            success=True,
            data={'sales': 50000.0},
            error_message=None,
            execution_time=0.1
        )

        mock_scraping_utils = Mock()
        mock_scraping_utils_class.return_value = mock_scraping_utils
        mock_scraping_utils.extract_id_from_url.return_value = 'store_123'

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建新的编排器实例
        orchestrator = ScrapingOrchestrator()

        # 执行测试
        result = orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.STORE_ANALYSIS,
            url='https://test.com/store/123'
        )

        # 验证结果
        self.assertTrue(result.success)
        self.assertIn('sales', result.data)
        mock_seerfar_scraper.scrape_store_sales_data.assert_called_once()

    @patch('common.services.competitor_detection_service.CompetitorDetectionService')
    @patch('common.scrapers.competitor_scraper.CompetitorScraper')
    @patch('common.scrapers.ozon_scraper.OzonScraper')
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def test_competitor_detection_mode(self, mock_get_global_browser_service, mock_ozon_scraper_class, mock_competitor_scraper_class, mock_detection_service_class):
        """测试跟卖检测模式"""
        # 设置Mock
        mock_ozon_scraper = Mock()
        mock_ozon_scraper_class.return_value = mock_ozon_scraper
        mock_ozon_scraper.navigate_to.return_value = True

        mock_detection_service = Mock()
        mock_detection_service_class.return_value = mock_detection_service
        mock_detection_service.detect_competitors.return_value = Mock(
            has_competitors=False,
            competitor_count=0
        )

        mock_competitor_scraper = Mock()
        mock_competitor_scraper_class.return_value = mock_competitor_scraper

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建新的编排器实例
        orchestrator = ScrapingOrchestrator()

        # 执行测试
        result = orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.COMPETITOR_DETECTION,
            url='https://test.com/product/123'
        )

        # 验证结果
        self.assertTrue(result.success)
        mock_ozon_scraper.navigate_to.assert_called_once()
        mock_detection_service.detect_competitors.assert_called_once()

    @patch('common.scrapers.erp_plugin_scraper.ErpPluginScraper')
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def test_erp_data_mode(self, mock_get_global_browser_service, mock_erp_scraper_class):
        """测试ERP数据抓取模式"""
        # 设置Mock
        mock_erp_scraper = Mock()
        mock_erp_scraper_class.return_value = mock_erp_scraper
        mock_erp_scraper.scrape.return_value = ScrapingResult(
            success=True,
            data={'category': 'Electronics'},
            error_message=None,
            execution_time=0.1
        )

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建新的编排器实例
        orchestrator = ScrapingOrchestrator()

        # 执行测试
        result = orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.ERP_DATA,
            url='https://test.com/product/123'
        )

        # 验证结果
        self.assertTrue(result.success)
        self.assertIn('category', result.data)
        mock_erp_scraper.scrape.assert_called_once()

class TestScrapingOrchestratorFullAnalysis(unittest.TestCase):
    """ScrapingOrchestrator全量分析测试"""

    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def setUp(self, mock_get_global_browser_service):
        """测试初始化"""
        # 创建Mock浏览器服务
        self.mock_browser_service = Mock()
        self.mock_browser_service.navigate_to_sync = Mock(return_value=True)
        self.mock_browser_service.evaluate_sync = Mock(return_value="<html></html>")
        self.mock_browser_service.get_current_page = Mock(return_value=Mock())

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建编排器实例
        self.orchestrator = ScrapingOrchestrator()

    @patch('common.scrapers.ozon_scraper.OzonScraper')
    @patch('common.scrapers.erp_plugin_scraper.ErpPluginScraper')
    @patch('common.services.competitor_detection_service.CompetitorDetectionService')
    @patch('common.scrapers.competitor_scraper.CompetitorScraper')
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def test_full_analysis_mode(self, mock_get_global_browser_service, mock_competitor_scraper_class, mock_detection_service_class,
                               mock_erp_scraper_class, mock_ozon_scraper_class):
        """测试全量分析抓取模式"""
        # 设置Mock
        mock_ozon_scraper = Mock()
        mock_ozon_scraper_class.return_value = mock_ozon_scraper
        mock_ozon_scraper.scrape.return_value = ScrapingResult(
            success=True,
            data={'price': 1000.0},
            error_message=None,
            execution_time=0.1
        )

        mock_erp_scraper = Mock()
        mock_erp_scraper_class.return_value = mock_erp_scraper
        mock_erp_scraper.scrape.return_value = ScrapingResult(
            success=True,
            data={'category': 'Electronics'},
            error_message=None,
            execution_time=0.1
        )

        mock_detection_service = Mock()
        mock_detection_service_class.return_value = mock_detection_service
        mock_detection_service.detect_competitors.return_value = Mock(
            has_competitors=False,
            competitor_count=0
        )

        mock_competitor_scraper = Mock()
        mock_competitor_scraper_class.return_value = mock_competitor_scraper

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建新的编排器实例
        orchestrator = ScrapingOrchestrator()

        # 执行测试
        result = orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.FULL_ANALYSIS,
            url='https://test.com/product/123'
        )

        # 验证结果
        self.assertTrue(result.success)
        self.assertIn('product_info', result.data)
        self.assertIn('erp_data', result.data)
        mock_ozon_scraper.scrape.assert_called_once()
        mock_erp_scraper.scrape.assert_called_once()

class TestScrapingOrchestratorErrorHandling(unittest.TestCase):
    """ScrapingOrchestrator错误处理测试"""

    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def setUp(self, mock_get_global_browser_service):
        """测试初始化"""
        # 创建Mock浏览器服务
        self.mock_browser_service = Mock()
        self.mock_browser_service.navigate_to_sync = Mock(return_value=True)
        self.mock_browser_service.evaluate_sync = Mock(return_value="<html></html>")
        self.mock_browser_service.get_current_page = Mock(return_value=Mock())

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建编排器实例
        self.orchestrator = ScrapingOrchestrator()

    def test_invalid_mode(self):
        """测试无效模式"""
        from enum import Enum

        class InvalidMode(Enum):
            INVALID = "invalid"

        result = self.orchestrator.scrape_with_orchestration(
            mode=InvalidMode.INVALID,
            url='https://test.com/product/123'
        )

        self.assertFalse(result.success)
        self.assertIn("不支持的抓取模式", result.error_message)

    @patch('common.scrapers.ozon_scraper.OzonScraper')
    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def test_scraper_failure(self, mock_get_global_browser_service, mock_ozon_scraper_class):
        """测试Scraper失败情况"""
        # 设置Mock
        mock_ozon_scraper = Mock()
        mock_ozon_scraper_class.return_value = mock_ozon_scraper
        mock_ozon_scraper.scrape.return_value = ScrapingResult(
            success=False,
            data={},
            error_message="抓取失败",
            execution_time=0.1
        )

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建新的编排器实例
        orchestrator = ScrapingOrchestrator()

        # 执行测试
        result = orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.PRODUCT_INFO,
            url='https://test.com/product/123'
        )

        # 验证结果
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "抓取失败")

    def test_exception_handling(self):
        """测试异常处理"""
        # 模拟异常
        self.orchestrator._orchestrate_product_info_scraping = Mock(
            side_effect=Exception("模拟异常")
        )

        result = self.orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.PRODUCT_INFO,
            url='https://test.com/product/123'
        )

        self.assertFalse(result.success)
        self.assertIn("模拟异常", result.error_message)

class TestScrapingOrchestratorMetrics(unittest.TestCase):
    """ScrapingOrchestrator监控指标测试"""

    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def setUp(self, mock_get_global_browser_service):
        """测试初始化"""
        # 创建Mock浏览器服务
        self.mock_browser_service = Mock()
        self.mock_browser_service.navigate_to_sync = Mock(return_value=True)
        self.mock_browser_service.evaluate_sync = Mock(return_value="<html></html>")
        self.mock_browser_service.get_current_page = Mock(return_value=Mock())

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建编排器实例
        self.orchestrator = ScrapingOrchestrator()

    def test_metrics_initialization(self):
        """测试监控指标初始化"""
        metrics = self.orchestrator.get_metrics()
        self.assertIn('total_operations', metrics)
        self.assertIn('successful_operations', metrics)
        self.assertIn('failed_operations', metrics)
        self.assertIn('avg_response_time', metrics)
        self.assertIn('retry_count', metrics)

        self.assertEqual(metrics['total_operations'], 0)
        self.assertEqual(metrics['successful_operations'], 0)
        self.assertEqual(metrics['failed_operations'], 0)
        self.assertEqual(metrics['avg_response_time'], 0.0)
        self.assertEqual(metrics['retry_count'], 0)

    def test_metrics_reset(self):
        """测试监控指标重置"""
        # 模拟一些操作
        self.orchestrator._update_metrics('total_operations', 5)
        self.orchestrator._update_metrics('successful_operations', 3)

        # 重置指标
        self.orchestrator.reset_metrics()

        # 验证重置
        metrics = self.orchestrator.get_metrics()
        self.assertEqual(metrics['total_operations'], 0)
        self.assertEqual(metrics['successful_operations'], 0)
        self.assertEqual(metrics['failed_operations'], 0)
        self.assertEqual(metrics['avg_response_time'], 0.0)
        self.assertEqual(metrics['retry_count'], 0)

class TestScrapingOrchestratorHealthCheck(unittest.TestCase):
    """ScrapingOrchestrator健康检查测试"""

    @patch('common.scrapers.global_browser_singleton.get_global_browser_service')
    def setUp(self, mock_get_global_browser_service):
        """测试初始化"""
        # 创建Mock浏览器服务
        self.mock_browser_service = Mock()
        self.mock_browser_service.navigate_to_sync = Mock(return_value=True)
        self.mock_browser_service.evaluate_sync = Mock(return_value="<html></html>")
        self.mock_browser_service.get_current_page = Mock(return_value=Mock())

        mock_get_global_browser_service.return_value = self.mock_browser_service

        # 创建编排器实例
        self.orchestrator = ScrapingOrchestrator()
    
    def test_health_check(self):
        """测试健康检查"""
        health_status = self.orchestrator.health_check()
        
        self.assertIn('orchestrator', health_status)
        self.assertIn('scrapers', health_status)
        self.assertIn('services', health_status)
        self.assertIn('browser_service', health_status)
        
        self.assertEqual(health_status['orchestrator'], 'healthy')
        self.assertEqual(health_status['browser_service'], 'healthy')
        self.assertEqual(health_status['scrapers']['ozon'], 'initialized')
        self.assertEqual(health_status['scrapers']['seerfar'], 'initialized')
        self.assertEqual(health_status['scrapers']['competitor'], 'initialized')
        self.assertEqual(health_status['scrapers']['erp'], 'initialized')
        self.assertEqual(health_status['services']['competitor_detection'], 'initialized')

if __name__ == '__main__':
    unittest.main()
