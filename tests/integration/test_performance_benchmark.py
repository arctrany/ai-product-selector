#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能基准测试

测试重构前后的性能对比，监控关键指标：
1. 时序控制成功率
2. 数据抓取成功率
3. 平均响应时间
4. 错误率和重试次数
"""

import sys
import time
import unittest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock

from tests.rpa.base_scraper_test import BaseScraperTest
from common.utils.wait_utils import WaitUtils
from common.utils.scraping_utils import ScrapingUtils


class TestPerformanceBenchmark(BaseScraperTest):
    """性能基准测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        self.performance_metrics = {
            'wait_utils': [],
            'scraping_utils': [],
            'timing_success_rate': [],
            'scraping_success_rate': []
        }
    
    def test_wait_utils_performance(self):
        """测试 WaitUtils 性能"""
        print("\n" + "="*80)
        print("🔍 测试 WaitUtils 性能")
        print("="*80)
        
        # 创建 Mock 浏览器服务
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_browser.page = mock_page
        
        # 模拟元素查找
        mock_element = MagicMock()
        mock_element.is_visible.return_value = True
        mock_page.wait_for_selector.return_value = mock_element
        
        wait_utils = WaitUtils(mock_browser, self.logger)
        
        # 测试等待元素可见
        iterations = 10
        total_time = 0
        success_count = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                result = wait_utils.wait_for_element_visible('.test-selector', timeout=1000)
                if result:
                    success_count += 1
                elapsed = time.time() - start_time
                total_time += elapsed
                self.performance_metrics['wait_utils'].append(elapsed)
            except Exception as e:
                self.logger.warning(f"等待元素失败: {e}")
        
        avg_time = total_time / iterations
        success_rate = (success_count / iterations) * 100
        
        print(f"✅ WaitUtils 平均响应时间: {avg_time*1000:.2f}ms")
        print(f"✅ 成功率: {success_rate:.1f}%")
        
        self.performance_metrics['timing_success_rate'].append(success_rate)
        
        # 性能断言
        self.assertGreater(success_rate, 80, "时序控制成功率应大于80%")
        self.assertLess(avg_time, 0.5, "平均响应时间应小于500ms")
    
    def test_scraping_utils_performance(self):
        """测试 ScrapingUtils 性能"""
        print("\n" + "="*80)
        print("🔍 测试 ScrapingUtils 性能")
        print("="*80)
        
        scraping_utils = ScrapingUtils(self.logger)
        
        # 测试价格提取性能
        test_prices = [
            "14\u2009482\u2009₽",
            "14 556 ₽",
            "14,562₽",
            "₽14602",
            "14864 руб"
        ]
        
        iterations = 100
        total_time = 0
        success_count = 0
        
        for _ in range(iterations):
            for price_str in test_prices:
                start_time = time.time()
                try:
                    price = scraping_utils.extract_price(price_str)
                    if price and price > 0:
                        success_count += 1
                    elapsed = time.time() - start_time
                    total_time += elapsed
                    self.performance_metrics['scraping_utils'].append(elapsed)
                except Exception as e:
                    self.logger.warning(f"价格提取失败: {e}")
        
        total_operations = iterations * len(test_prices)
        avg_time = total_time / total_operations
        success_rate = (success_count / total_operations) * 100
        
        print(f"✅ ScrapingUtils 平均响应时间: {avg_time*1000:.2f}ms")
        print(f"✅ 数据提取成功率: {success_rate:.1f}%")
        
        self.performance_metrics['scraping_success_rate'].append(success_rate)
        
        # 性能断言
        self.assertGreater(success_rate, 95, "数据提取成功率应大于95%")
        self.assertLess(avg_time, 0.001, "平均响应时间应小于1ms")
    
    def test_price_validation_performance(self):
        """测试价格验证性能"""
        print("\n" + "="*80)
        print("🔍 测试价格验证性能")
        print("="*80)
        
        scraping_utils = ScrapingUtils(self.logger)
        
        test_cases = [
            (14482.0, True),
            (0, False),
            (-100, False),
            (None, False),
            (999999, True)
        ]
        
        iterations = 1000
        total_time = 0
        success_count = 0
        
        for _ in range(iterations):
            for price, expected in test_cases:
                start_time = time.time()
                try:
                    result = scraping_utils.validate_price(price)
                    if result == expected:
                        success_count += 1
                    elapsed = time.time() - start_time
                    total_time += elapsed
                except Exception as e:
                    self.logger.warning(f"价格验证失败: {e}")
        
        total_operations = iterations * len(test_cases)
        avg_time = total_time / total_operations
        success_rate = (success_count / total_operations) * 100
        
        print(f"✅ 价格验证平均响应时间: {avg_time*1000:.2f}ms")
        print(f"✅ 验证准确率: {success_rate:.1f}%")
        
        # 性能断言
        self.assertEqual(success_rate, 100, "价格验证准确率应为100%")
        self.assertLess(avg_time, 0.0001, "平均响应时间应小于0.1ms")
    
    def test_text_cleaning_performance(self):
        """测试文本清理性能"""
        print("\n" + "="*80)
        print("🔍 测试文本清理性能")
        print("="*80)
        
        scraping_utils = ScrapingUtils(self.logger)
        
        test_texts = [
            "  Счастливый магазин  ",
            "\n\nGood and excellent 12\n",
            "\t\tNEW Воспоминания\t\t",
            "   Original   quality   store   ",
            None
        ]
        
        iterations = 1000
        total_time = 0
        
        for _ in range(iterations):
            for text in test_texts:
                start_time = time.time()
                try:
                    cleaned = scraping_utils.clean_text(text)
                    elapsed = time.time() - start_time
                    total_time += elapsed
                except Exception as e:
                    self.logger.warning(f"文本清理失败: {e}")
        
        total_operations = iterations * len(test_texts)
        avg_time = total_time / total_operations
        
        print(f"✅ 文本清理平均响应时间: {avg_time*1000:.2f}ms")
        
        # 性能断言
        self.assertLess(avg_time, 0.0001, "平均响应时间应小于0.1ms")
    
    def tearDown(self):
        """测试清理并输出性能报告"""
        super().tearDown()
        self._print_performance_report()
    
    def _print_performance_report(self):
        """输出性能报告"""
        print("\n" + "="*80)
        print("📊 性能测试报告")
        print("="*80)
        
        if self.performance_metrics['wait_utils']:
            avg_wait = sum(self.performance_metrics['wait_utils']) / len(self.performance_metrics['wait_utils'])
            print(f"⏱️  WaitUtils 平均响应时间: {avg_wait*1000:.2f}ms")
        
        if self.performance_metrics['scraping_utils']:
            avg_scrape = sum(self.performance_metrics['scraping_utils']) / len(self.performance_metrics['scraping_utils'])
            print(f"⏱️  ScrapingUtils 平均响应时间: {avg_scrape*1000:.2f}ms")
        
        if self.performance_metrics['timing_success_rate']:
            avg_timing_success = sum(self.performance_metrics['timing_success_rate']) / len(self.performance_metrics['timing_success_rate'])
            print(f"✅ 时序控制成功率: {avg_timing_success:.1f}%")
        
        if self.performance_metrics['scraping_success_rate']:
            avg_scraping_success = sum(self.performance_metrics['scraping_success_rate']) / len(self.performance_metrics['scraping_success_rate'])
            print(f"✅ 数据抓取成功率: {avg_scraping_success:.1f}%")
        
        print("="*80)


def main():
    """主函数"""
    print("🚀 开始性能基准测试")
    print("="*80)
    
    # 运行测试
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformanceBenchmark)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回退出码
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
