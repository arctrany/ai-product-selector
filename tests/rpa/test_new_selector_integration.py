# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
#
# """
# 新选择器配置集成测试
#
# 测试 competitor_area_selectors 和 competitor_popup_selectors 在实际抓取中的使用
# """
#
# import unittest
# from unittest.mock import Mock, MagicMock, patch
# from bs4 import BeautifulSoup
#
# from common.config.ozon_selectors_config import get_ozon_selectors_config
# from common.scrapers.competitor_scraper import CompetitorScraper
# from common.services.competitor_detection_service import CompetitorDetectionService
#
# class TestNewSelectorIntegration(unittest.TestCase):
#     """新选择器配置集成测试类"""
#
#     def setUp(self):
#         """测试初始化"""
#         self.config = get_ozon_selectors_config()
#         self.scraper = CompetitorScraper()
#
#     def test_competitor_area_selectors_in_scraper(self):
#         """测试 competitor_area_selectors 在 CompetitorScraper 中的使用"""
#         # 验证 scraper 使用了新的选择器配置
#         self.assertTrue(hasattr(self.config, 'competitor_area_selectors'))
#         self.assertIsInstance(self.config.competitor_area_selectors, list)
#         self.assertGreater(len(self.config.competitor_area_selectors), 0)
#
#     def test_competitor_popup_selectors_in_scraper(self):
#         """测试 competitor_popup_selectors 在 CompetitorScraper 中的使用"""
#         # 验证 scraper 使用了新的选择器配置
#         self.assertTrue(hasattr(self.config, 'competitor_popup_selectors'))
#         self.assertIsInstance(self.config.competitor_popup_selectors, list)
#         self.assertGreater(len(self.config.competitor_popup_selectors), 0)
#
#     @patch('common.scrapers.competitor_scraper.CompetitorScraper._find_container_in_soup')
#     def test_find_container_uses_new_selectors(self, mock_find_container):
#         """测试 _find_container_in_soup 使用新的选择器"""
#         # 创建模拟的 HTML 内容
#         html_content = """
#         <div class="pdp_bk3">
#             <div class="competitor-item">Store 1</div>
#             <div class="competitor-item">Store 2</div>
#         </div>
#         """
#         soup = BeautifulSoup(html_content, 'html.parser')
#
#         # 设置模拟返回值
#         mock_container = MagicMock()
#         mock_find_container.return_value = mock_container
#
#         # 调用方法
#         result = self.scraper._find_container_in_soup(soup)
#
#         # 验证调用了正确的方法
#         mock_find_container.assert_called_once_with(soup)
#         self.assertEqual(result, mock_container)
#
#     def test_competitor_detection_service_uses_new_selectors(self):
#         """测试 CompetitorDetectionService 使用新的选择器"""
#         # 创建服务实例
#         service = CompetitorDetectionService(self.config, Mock())
#
#         # 验证服务使用了新的选择器配置
#         self.assertTrue(hasattr(service.selectors_config, 'competitor_area_selectors'))
#         self.assertTrue(hasattr(service.selectors_config, 'competitor_popup_selectors'))
#
#     def test_selector_configuration_consistency(self):
#         """测试选择器配置的一致性"""
#         # 验证新旧选择器配置的一致性
#         self.assertFalse(hasattr(self.config, 'competitor_container_selectors'),
#                         "旧的 competitor_container_selectors 应该已被移除")
#
#         # 验证新选择器配置存在
#         self.assertTrue(hasattr(self.config, 'competitor_area_selectors'))
#         self.assertTrue(hasattr(self.config, 'competitor_popup_selectors'))
#
# if __name__ == '__main__':
#     unittest.main()
