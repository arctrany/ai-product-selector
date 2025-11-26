#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OZON Scraper 递归功能单元测试

测试新增的跟卖商品详情递归抓取功能，包括：
- _extract_product_id() URL解析
- _click_first_competitor() 浏览器交互
- scrape() 递归逻辑
- 递归深度限制
- 错误处理和降级策略
"""

import sys
import unittest
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from unittest.mock import Mock, MagicMock, patch

from common.config.base_config import get_config
from common.scrapers.ozon_scraper import OzonScraper
from common.models.scraping_models import ScrapingResult

class TestOzonScraperRecursiveFeatures(unittest.TestCase):
    """OZON Scraper 递归功能测试类"""

    def setUp(self):
        """测试初始化"""
        self.config = get_config()
        self.scraper = None

    def tearDown(self):
        """测试清理"""
        if self.scraper:
            # 不调用 close() 因为我们用的是 Mock
            self.scraper = None

    def _create_mock_scraper(self) -> OzonScraper:
        """创建 Mock 版本的 OzonScraper"""
        with patch('common.scrapers.ozon_scraper.get_global_browser_service'):
            scraper = OzonScraper(self.config)
            # Mock browser_service 避免真实浏览器交互
            scraper.browser_service = MagicMock()
            return scraper

    # ===== _extract_product_id() 测试 =====

    def test_extract_product_id_standard_format(self):
        """测试标准格式URL的商品ID提取: /product/xxx-1234567/"""
        scraper = self._create_mock_scraper()

        test_cases = [
            ("https://www.ozon.ru/product/telefon-apple-iphone-15-128gb-1234567/", "1234567"),
            ("https://www.ozon.ru/product/xiaomi-redmi-note-12-4-128gb-9876543/", "9876543"),
            ("https://www.ozon.ru/product/single-word-1111111/", "1111111"),
            ("https://www.ozon.ru/product/multiple-hyphen-words-here-5555555/", "5555555"),
        ]

        for url, expected_id in test_cases:
            with self.subTest(url=url):
                actual_id = scraper._extract_product_id(url)
                self.assertEqual(actual_id, expected_id,
                               f"URL {url} 应该提取出ID {expected_id}，实际得到 {actual_id}")

    def test_extract_product_id_seller_format(self):
        """测试卖家格式URL的商品ID提取: /seller/xxx/product/1234567/"""
        scraper = self._create_mock_scraper()

        test_cases = [
            ("https://www.ozon.ru/seller/official-apple/product/1234567/", "1234567"),
            ("https://www.ozon.ru/seller/xiaomi-store/product/9876543/", "9876543"),
        ]

        for url, expected_id in test_cases:
            with self.subTest(url=url):
                actual_id = scraper._extract_product_id(url)
                self.assertEqual(actual_id, expected_id,
                               f"URL {url} 应该提取出ID {expected_id}，实际得到 {actual_id}")

    def test_extract_product_id_invalid_urls(self):
        """测试无效URL的处理"""
        scraper = self._create_mock_scraper()

        invalid_urls = [
            "https://www.ozon.ru/",
            "https://www.ozon.ru/category/telefony/",
            "https://www.ozon.ru/product/",
            "https://www.ozon.ru/product/no-id-here/",
            "https://invalid-domain.com/product/test-123456/",
            "",
            None,
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                if url is None:
                    # 测试None输入时的异常处理
                    with self.assertRaises(Exception):
                        scraper._extract_product_id(url)
                else:
                    actual_id = scraper._extract_product_id(url)
                    self.assertIsNone(actual_id,
                                    f"无效URL {url} 应该返回None，实际得到 {actual_id}")

    def test_extract_product_id_edge_cases(self):
        """测试边界情况"""
        scraper = self._create_mock_scraper()

        edge_cases = [
            # 只有数字的商品名
            ("https://www.ozon.ru/product/123-456789/", "456789"),
            # 很长的商品ID
            ("https://www.ozon.ru/product/test-12345678901234567890/", "12345678901234567890"),
            # URL中有其他数字干扰
            ("https://www.ozon.ru/product/iphone-15-pro-max-1tb-1234567/?from_sku=98765", "1234567"),
        ]

        for url, expected_id in edge_cases:
            with self.subTest(url=url):
                actual_id = scraper._extract_product_id(url)
                self.assertEqual(actual_id, expected_id,
                               f"边界情况URL {url} 应该提取出ID {expected_id}，实际得到 {actual_id}")

    # ===== _click_first_competitor() 测试 =====

    @patch('time.sleep')  # Mock sleep 以加速测试
    def test_click_first_competitor_success(self, mock_sleep):
        """测试成功点击第一个跟卖店铺"""
        scraper = self._create_mock_scraper()

        # Mock 页面和元素
        mock_page = MagicMock()
        mock_card_locator = MagicMock()
        mock_first_card = MagicMock()
        mock_clickable_locator = MagicMock()
        mock_clickable_element = MagicMock()

        # 设置 browser_service.get_page() 返回 mock_page
        scraper.browser_service.get_page.return_value = mock_page

        # 设置页面locator行为 - 第一个选择器找到卡片
        # 使用配置系统中的选择器
        mock_page.locator.side_effect = [
            mock_card_locator,  # 使用配置的容器选择器
            mock_clickable_locator,  # 使用配置的价格选择器
        ]

        # 设置卡片定位成功
        mock_card_locator.count.return_value = 1
        mock_card_locator.first = mock_first_card

        # 设置可点击元素定位成功
        mock_first_card.locator.return_value = mock_clickable_locator
        mock_clickable_locator.count.return_value = 1
        mock_clickable_locator.first = mock_clickable_element

        # 设置URL跳转
        mock_page.url = "https://www.ozon.ru/product/original-1234567/"
        mock_page.url = "https://www.ozon.ru/product/competitor-9876543/"  # 跳转后

        # 执行测试
        new_url, product_id = scraper._click_first_competitor()

        # 验证结果
        self.assertEqual(new_url, "https://www.ozon.ru/product/competitor-9876543/")
        self.assertEqual(product_id, "9876543")

        # 验证调用了正确的方法
        scraper.browser_service.get_page.assert_called_once()
        mock_page.locator.assert_called()
        mock_clickable_element.scroll_into_view_if_needed.assert_called_once()
        mock_clickable_element.click.assert_called_once()

    @patch('time.sleep')
    def test_click_first_competitor_no_cards_found(self, mock_sleep):
        """测试未找到跟卖卡片的情况"""
        scraper = self._create_mock_scraper()

        mock_page = MagicMock()
        scraper.browser_service.get_page.return_value = mock_page

        # 模拟所有选择器都找不到卡片
        mock_empty_locator = MagicMock()
        mock_empty_locator.count.return_value = 0
        mock_page.locator.return_value = mock_empty_locator

        # 执行测试，应该抛出异常
        with self.assertRaises(Exception) as context:
            scraper._click_first_competitor()

        self.assertIn("未找到跟卖店铺卡片", str(context.exception))

    @patch('time.sleep')
    def test_click_first_competitor_no_clickable_area(self, mock_sleep):
        """测试找到卡片但无安全点击区域的情况"""
        scraper = self._create_mock_scraper()

        mock_page = MagicMock()
        scraper.browser_service.get_page.return_value = mock_page

        # 模拟找到卡片
        mock_card_locator = MagicMock()
        mock_first_card = MagicMock()
        mock_card_locator.count.return_value = 1
        mock_card_locator.first = mock_first_card

        # 模拟找不到安全点击区域
        mock_empty_clickable = MagicMock()
        mock_empty_clickable.count.return_value = 0
        mock_first_card.locator.return_value = mock_empty_clickable

        mock_page.locator.return_value = mock_card_locator

        # 执行测试，应该抛出异常
        with self.assertRaises(Exception) as context:
            scraper._click_first_competitor()

        self.assertIn("未找到安全的可点击区域", str(context.exception))

    @patch('time.sleep')
    def test_click_first_competitor_page_not_changed(self, mock_sleep):
        """测试页面未跳转的情况"""
        scraper = self._create_mock_scraper()

        mock_page = MagicMock()
        scraper.browser_service.get_page.return_value = mock_page

        # 模拟找到卡片和可点击元素
        self._setup_successful_click_mocks(scraper, mock_page)

        # 模拟页面未跳转（URL保持不变）
        original_url = "https://www.ozon.ru/product/original-1234567/"
        mock_page.url = original_url  # 保持不变

        # 执行测试，应该抛出异常
        with self.assertRaises(Exception) as context:
            scraper._click_first_competitor()

        self.assertIn("页面未跳转", str(context.exception))

    def _setup_successful_click_mocks(self, scraper, mock_page):
        """设置成功点击所需的 Mock 对象"""
        mock_card_locator = MagicMock()
        mock_first_card = MagicMock()
        mock_clickable_locator = MagicMock()
        mock_clickable_element = MagicMock()

        mock_page.locator.return_value = mock_card_locator
        mock_card_locator.count.return_value = 1
        mock_card_locator.first = mock_first_card

        mock_first_card.locator.return_value = mock_clickable_locator
        mock_clickable_locator.count.return_value = 1
        mock_clickable_locator.first = mock_clickable_element

    # ===== scrape() 递归逻辑测试 =====

    def test_scrape_recursion_depth_limit(self):
        """测试递归深度限制"""
        scraper = self._create_mock_scraper()

        url = "https://www.ozon.ru/product/test-1234567/"

        # 测试递归深度为0时正常工作
        with patch.object(scraper, 'scrape_product_basics') as mock_price:
            mock_price.return_value = ScrapingResult(success=True, data={})
            result = scraper.scrape(url, _recursion_depth=0)
            self.assertTrue(result.success)

        # 测试递归深度为1时正常工作
        with patch.object(scraper, 'scrape_product_basics') as mock_price:
            mock_price.return_value = ScrapingResult(success=True, data={})
            result = scraper.scrape(url, _recursion_depth=1)
            self.assertTrue(result.success)

        # 测试递归深度超限时被拒绝
        result = scraper.scrape(url, _recursion_depth=2)
        self.assertFalse(result.success)
        self.assertIn("递归深度超限", result.error_message)

    @patch.object(OzonScraper, '_click_first_competitor')
    @patch.object(OzonScraper, 'scrape_competitor_stores')
    def test_scrape_recursive_call_conditions(self, mock_competitor_stores, mock_click):
        """测试递归调用的触发条件"""
        scraper = self._create_mock_scraper()

        # Mock 基础方法返回
        with patch.object(scraper, 'scrape_product_basics') as mock_price, \
             patch.object(scraper, 'scrape_erp_info') as mock_erp, \
             patch.object(scraper, 'profit_evaluator') as mock_evaluator:

            # 设置基础返回值
            mock_price.return_value = ScrapingResult(success=True, data={'test': 'data'})
            mock_erp.return_value = ScrapingResult(success=True, data={})

            # 测试条件1：include_competitors=True, has_better_price=True 时触发递归
            mock_evaluator.has_better_competitor_price.return_value = True
            mock_competitor_stores.return_value = ScrapingResult(
                success=True,
                data={'competitors': [], 'total_count': 0}
            )
            mock_click.return_value = ("https://www.ozon.ru/product/new-999999/", "999999")

            # Mock 递归调用的 scrape 返回
            with patch.object(scraper, 'scrape', wraps=scraper.scrape) as mock_scrape:
                def side_effect(*args, **kwargs):
                    if kwargs.get('_recursion_depth', 0) > 0:
                        return ScrapingResult(success=True, data={'recursive': 'data'})
                    return scraper.scrape(*args, **kwargs)
                mock_scrape.side_effect = side_effect

                result = scraper.scrape(
                    "https://www.ozon.ru/product/test-1234567/",
                    include_competitors=True,
                    _recursion_depth=0,
                    _fetch_competitor_details=True
                )

                self.assertTrue(result.success)
                # 验证递归调用被触发
                mock_click.assert_called_once()

    @patch.object(OzonScraper, '_click_first_competitor')
    def test_scrape_recursive_call_parameters(self, mock_click):
        """测试递归调用参数正确性"""
        scraper = self._create_mock_scraper()

        # Mock 基础方法
        with patch.object(scraper, 'scrape_product_basics') as mock_price, \
             patch.object(scraper, 'scrape_erp_info') as mock_erp, \
             patch.object(scraper, 'scrape_competitor_stores') as mock_competitor, \
             patch.object(scraper, 'profit_evaluator') as mock_evaluator:

            mock_price.return_value = ScrapingResult(success=True, data={})
            mock_erp.return_value = ScrapingResult(success=True, data={})
            mock_evaluator.has_better_competitor_price.return_value = True
            mock_competitor.return_value = ScrapingResult(
                success=True, data={'competitors': [], 'total_count': 0}
            )
            mock_click.return_value = ("https://www.ozon.ru/product/competitor-999999/", "999999")

            # 使用真实的 scrape 方法进行递归调用测试
            with patch.object(scraper, 'scrape', wraps=scraper.scrape) as mock_scrape:
                # 设置递归调用的返回值
                def scrape_side_effect(url, include_competitors=False, _recursion_depth=0, _fetch_competitor_details=True, **kwargs):
                    if _recursion_depth > 0:
                        # 模拟递归调用的返回
                        return ScrapingResult(success=True, data={
                            'product_url': url,
                            'product_id': "999999",
                            'price_data': {},
                            'erp_data': {},
                            'competitors': [],
                            'competitor_count': 0
                        })
                    else:
                        # 原始调用，继续执行
                        return scraper.scrape.__wrapped__(scraper, url, include_competitors, _recursion_depth, _fetch_competitor_details, **kwargs)

                mock_scrape.side_effect = scrape_side_effect

                result = scraper.scrape(
                    "https://www.ozon.ru/product/original-1234567/",
                    include_competitors=True
                )

                self.assertTrue(result.success)

                # 验证递归调用参数
                recursive_calls = [call for call in mock_scrape.call_args_list
                                 if call.kwargs.get('_recursion_depth', 0) > 0]

                if recursive_calls:
                    recursive_call = recursive_calls[0]
                    # 验证递归调用参数
                    self.assertEqual(recursive_call.args[0], "https://www.ozon.ru/product/competitor-999999/")
                    self.assertEqual(recursive_call.kwargs['include_competitors'], False)
                    self.assertEqual(recursive_call.kwargs['_fetch_competitor_details'], False)
                    self.assertEqual(recursive_call.kwargs['_recursion_depth'], 1)

    # ===== 错误处理和降级策略测试 =====

    @patch.object(OzonScraper, '_click_first_competitor')
    def test_scrape_recursive_error_handling(self, mock_click):
        """测试递归抓取错误处理"""
        scraper = self._create_mock_scraper()

        # Mock 基础方法正常工作
        with patch.object(scraper, 'scrape_product_basics') as mock_price, \
             patch.object(scraper, 'scrape_erp_info') as mock_erp, \
             patch.object(scraper, 'scrape_competitor_stores') as mock_competitor, \
             patch.object(scraper, 'profit_evaluator') as mock_evaluator:

            mock_price.return_value = ScrapingResult(success=True, data={})
            mock_erp.return_value = ScrapingResult(success=True, data={})
            mock_evaluator.has_better_competitor_price.return_value = True
            mock_competitor.return_value = ScrapingResult(
                success=True, data={'competitors': [], 'total_count': 0}
            )

            # 模拟点击失败
            mock_click.side_effect = Exception("点击失败")

            result = scraper.scrape(
                "https://www.ozon.ru/product/test-1234567/",
                include_competitors=True
            )

            # 错误不应该影响主流程，仍然返回成功
            self.assertTrue(result.success)
            self.assertNotIn('first_competitor_details', result.data)

    def test_scrape_conditions_not_met_for_recursion(self):
        """测试不满足递归条件时的行为"""
        scraper = self._create_mock_scraper()

        # Mock 基础方法
        with patch.object(scraper, 'scrape_product_basics') as mock_price, \
             patch.object(scraper, 'scrape_erp_info') as mock_erp, \
             patch.object(scraper, 'profit_evaluator') as mock_evaluator:

            mock_price.return_value = ScrapingResult(success=True, data={})
            mock_erp.return_value = ScrapingResult(success=True, data={})

            # 测试情况1：has_better_price=False
            mock_evaluator.has_better_competitor_price.return_value = False

            result = scraper.scrape(
                "https://www.ozon.ru/product/test-1234567/",
                include_competitors=True
            )

            self.assertTrue(result.success)
            self.assertNotIn('first_competitor_details', result.data)

            # 测试情况2：include_competitors=False
            result = scraper.scrape(
                "https://www.ozon.ru/product/test-1234567/",
                include_competitors=False
            )

            self.assertTrue(result.success)
            self.assertNotIn('first_competitor_details', result.data)

            # 测试情况3：_fetch_competitor_details=False
            mock_evaluator.has_better_competitor_price.return_value = True

            result = scraper.scrape(
                "https://www.ozon.ru/product/test-1234567/",
                include_competitors=True,
                _fetch_competitor_details=False
            )

            self.assertTrue(result.success)
            self.assertNotIn('first_competitor_details', result.data)

if __name__ == '__main__':
    unittest.main()
