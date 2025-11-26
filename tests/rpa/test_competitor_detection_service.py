#!/usr/bin/env python3
"""
CompetitorDetectionService 测试用例

测试跟卖检测服务的各项功能
"""

import unittest
import logging
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup

from common.services.competitor_detection_service import CompetitorDetectionService
from common.models.scraping_result import CompetitorInfo, CompetitorDetectionResult
from common.config.ozon_selectors_config import OzonSelectorsConfig


class TestCompetitorDetectionService(unittest.TestCase):
    """CompetitorDetectionService 测试类"""

    def setUp(self):
        """测试初始化"""
        self.logger = logging.getLogger(__name__)
        self.selectors_config = OzonSelectorsConfig()
        self.service = CompetitorDetectionService(
            selectors_config=self.selectors_config,
            logger=self.logger
        )

    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.service, CompetitorDetectionService)
        self.assertEqual(self.service.selectors_config, self.selectors_config)

    def test_detect_competitors_with_empty_content(self):
        """测试空内容的跟卖检测"""
        result = self.service.detect_competitors("")
        self.assertIsInstance(result, CompetitorDetectionResult)
        self.assertFalse(result.has_competitors)
        self.assertEqual(result.competitor_count, 0)

    def test_detect_competitors_with_no_competitor_element(self):
        """测试无跟卖元素的页面内容"""
        html_content = "<html><body><div>No competitors here</div></body></html>"
        result = self.service.detect_competitors(html_content)
        self.assertIsInstance(result, CompetitorDetectionResult)
        self.assertFalse(result.has_competitors)
        self.assertEqual(result.competitor_count, 0)

    def test_extract_competitors_from_element_success(self):
        """测试成功提取跟卖元素"""
        # 创建模拟的跟卖HTML元素
        html_content = """
        <div class="pdp_bk3">
            <div class="competitor">
                <span class="store-name">Test Store</span>
                <span class="price">1000 ₽</span>
                <a href="https://www.ozon.ru/seller/test-123/">Store Link</a>
            </div>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.pdp_bk3')
        
        competitors = self.service._extract_competitors_from_element(element)
        self.assertIsInstance(competitors, list)
        self.assertEqual(len(competitors), 1)
        
        competitor = competitors[0]
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.store_name, "Test Store")

    def test_parse_competitor_item_success(self):
        """测试成功解析跟卖项"""
        html_content = """
        <div class="competitor">
            <span class="store-name">Test Store</span>
            <span class="price">1000 ₽</span>
            <a href="https://www.ozon.ru/seller/test-123/">Store Link</a>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.store_name, "Test Store")
        self.assertEqual(competitor.price, 1000.0)

    def test_filter_competitors_by_price(self):
        """测试按价格过滤跟卖店铺"""
        competitors = [
            CompetitorInfo(store_name="Store 1", price=500.0),
            CompetitorInfo(store_name="Store 2", price=1500.0),
            CompetitorInfo(store_name="Store 3", price=800.0)
        ]
        
        filtered = self.service.filter_competitors_by_price(competitors, 1000.0)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].store_name, "Store 1")
        self.assertEqual(filtered[1].store_name, "Store 3")

    def test_sort_competitors_by_price(self):
        """测试按价格排序跟卖店铺"""
        competitors = [
            CompetitorInfo(store_name="Store 1", price=1500.0),
            CompetitorInfo(store_name="Store 2", price=500.0),
            CompetitorInfo(store_name="Store 3", price=800.0)
        ]
        
        sorted_competitors = self.service.sort_competitors_by_price(competitors, ascending=True)
        self.assertEqual(sorted_competitors[0].price, 500.0)
        self.assertEqual(sorted_competitors[1].price, 800.0)
        self.assertEqual(sorted_competitors[2].price, 1500.0)


if __name__ == "__main__":
    unittest.main()
