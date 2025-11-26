#!/usr/bin/env python3
"""
跟卖检测性能测试

测试跟卖检测服务的性能指标
"""

import unittest
import logging
import time
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup

from common.services.competitor_detection_service import CompetitorDetectionService
from common.models.scraping_result import CompetitorInfo, CompetitorDetectionResult
from common.config.ozon_selectors_config import OzonSelectorsConfig


class TestCompetitorPerformance(unittest.TestCase):
    """跟卖检测性能测试类"""

    def setUp(self):
        """测试初始化"""
        self.logger = logging.getLogger(__name__)
        self.selectors_config = OzonSelectorsConfig()
        self.service = CompetitorDetectionService(
            selectors_config=self.selectors_config,
            logger=self.logger
        )

    def test_detect_competitors_performance(self):
        """测试跟卖检测性能"""
        # 创建较大的HTML内容用于性能测试
        competitors_html = ""
        for i in range(50):  # 创建50个跟卖店铺
            competitors_html += f"""
            <div class="competitor">
                <span class="store-name">Test Store {i}</span>
                <span class="price">{1000 + i * 10} ₽</span>
                <a href="https://www.ozon.ru/seller/test-{i}/">Store Link</a>
            </div>
            """
        
        html_content = f"""
        <html>
            <body>
                <div class="pdp_bk3">
                    {competitors_html}
                </div>
            </body>
        </html>
        """
        
        # 测试性能
        start_time = time.time()
        result = self.service.detect_competitors(html_content)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 验证结果正确性
        self.assertIsInstance(result, CompetitorDetectionResult)
        self.assertTrue(result.has_competitors)
        self.assertEqual(result.competitor_count, 50)
        self.assertEqual(len(result.competitors), 50)
        
        # 性能应该在合理范围内（假设应该在1秒内完成）
        self.assertLess(execution_time, 1.0, f"跟卖检测耗时过长: {execution_time:.4f}秒")

    def test_filter_competitors_performance(self):
        """测试跟卖过滤性能"""
        # 创建大量跟卖店铺用于性能测试 (价格从1到500，共500个店铺，避免价格为0的问题)
        competitors = []
        for i in range(1, 501):  # 1-500包含500个数字 (1,2,3,...,500)
            competitors.append(CompetitorInfo(store_name=f"Store {i}", price=float(i)))

        # 测试过滤性能 (过滤价格<=500的店铺)
        start_time = time.time()
        filtered = self.service.filter_competitors_by_price(competitors, 500.0)
        end_time = time.time()

        execution_time = end_time - start_time

        # 验证结果正确性
        # 价格<=500的店铺数量应该是500个 (1,2,3,...,500)，价格为0的店铺会被过滤掉
        self.assertEqual(len(filtered), 500)
        
        # 性能应该在合理范围内（假设应该在0.1秒内完成）
        self.assertLess(execution_time, 0.1, f"跟卖过滤耗时过长: {execution_time:.4f}秒")

    def test_sort_competitors_performance(self):
        """测试跟卖排序性能"""
        # 创建大量跟卖店铺用于性能测试
        competitors = []
        import random
        for i in range(1000):
            # 随机价格
            price = random.uniform(100.0, 5000.0)
            competitors.append(CompetitorInfo(store_name=f"Store {i}", price=price))
        
        # 测试排序性能
        start_time = time.time()
        sorted_competitors = self.service.sort_competitors_by_price(competitors, ascending=True)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 验证结果正确性（检查是否已排序）
        for i in range(len(sorted_competitors) - 1):
            price1 = sorted_competitors[i].price or float('inf')
            price2 = sorted_competitors[i + 1].price or float('inf')
            self.assertLessEqual(price1, price2)
        
        # 性能应该在合理范围内（假设应该在0.1秒内完成）
        self.assertLess(execution_time, 0.1, f"跟卖排序耗时过长: {execution_time:.4f}秒")


if __name__ == "__main__":
    unittest.main()
