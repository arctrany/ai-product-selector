#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OZON 选择器配置测试

测试新增的 competitor_area_selectors 和 competitor_popup_selectors 配置
"""

import unittest
from common.config.ozon_selectors_config import get_ozon_selectors_config

class TestOzonSelectorsConfig(unittest.TestCase):
    """OZON 选择器配置测试类"""

    def setUp(self):
        """测试初始化"""
        self.config = get_ozon_selectors_config()

    def test_competitor_area_selectors_exist(self):
        """测试 competitor_area_selectors 配置存在"""
        # 验证配置项存在
        self.assertTrue(hasattr(self.config, 'competitor_area_selectors'))
        # 验证配置项不为空
        self.assertIsInstance(self.config.competitor_area_selectors, list)
        self.assertGreater(len(self.config.competitor_area_selectors), 0)
        # 验证配置项包含预期的选择器
        expected_selectors = [
            "div.pdp_bk3",
            "div.pdp_kb2",
            "[data-widget='webSellerList']",
            "[class*='competitor']",
            "#seller-list"
        ]
        for selector in expected_selectors:
            self.assertIn(selector, self.config.competitor_area_selectors)

    def test_competitor_popup_selectors_exist(self):
        """测试 competitor_popup_selectors 配置存在"""
        # 验证配置项存在
        self.assertTrue(hasattr(self.config, 'competitor_popup_selectors'))
        # 验证配置项不为空
        self.assertIsInstance(self.config.competitor_popup_selectors, list)
        self.assertGreater(len(self.config.competitor_popup_selectors), 0)
        # 验证配置项包含预期的选择器
        expected_selectors = [
            "#seller-list",
            "div.pdp_b2k",
            "h3.pdp_kb2",
            "div.pdp_k2b",
            "div.pdp_bk3"
        ]
        for selector in expected_selectors:
            self.assertIn(selector, self.config.competitor_popup_selectors)

    def test_old_competitor_container_selectors_removed(self):
        """测试旧的 competitor_container_selectors 配置已被移除"""
        # 验证旧配置项不存在
        self.assertFalse(hasattr(self.config, 'competitor_container_selectors'))

    def test_selector_configuration_validity(self):
        """测试选择器配置的有效性"""
        # 验证所有选择器都是字符串
        all_selectors = (
            self.config.competitor_area_selectors + 
            self.config.competitor_popup_selectors
        )
        
        for selector in all_selectors:
            self.assertIsInstance(selector, str)
            self.assertGreater(len(selector.strip()), 0)

    def test_selector_uniqueness(self):
        """测试选择器配置的唯一性"""
        # 验证 competitor_area_selectors 中没有重复项
        area_selectors = self.config.competitor_area_selectors
        self.assertEqual(len(area_selectors), len(set(area_selectors)))
        
        # 验证 competitor_popup_selectors 中没有重复项
        popup_selectors = self.config.competitor_popup_selectors
        self.assertEqual(len(popup_selectors), len(set(popup_selectors)))

if __name__ == '__main__':
    unittest.main()
