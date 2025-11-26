#!/usr/bin/env python3
"""
跟卖检测数据准确性测试

测试跟卖检测服务提取数据的准确性
"""

import unittest
import logging
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup

from common.services.competitor_detection_service import CompetitorDetectionService
from common.models.scraping_result import CompetitorInfo, CompetitorDetectionResult
from common.config.ozon_selectors_config import OzonSelectorsConfig


class TestCompetitorDataAccuracy(unittest.TestCase):
    """跟卖检测数据准确性测试类"""

    def setUp(self):
        """测试初始化"""
        self.logger = logging.getLogger(__name__)
        self.selectors_config = OzonSelectorsConfig()
        self.service = CompetitorDetectionService(
            selectors_config=self.selectors_config,
            logger=self.logger
        )

    def test_store_name_extraction_accuracy(self):
        """测试店铺名称提取准确性"""
        html_content = """
        <div class="competitor">
            <a class="seller-name" href="https://www.ozon.ru/seller/test-123/">Тестовый магазин</a>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.store_name, "Тестовый магазин")

    def test_price_extraction_accuracy(self):
        """测试价格提取准确性"""
        test_cases = [
            ("<span class='price'>1 500 ₽</span>", 1500.0),
            ("<span class='price'>от 1 200 ₽</span>", 1200.0),
            ("<span class='price'>до 2 000 ₽</span>", 2000.0),
        ]
        
        for html_price, expected_price in test_cases:
            html_content = f"<div class='competitor'>{html_price}</div>"
            soup = BeautifulSoup(html_content, 'html.parser')
            element = soup.select_one('.competitor')
            
            competitor = self.service._parse_competitor_item(element)
            self.assertIsInstance(competitor, CompetitorInfo)
            self.assertEqual(competitor.price, expected_price, 
                           f"价格提取失败: {html_price} 应该提取为 {expected_price}, 实际为 {competitor.price}")

    def test_store_url_extraction_accuracy(self):
        """测试店铺URL提取准确性"""
        html_content = """
        <div class="competitor">
            <a class="seller-name" href="https://www.ozon.ru/seller/test-store-123/">Test Store</a>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.store_url, "https://www.ozon.ru/seller/test-store-123/")

    def test_rating_extraction_accuracy(self):
        """测试评分提取准确性"""
        html_content = """
        <div class="competitor">
            <span class="rating">4.5</span>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.rating, 4.5)

    def test_sales_count_extraction_accuracy(self):
        """测试销量提取准确性"""
        html_content = """
        <div class="competitor">
            <span class="sales">1000+ продаж</span>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.sales_count, 1000)

    def test_delivery_info_extraction_accuracy(self):
        """测试配送信息提取准确性"""
        html_content = """
        <div class="competitor">
            <span class="delivery">Доставим завтра</span>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.delivery_info, "Доставим завтра")

    def test_complete_competitor_info_extraction(self):
        """测试完整跟卖信息提取准确性"""
        html_content = """
        <div class="competitor">
            <a class="seller-name" href="https://www.ozon.ru/seller/test-123/">Тестовый магазин</a>
            <span class="price">1 500 ₽</span>
            <span class="rating">4.8</span>
            <span class="sales">500 продаж</span>
            <span class="delivery">Доставим 5 декабря</span>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one('.competitor')
        
        competitor = self.service._parse_competitor_item(element)
        self.assertIsInstance(competitor, CompetitorInfo)
        self.assertEqual(competitor.store_name, "Тестовый магазин")
        self.assertEqual(competitor.price, 1500.0)
        self.assertEqual(competitor.rating, 4.8)
        self.assertEqual(competitor.sales_count, 500)
        self.assertEqual(competitor.delivery_info, "Доставим 5 декабря")

    def test_competitor_detection_result_accuracy(self):
        """测试跟卖检测结果准确性"""
        html_content = """
        <html>
            <body>
                <div class="pdp_bk3">
                    <div class="competitor">
                        <a class="seller-name" href="https://www.ozon.ru/seller/store1/">Магазин 1</a>
                        <span class="price">1 000 ₽</span>
                    </div>
                    <div class="competitor">
                        <a class="seller-name" href="https://www.ozon.ru/seller/store2/">Магазин 2</a>
                        <span class="price">1 200 ₽</span>
                    </div>
                </div>
            </body>
        </html>
        """
        
        result = self.service.detect_competitors(html_content)
        self.assertIsInstance(result, CompetitorDetectionResult)
        self.assertTrue(result.has_competitors)
        self.assertEqual(result.competitor_count, 2)
        self.assertEqual(len(result.competitors), 2)
        
        # 验证第一个跟卖店铺
        competitor1 = result.competitors[0]
        self.assertEqual(competitor1.store_name, "Магазин 1")
        self.assertEqual(competitor1.price, 1000.0)
        
        # 验证第二个跟卖店铺
        competitor2 = result.competitors[1]
        self.assertEqual(competitor2.store_name, "Магазин 2")
        self.assertEqual(competitor2.price, 1200.0)


if __name__ == "__main__":
    unittest.main()
