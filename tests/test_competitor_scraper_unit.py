"""
CompetitorScraper 单元测试

符合项目测试规范，包含全面的功能测试和边界条件测试。
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from bs4 import BeautifulSoup

from common.scrapers.competitor_scraper import CompetitorScraper
from common.models.scraping_result import ScrapingResult
from common.config.ozon_selectors_config import OzonSelectorsConfig


class TestCompetitorScraper:
    """CompetitorScraper 单元测试类"""

    def setup_method(self):
        """测试方法设置 - 每个测试方法执行前调用"""
        # Mock 浏览器服务
        self.mock_browser_service = Mock()
        self.mock_page = Mock()
        self.mock_browser_service.get_page.return_value = self.mock_page
        self.mock_page.query_selector.return_value = True
        self.mock_page.click.return_value = None
        self.mock_page.content.return_value = self._create_mock_html_content()

        # Mock selectors config
        self.mock_config = Mock(spec=OzonSelectorsConfig)
        self.mock_config.competitor_area_click_selectors = [
            ".pdp_bi8",
            ".pdp_bi8 button",
            "[data-widget='webBestSeller']"
        ]
        self.mock_config.expand_selectors = [
            "button:has-text('показать')",
            "button:has-text('еще')",
            "[class*='show-more']"
        ]
        self.mock_config.popup_container_selectors = [
            "#seller-list",
            "div.pdp_b2k"
        ]
        self.mock_config.competitor_popup_selectors = [
            "div.pdp_bk3",
            "[class*='seller-item']"
        ]
        self.mock_config.currency_symbol = "₽"

        # Mock wait_utils and scraping_utils
        self.mock_wait_utils = Mock()
        self.mock_wait_utils.smart_wait.return_value = None
        
        self.mock_scraping_utils = Mock()
        self.mock_scraping_utils.wait_for_content_smart.return_value = {
            'soup': BeautifulSoup(self._create_mock_html_content(), 'html.parser'),
            'content': self._create_mock_html_content()
        }

        # 使用 patch 创建 CompetitorScraper 实例
        with patch('common.scrapers.competitor_scraper.get_global_browser_service', return_value=self.mock_browser_service), \
             patch('common.scrapers.competitor_scraper.WaitUtils', return_value=self.mock_wait_utils), \
             patch('common.scrapers.competitor_scraper.ScrapingUtils', return_value=self.mock_scraping_utils):
            self.scraper = CompetitorScraper(
                selectors_config=self.mock_config,
                browser_service=self.mock_browser_service
            )

    def teardown_method(self):
        """测试方法清理 - 每个测试方法执行后调用"""
        pass

    # ========== 测试数据辅助方法 ==========

    def _create_mock_html_content(self):
        """创建模拟的HTML内容"""
        return """
        <html>
        <body>
            <div class="pdp_bi8">
                <button>竞品信息</button>
            </div>
            <div id="seller-list">
                <div class="pdp_bk3">
                    <div class="seller-name">测试店铺1</div>
                    <div class="seller-price">1000₽</div>
                    <a href="/seller/123">店铺链接</a>
                </div>
                <div class="pdp_bk3">
                    <div class="seller-name">测试店铺2</div>
                    <div class="seller-price">900₽</div>
                    <a href="/seller/456">店铺链接</a>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_mock_competitor_elements(self):
        """创建模拟的竞品元素"""
        html = """
        <div class="pdp_bk3">
            <div class="seller-name">测试店铺</div>
            <div class="seller-price">1000₽</div>
            <a href="/seller/123456">店铺链接</a>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        return [soup.find('div', class_='pdp_bk3')]

    # ========== 基本功能测试 ==========

    def test_scraper_initialization(self):
        """测试爬虫初始化"""
        # Arrange & Act
        with patch('common.scrapers.competitor_scraper.get_global_browser_service', return_value=self.mock_browser_service), \
             patch('common.scrapers.competitor_scraper.WaitUtils', return_value=self.mock_wait_utils), \
             patch('common.scrapers.competitor_scraper.ScrapingUtils', return_value=self.mock_scraping_utils):
            scraper = CompetitorScraper(browser_service=self.mock_browser_service)

        # Assert
        assert scraper.browser_service == self.mock_browser_service
        assert scraper.selectors_config is not None
        assert scraper.wait_utils is not None
        assert scraper.scraping_utils is not None

    def test_scraper_initialization_without_browser_service(self):
        """测试无浏览器服务的初始化（使用全局单例）"""
        # Arrange & Act
        with patch('common.scrapers.competitor_scraper.get_global_browser_service', return_value=self.mock_browser_service), \
             patch('common.scrapers.competitor_scraper.WaitUtils', return_value=self.mock_wait_utils), \
             patch('common.scrapers.competitor_scraper.ScrapingUtils', return_value=self.mock_scraping_utils):
            scraper = CompetitorScraper()

        # Assert
        assert scraper.browser_service == self.mock_browser_service

    # ========== scrape 方法测试 ==========

    def test_scrape_success_basic(self):
        """测试 scrape 方法基本成功场景"""
        # Arrange
        test_url = "https://www.ozon.ru/product/1176594312"
        
        # Act
        result = self.scraper.scrape(url=test_url)

        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is True
        assert isinstance(result.data, list)
        assert result.execution_time is not None

    def test_scrape_with_context_expand_needed(self):
        """测试需要展开更多竞品的 scrape 方法"""
        # Arrange
        test_url = "https://www.ozon.ru/product/1176594312"
        context = {'competitor_count': 15}  # 超过10个需要展开
        
        # Act
        result = self.scraper.scrape(url=test_url, context=context)

        # Assert
        assert result.success is True
        self.mock_scraping_utils.wait_for_content_smart.assert_called_once()

    def test_scrape_with_max_competitors_limit(self):
        """测试设置最大竞品数量限制的 scrape"""
        # Arrange
        test_url = "https://www.ozon.ru/product/1176594312"
        
        # Act
        result = self.scraper.scrape(url=test_url, max_competitors=5)

        # Assert
        assert result.success is True
        assert len(result.data) <= 5

    # ========== _present_competitor_popup 方法测试 ==========

    @patch('common.scrapers.competitor_scraper.BeautifulSoup')
    def test_present_competitor_popup_success(self, mock_beautifulsoup):
        """测试成功弹出竞品弹窗"""
        # Arrange
        soup = Mock()
        competitor_container = Mock()
        mock_beautifulsoup.return_value = soup
        
        # Act
        result = self.scraper._present_competitor_popup(soup, competitor_container, expand=False)

        # Assert
        assert result["success"] is True
        assert "soup" in result
        assert "popup_container" in result
        assert "competitor_container" in result
        self.mock_page.click.assert_called()

    def test_present_competitor_popup_no_page(self):
        """测试无浏览器页面的情况"""
        # Arrange
        self.mock_browser_service.get_page.return_value = None
        soup = Mock()
        competitor_container = Mock()

        # Act
        result = self.scraper._present_competitor_popup(soup, competitor_container, expand=False)

        # Assert
        assert result["success"] is False
        assert result["error"] == "浏览器页面不可用"

    def test_present_competitor_popup_click_failure(self):
        """测试点击失败的情况"""
        # Arrange
        self.mock_page.query_selector.return_value = None  # 找不到元素
        soup = Mock()
        competitor_container = Mock()

        # Act
        result = self.scraper._present_competitor_popup(soup, competitor_container, expand=False)

        # Assert
        assert result["success"] is False

    # ========== _expand_competitor_list 方法测试 ==========

    def test_expand_competitor_list_success(self):
        """测试成功展开竞品列表"""
        # Arrange
        self.mock_page.query_selector.return_value = True

        # Act
        result = self.scraper._expand_competitor_list()

        # Assert
        assert result is True
        self.mock_page.click.assert_called()
        self.mock_wait_utils.smart_wait.assert_called_with(1.0)

    def test_expand_competitor_list_no_page(self):
        """测试无浏览器页面的展开操作"""
        # Arrange
        self.mock_browser_service.get_page.return_value = None

        # Act
        result = self.scraper._expand_competitor_list()

        # Assert
        assert result is False

    def test_expand_competitor_list_no_expand_button(self):
        """测试找不到展开按钮的情况"""
        # Arrange
        self.mock_page.query_selector.return_value = None

        # Act
        result = self.scraper._expand_competitor_list()

        # Assert
        assert result is True  # 找不到展开按钮也算成功

    def test_expand_competitor_list_click_exception(self):
        """测试点击异常的情况"""
        # Arrange
        self.mock_page.query_selector.return_value = True
        self.mock_page.click.side_effect = Exception("Click failed")

        # Act
        result = self.scraper._expand_competitor_list()

        # Assert
        assert result is True  # 即使点击失败也返回True

    # ========== extract_competitors_from_content 方法测试 ==========

    def test_extract_competitors_from_content_success(self):
        """测试成功提取竞品信息"""
        # Arrange
        html_content = self._create_mock_html_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        with patch.object(self.scraper, '_find_competitor_elements_in_soup') as mock_find_elements, \
             patch.object(self.scraper, '_extract_competitor_from_element') as mock_extract_element:
            
            mock_find_elements.return_value = (self._create_mock_competitor_elements(), ".pdp_bk3")
            mock_extract_element.return_value = {
                "store_name": "测试店铺",
                "price": "1000",
                "store_link": "/seller/123456",
                "store_id": "123456",
                "ranking": 1
            }

            # Act
            result = self.scraper.extract_competitors_from_content(soup, max_competitors=10)

            # Assert
            assert isinstance(result, list)
            assert len(result) > 0
            assert result[0]["store_name"] == "测试店铺"
            mock_find_elements.assert_called_once_with(soup)
            mock_extract_element.assert_called()

    def test_extract_competitors_from_content_empty_container(self):
        """测试空容器的情况"""
        # Arrange
        full_pop_layer = None

        # Act
        result = self.scraper.extract_competitors_from_content(full_pop_layer)

        # Assert
        assert result == []

    def test_extract_competitors_from_content_no_elements_found(self):
        """测试找不到竞品元素的情况"""
        # Arrange
        html_content = "<html><body></body></html>"
        soup = BeautifulSoup(html_content, 'html.parser')
        
        with patch.object(self.scraper, '_find_competitor_elements_in_soup') as mock_find_elements:
            mock_find_elements.return_value = ([], None)

            # Act
            result = self.scraper.extract_competitors_from_content(soup)

            # Assert
            assert result == []

    def test_extract_competitors_from_content_with_limit(self):
        """测试限制竞品数量的提取"""
        # Arrange
        html_content = self._create_mock_html_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        max_competitors = 1
        
        with patch.object(self.scraper, '_find_competitor_elements_in_soup') as mock_find_elements, \
             patch.object(self.scraper, '_extract_competitor_from_element') as mock_extract_element:
            
            mock_find_elements.return_value = (self._create_mock_competitor_elements() * 3, ".pdp_bk3")
            mock_extract_element.return_value = {
                "store_name": "测试店铺",
                "price": "1000",
                "store_link": "/seller/123456",
                "store_id": "123456",
                "ranking": 1
            }

            # Act
            result = self.scraper.extract_competitors_from_content(soup, max_competitors=max_competitors)

            # Assert
            assert len(result) <= max_competitors

    # ========== _extract_store_id_from_url 方法测试 ==========

    def test_extract_store_id_from_url_success(self):
        """测试成功从URL提取店铺ID"""
        # Arrange
        test_cases = [
            ("/seller/123456", "123456"),
            ("/seller/789012/", "789012"),
            ("https://www.ozon.ru/seller/555666", "555666"),
            ("/seller/999888?param=value", "999888")
        ]

        for href, expected_id in test_cases:
            # Act
            result = self.scraper._extract_store_id_from_url(href)
            
            # Assert
            assert result == expected_id

    def test_extract_store_id_from_url_no_match(self):
        """测试无法匹配店铺ID的URL"""
        # Arrange
        invalid_urls = [
            "/product/123456",
            "/category/electronics",
            "",
            None
        ]

        for href in invalid_urls:
            # Act
            result = self.scraper._extract_store_id_from_url(href)
            
            # Assert
            assert result is None

    # ========== _find_competitor_elements_in_soup 方法测试 ==========

    def test_find_competitor_elements_in_soup_success(self):
        """测试成功查找竞品元素"""
        # Arrange
        html_content = self._create_mock_html_content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Act
        elements, selector = self.scraper._find_competitor_elements_in_soup(soup)

        # Assert
        assert isinstance(elements, list)
        assert len(elements) > 0
        assert selector is not None

    def test_find_competitor_elements_in_soup_no_elements(self):
        """测试找不到竞品元素"""
        # Arrange
        html_content = "<html><body><div>无竞品信息</div></body></html>"
        soup = BeautifulSoup(html_content, 'html.parser')

        # Act
        elements, selector = self.scraper._find_competitor_elements_in_soup(soup)

        # Assert
        assert elements == []
        assert selector is None

    # ========== _extract_competitor_from_element 方法测试 ==========

    def test_extract_competitor_from_element_success(self):
        """测试成功从元素提取竞品信息"""
        # Arrange
        element_html = """
        <div class="pdp_bk3">
            <div class="seller-name">测试店铺名称</div>
            <div class="seller-price">1500₽</div>
            <a href="/seller/789012">店铺链接</a>
        </div>
        """
        element = BeautifulSoup(element_html, 'html.parser').find('div')
        ranking = 1

        # Act
        result = self.scraper._extract_competitor_from_element(element, ranking)

        # Assert
        assert isinstance(result, dict)
        assert "store_name" in result
        assert "price" in result
        assert "store_link" in result
        assert "store_id" in result
        assert "ranking" in result
        assert result["ranking"] == ranking

    def test_extract_competitor_from_element_missing_data(self):
        """测试缺少数据的元素"""
        # Arrange
        element_html = "<div class='pdp_bk3'><div>不完整数据</div></div>"
        element = BeautifulSoup(element_html, 'html.parser').find('div')
        ranking = 1

        # Act
        result = self.scraper._extract_competitor_from_element(element, ranking)

        # Assert
        # 即使数据不完整，也应该返回一个字典，包含可获取的信息
        assert isinstance(result, dict)
        assert result["ranking"] == ranking

    # ========== 异常处理和边界条件测试 ==========

    def test_scrape_with_invalid_url(self):
        """测试无效URL的处理"""
        # Arrange
        invalid_url = "invalid-url"

        # Act & Assert
        # 应该能处理无效URL而不抛出异常
        result = self.scraper.scrape(url=invalid_url)
        assert isinstance(result, ScrapingResult)

    def test_scrape_with_network_timeout(self):
        """测试网络超时的处理"""
        # Arrange
        self.mock_scraping_utils.wait_for_content_smart.side_effect = Exception("Network timeout")
        test_url = "https://www.ozon.ru/product/1176594312"

        # Act
        result = self.scraper.scrape(url=test_url)

        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is False
        assert "timeout" in result.error.lower() or "exception" in result.error.lower()

    def test_extract_competitors_exception_handling(self):
        """测试提取竞品时的异常处理"""
        # Arrange
        html_content = self._create_mock_html_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        with patch.object(self.scraper, '_find_competitor_elements_in_soup') as mock_find_elements:
            mock_find_elements.side_effect = Exception("Extraction error")

            # Act
            result = self.scraper.extract_competitors_from_content(soup)

            # Assert
            assert result == []

    # ========== 参数化测试 ==========

    @pytest.mark.parametrize("max_competitors", [1, 5, 10, 20])
    def test_scrape_with_different_max_competitors(self, max_competitors):
        """参数化测试不同的最大竞品数量"""
        # Arrange
        test_url = "https://www.ozon.ru/product/1176594312"
        
        # Act
        result = self.scraper.scrape(url=test_url, max_competitors=max_competitors)

        # Assert
        assert result.success is True
        assert len(result.data) <= max_competitors

    @pytest.mark.parametrize("expand_needed", [True, False])
    def test_scrape_with_different_expand_options(self, expand_needed):
        """参数化测试不同的展开选项"""
        # Arrange
        test_url = "https://www.ozon.ru/product/1176594312"
        
        # Act
        result = self.scraper.scrape(url=test_url, expand_pop_layer=expand_needed)

        # Assert
        assert isinstance(result, ScrapingResult)
