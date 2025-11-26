#!/usr/bin/env python3
"""
跟卖检测边缘情况测试

测试各种异常和边界条件下的跟卖检测功能
"""

import unittest
import logging
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup

from common.services.competitor_detection_service import CompetitorDetectionService
from common.models.scraping_result import CompetitorInfo, CompetitorDetectionResult
from common.config.ozon_selectors_config import OzonSelectorsConfig


class TestCompetitorEdgeCases(unittest.TestCase):
    """跟卖检测边缘情况测试类"""

    def setUp(self):
        """测试初始化"""
        self.logger = logging.getLogger(__name__)
        self.selectors_config = OzonSelectorsConfig()
        self.service = CompetitorDetectionService(
            selectors_config=self.selectors_config,
            logger=self.logger
        )

    def test_detect_competitors_with_malformed_html(self):
        """测试畸形HTML内容的跟卖检测"""
        malformed_html = "<html><body><div class='pdp_bk3'><div class='competitor'><span class='store-name'>Test Store</span></div></body></html>"
        result = self.service.detect_competitors(malformed_html)
        # 即使HTML不完整也应该正确处理
        self.assertIsInstance(result, CompetitorDetectionResult)

    def test_detect_competitors_with_none_content(self):
        """测试None内容的跟卖检测"""
        result = self.service.detect_competitors(None)
        self.assertIsInstance(result, CompetitorDetectionResult)
        self.assertFalse(result.has_competitors)

    def test_parse_competitor_item_with_missing_fields(self):
        """测试缺少字段的跟卖项解析"""
        html_content = """
        <div class="competitor">
            <span class="store-name">Test Store</span>
            <!-- 缺少价格和链接 -->
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.store_name, "Test Store")
        # 缺少的字段应该为None
        self.assertIsNone(competitor.price)

    def test_parse_competitor_item_with_invalid_price(self):
        """测试无效价格的跟卖项解析"""
        html_content = """
        <div class="competitor">
            <span class="store-name">Test Store</span>
            <span class="price">Invalid Price</span>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.store_name, "Test Store")
        self.assertIsNone(competitor.price)

    def test_extract_competitors_with_empty_element(self):
        """测试空元素的跟卖提取"""
        html_content = "<div class='pdp_bk3'></div>"
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.pdp_bk3')
        
        competitors = self.service._extract_competitors_from_element(element)
        self.assertIsInstance(competitors, list)
        self.assertEqual(len(competitors), 0)

    def test_filter_competitors_with_none_prices(self):
        """测试包含None价格的跟卖过滤"""
        competitors = [
            CompetitorInfo(store_name="Store 1", price=500.0),
            CompetitorInfo(store_name="Store 2", price=None),
            CompetitorInfo(store_name="Store 3", price=800.0)
        ]
        
        filtered = self.service.filter_competitors_by_price(competitors, 1000.0)
        # None价格的应该被过滤掉
        self.assertEqual(len(filtered), 2)

    def test_sort_competitors_with_none_prices(self):
        """测试包含None价格的跟卖排序"""
        competitors = [
            CompetitorInfo(store_name="Store 1", price=1500.0),
            CompetitorInfo(store_name="Store 2", price=None),
            CompetitorInfo(store_name="Store 3", price=800.0)
        ]
        
        sorted_competitors = self.service.sort_competitors_by_price(competitors, ascending=True)
        # None价格的应该排在最后
        self.assertEqual(sorted_competitors[0].price, 800.0)
        self.assertEqual(sorted_competitors[1].price, 1500.0)
        self.assertIsNone(sorted_competitors[2].price)


if __name__ == "__main__":
    unittest.main()
