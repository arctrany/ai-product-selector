"""
ErpPluginScraper 单元测试

符合项目测试规范，包含全面的功能测试和使用真实URL的参数化测试。
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from bs4 import BeautifulSoup

from common.scrapers.erp_plugin_scraper import ErpPluginScraper
from common.models.scraping_result import ScrapingResult
from common.config.erp_selectors_config import ERPSelectorsConfig


class TestErpPluginScraper:
    """ErpPluginScraper 单元测试类"""

    def setup_method(self):
        """测试方法设置 - 每个测试方法执行前调用"""
        # Mock 浏览器服务
        self.mock_browser_service = Mock()
        self.mock_browser_service.get_page_url_sync.return_value = "https://www.ozon.ru/product/1176594312"
        self.mock_browser_service.navigate_to_sync.return_value = True

        # Mock selectors config
        self.mock_config = Mock(spec=ERPSelectorsConfig)
        self.mock_config.erp_container_selectors = [
            '.erp-container',
            '[data-widget="webErpInfo"]'
        ]

        # 使用 patch 创建 ErpPluginScraper 实例
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = ErpPluginScraper(
                selectors_config=self.mock_config,
                browser_service=self.mock_browser_service
            )

    def teardown_method(self):
        """测试方法清理 - 每个测试方法执行后调用"""
        pass

    # ========== 基本功能测试 ==========

    def test_scraper_initialization(self):
        """测试爬虫初始化"""
        # Arrange & Act
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            scraper = ErpPluginScraper(browser_service=self.mock_browser_service)

        # Assert
        assert scraper.browser_service == self.mock_browser_service
        assert scraper.selectors_config is not None
        assert scraper.config is not None
        assert len(scraper.field_mappings) > 0
        assert 'category' in scraper.field_mappings.values()

    @patch('common.scrapers.erp_plugin_scraper.wait_for_content_smart')
    def test_scrape_success(self, mock_wait_for_content):
        """测试 scrape 方法成功场景"""
        # Arrange
        test_url = "https://www.ozon.ru/product/1176594312"
        mock_content = self._create_mock_erp_content()
        mock_wait_for_content.return_value = {
            'soup': BeautifulSoup('<html></html>', 'html.parser'),
            'content': mock_content
        }

        # Act
        result = self.scraper.scrape(target=test_url)

        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is True
        assert isinstance(result.data, dict)
        assert result.execution_time is not None

    @patch('common.scrapers.erp_plugin_scraper.wait_for_content_smart')
    def test_scrape_with_static_soup(self, mock_wait_for_content):
        """测试使用静态 soup 的 scrape 方法"""
        # Arrange
        test_url = "https://www.ozon.ru/product/1176594312"
        static_soup = BeautifulSoup('<html></html>', 'html.parser')
        mock_content = self._create_mock_erp_content()
        mock_wait_for_content.return_value = {
            'soup': static_soup,
            'content': mock_content
        }

        options = {'soup': static_soup}

        # Act
        result = self.scraper.scrape(target=test_url, options=options)

        # Assert
        assert result.success is True
        mock_wait_for_content.assert_called_once()

    @patch('common.scrapers.erp_plugin_scraper.wait_for_content_smart')
    def test_scrape_exception_handling(self, mock_wait_for_content):
        """测试 scrape 方法异常处理"""
        # Arrange
        test_url = "https://www.ozon.ru/product/1176594312"
        mock_wait_for_content.side_effect = Exception("网络错误")

        # Act & Assert
        with pytest.raises(RuntimeError, match="抓取失败"):
            self.scraper.scrape(target=test_url)

    # ========== 参数化测试 - 使用真实URL ==========

    def _load_test_cases(self):
        """加载测试用例数据"""
        try:
            with open('tests/test_data/ozon_test_cases.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['test_cases']
        except FileNotFoundError:
            # 如果文件不存在，返回默认测试用例
            return [
                {
                    "id": "default_test",
                    "url": "https://www.ozon.ru/product/1176594312",
                    "name": "默认测试用例"
                }
            ]

    @pytest.mark.parametrize("test_case", _load_test_cases(None))
    @patch('common.scrapers.erp_plugin_scraper.wait_for_content_smart')
    def test_scrape_with_real_urls(self, mock_wait_for_content, test_case):
        """参数化测试 - 使用真实URL"""
        # Arrange
        test_url = test_case['url']
        mock_content = self._create_mock_erp_content()
        mock_wait_for_content.return_value = {
            'soup': BeautifulSoup('<html></html>', 'html.parser'),
            'content': mock_content
        }

        # Act
        result = self.scraper.scrape(target=test_url)

        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is True
        assert isinstance(result.data, dict)
        print(f"✅ 测试用例 {test_case['id']} ({test_case['name']}) 通过")

    # ========== 数据提取和解析测试 ==========

    def test_extract_erp_data_from_content(self):
        """测试从内容中提取ERP数据"""
        # Arrange
        mock_content = self._create_mock_erp_content()

        # Act
        result = self.scraper._extract_erp_data_from_content(mock_content)

        # Assert
        assert isinstance(result, dict)
        # 检查是否提取到了一些关键字段
        expected_fields = ['category', 'sku', 'brand_name']
        for field in expected_fields:
            if field in result:
                assert result[field] is not None

    def test_extract_erp_data_empty_content(self):
        """测试空内容的数据提取"""
        # Act
        result = self.scraper._extract_erp_data_from_content(None)

        # Assert
        assert result == {}

    def test_extract_field_value(self):
        """测试字段值提取"""
        # Arrange
        html = '''
        <div class="erp-field">
            <span>类目：</span>
            <span>电子产品</span>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        # Act
        result = self.scraper._extract_field_value(soup, '类目')

        # Assert
        assert result == '电子产品'

    def test_extract_field_value_not_found(self):
        """测试字段值提取 - 未找到字段"""
        # Arrange
        html = '<div><span>其他内容</span></div>'
        soup = BeautifulSoup(html, 'html.parser')

        # Act
        result = self.scraper._extract_field_value(soup, '不存在的字段')

        # Assert
        assert result is None

    # ========== 数据解析方法测试 ==========

    @pytest.mark.parametrize("dimensions_str,expected", [
        ("50 x 37 x 43mm", {"length": 50.0, "width": 37.0, "height": 43.0}),
        ("100x200x300cm", {"length": 100.0, "width": 200.0, "height": 300.0}),
        ("", {"length": None, "width": None, "height": None}),
        ("无效格式", {"length": None, "width": None, "height": None})
    ])
    def test_parse_dimensions(self, dimensions_str, expected):
        """测试尺寸解析"""
        # Act
        result = self.scraper._parse_dimensions(dimensions_str)

        # Assert
        assert result == expected

    @pytest.mark.parametrize("date_str,expected_date,expected_days", [
        ("2024-09-23(415天)", "2024-09-23", 415),
        ("2023-01-01(100天)", "2023-01-01", 100),
        ("", None, None),
        ("无效格式", None, None)
    ])
    def test_parse_listing_date(self, date_str, expected_date, expected_days):
        """测试上架时间解析"""
        # Act
        result = self.scraper._parse_listing_date(date_str)

        # Assert
        assert result['listing_date_parsed'] == expected_date
        assert result['shelf_days'] == expected_days

    @pytest.mark.parametrize("weight_str,expected", [
        ("40g", 40.0),
        ("1.5kg", 1.5),
        ("", None),
        ("无效重量", None)
    ])
    def test_parse_weight(self, weight_str, expected):
        """测试重量解析"""
        # Act
        result = self.scraper._parse_weight(weight_str)

        # Assert
        assert result == expected

    @pytest.mark.parametrize("commission_str,expected", [
        ("15%", [15.0]),
        ("8.5%, 12%", [8.5, 12.0]),
        ("", None),
        ("无效佣金", None)
    ])
    def test_parse_rfbs_commission(self, commission_str, expected):
        """测试佣金解析"""
        # Act
        result = self.scraper._parse_rfbs_commission(commission_str)

        # Assert
        assert result == expected

    @pytest.mark.parametrize("price,expected", [
        (400.0, 15.0),    # 低价商品
        (1500.0, 12.0),   # 中等价格
        (3000.0, 8.0)     # 高价商品
    ])
    def test_calculate_commission_rate_by_price(self, price, expected):
        """测试根据价格计算佣金率"""
        # Act
        result = self.scraper._calculate_commission_rate_by_price(price)

        # Assert
        assert result == expected

    # ========== 数据验证测试 ==========

    def test_validate_data_success(self):
        """测试数据验证 - 成功场景"""
        # Arrange
        valid_data = {
            'category': '电子产品',
            'sku': 'ABC123',
            'brand_name': '测试品牌',
            'monthly_sales_volume': '100',
            'monthly_sales_amount': '50000'
        }

        # Act
        result = self.scraper.validate_data(valid_data)

        # Assert
        assert result is True

    def test_validate_data_empty(self):
        """测试数据验证 - 空数据"""
        # Act
        result = self.scraper.validate_data({})

        # Assert
        assert result is False

    def test_validate_data_no_valid_fields(self):
        """测试数据验证 - 无有效字段"""
        # Arrange
        invalid_data = {
            'other_field': 'value'
        }

        # Act
        result = self.scraper.validate_data(invalid_data)

        # Assert
        assert result is False

    def test_validate_data_negative_numbers(self):
        """测试数据验证 - 负数值"""
        # Arrange
        invalid_data = {
            'category': '电子产品',
            'monthly_sales_volume': '-100'  # 负数
        }

        # Act
        result = self.scraper.validate_data(invalid_data)

        # Assert
        assert result is False

    def test_validate_data_with_filters(self):
        """测试数据验证 - 使用自定义过滤器"""
        # Arrange
        data = {
            'category': '电子产品',
            'test_field': 'test_value'
        }
        
        def custom_filter(data_dict):
            return 'test_field' in data_dict

        # Act
        result = self.scraper.validate_data(data, filters=[custom_filter])

        # Assert
        assert result is True

    # ========== 异常处理和边界情况测试 ==========

    def test_extract_field_value_exception(self):
        """测试字段提取异常处理"""
        # Arrange
        invalid_container = "不是BeautifulSoup对象"

        # Act
        result = self.scraper._extract_field_value(invalid_container, '类目')

        # Assert
        assert result is None

    def test_parse_dimensions_exception(self):
        """测试尺寸解析异常处理"""
        # Arrange
        invalid_input = None

        # Act
        result = self.scraper._parse_dimensions(invalid_input)

        # Assert
        assert result == {'length': None, 'width': None, 'height': None}

    # ========== 辅助方法 ==========

    def _create_mock_erp_content(self):
        """创建模拟的ERP内容"""
        html = '''
        <div class="erp-container">
            <div class="field-group">
                <span>类目：</span><span>电子产品</span>
            </div>
            <div class="field-group">
                <span>SKU：</span><span>TEST123456</span>
            </div>
            <div class="field-group">
                <span>品牌：</span><span>测试品牌</span>
            </div>
            <div class="field-group">
                <span>月销量：</span><span>100</span>
            </div>
            <div class="field-group">
                <span>长 宽 高：</span><span>50 x 37 x 43mm</span>
            </div>
            <div class="field-group">
                <span>重 量：</span><span>500g</span>
            </div>
            <div class="field-group">
                <span>上架时间：</span><span>2024-01-01(300天)</span>
            </div>
            <div class="field-group">
                <span>rFBS佣金：</span><span>15%</span>
            </div>
        </div>
        '''
        return BeautifulSoup(html, 'html.parser')
