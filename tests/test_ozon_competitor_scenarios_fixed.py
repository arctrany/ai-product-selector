#!/usr/bin/env python3
"""
OZON跟卖功能场景测试 - 标准测试版

测试三种场景：
1. 没有跟卖店铺的商品 - 直接返回
2. 有跟卖店铺的商品 - 点击浮层获取跟卖店铺列表
3. 有跟卖店铺的商品，跟卖店铺超过10个 - 点击浮层获取更多跟卖店铺列表

使用标准的unittest框架进行测试
"""

import asyncio
import sys
from pathlib import Path
import unittest
import logging
import nest_asyncio

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.scrapers.ozon_scraper import OzonScraper
from common.config import get_config

# 配置测试日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 🔧 修复异步事件循环冲突问题
nest_asyncio.apply()

class TestOzonCompetitorScenarios(unittest.TestCase):
    """测试OZON跟卖功能场景 - 标准测试版"""

    def setUp(self):
        """测试初始化"""
        self.config = get_config()
        self.scraper = OzonScraper(self.config)
        
        # 设置测试用例数据
        self.test_cases = {
            'no_competitors': {
                'name': '场景1 - 无跟卖店铺',
                'url': 'https://www.ozon.ru/product/1756017628',
                'description': '测试没有跟卖店铺的商品',
                'expected_competitor_count': 0,
                'has_competitors': False
            },
            'with_competitors': {
                'name': '场景2 - 有跟卖店铺',
                'url': 'https://www.ozon.ru/product/144042159',
                'description': '测试有跟卖店铺的商品',
                'has_competitors': True
            },
            'many_competitors': {
                'name': '场景3 - 跟卖店铺超过10个',
                'url': 'https://www.ozon.ru/product/2369901364',
                'description': '测试有跟卖店铺的商品，跟卖店铺超过10个',
                'expected_min_competitors': 10,
                'has_competitors': True
            }
        }

    def tearDown(self):
        """测试清理"""
        if hasattr(self, 'scraper'):
            self.scraper.close()

    def test_browser_functionality(self):
        """测试浏览器基本功能"""
        async def run_test():
            logging.info("🔧 开始浏览器功能测试")
            
            test_url = "https://www.ozon.ru/product/1756017628"
            
            # 使用浏览器服务直接测试
            async def simple_test(browser_service):
                try:
                    result = await browser_service.navigate_to(test_url)
                    if result:
                        page_content = await browser_service.get_page_content()
                        if not isinstance(page_content, str):
                            page_content = str(page_content)
                        
                        # 从页面内容中提取标题
                        import re
                        title_match = re.search(r'<title>(.*?)</title>', page_content)
                        title = title_match.group(1) if title_match else "未知标题"
                        
                        return {"success": True, "title": title}
                    else:
                        return {"success": False, "error": "页面导航失败"}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            result = self.scraper.browser_service.scrape_page_data(test_url, simple_test)
            
            # 使用标准的unittest断言
            self.assertTrue(result.success, f"浏览器功能测试失败: {result.error_message if not result.success else ''}")
            logging.info("✅ 浏览器功能测试通过")
        
        asyncio.run(run_test())

    def test_scenario_1_no_competitors(self):
        """
        场景1：测试没有跟卖店铺的商品
        URL: https://www.ozon.ru/product/1756017628
        """
        async def run_test():
            test_case = self.test_cases['no_competitors']
            logging.info(f"🧪 开始{test_case['name']}测试")
            
            url = test_case['url']
            
            # 测试价格信息抓取
            price_result = self.scraper.scrape_product_prices(url)

            # 断言价格抓取成功
            self.assertTrue(price_result.success, f"价格信息抓取失败: {price_result.error_message}")

            # 验证价格数据结构
            self.assertIsInstance(price_result.data, dict, "价格数据应该是字典类型")

            # 检查关键数据字段
            price_data = price_result.data
            self.assertIn('green_price', price_data, "价格数据应包含绿标价格字段")
            self.assertIn('black_price', price_data, "价格数据应包含黑标价格字段")

            # 记录价格信息
            green_price = price_data.get('green_price')
            black_price = price_data.get('black_price')
            logging.info(f"💰 绿标价格: {green_price}₽, 黑标价格: {black_price}₽")

            # 测试跟卖店铺抓取
            competitor_result = self.scraper.scrape_competitor_stores(url, max_competitors=10)

            # 断言跟卖店铺抓取成功
            self.assertTrue(competitor_result.success, f"跟卖店铺抓取失败: {competitor_result.error_message}")

            # 验证跟卖店铺数据结构
            self.assertIsInstance(competitor_result.data, dict, "跟卖店铺数据应该是字典类型")

            competitors_data = competitor_result.data
            self.assertIn('competitors', competitors_data, "跟卖店铺数据应包含competitors字段")
            self.assertIn('total_count', competitors_data, "跟卖店铺数据应包含total_count字段")

            competitors = competitors_data.get('competitors', [])
            total_count = competitors_data.get('total_count', 0)

            # 验证跟卖店铺数量符合预期（无跟卖店铺场景）
            self.assertEqual(total_count, test_case['expected_competitor_count'],
                            f"预期无跟卖店铺，但发现{total_count}个跟卖店铺")

            logging.info(f"✅ {test_case['name']}测试通过 - 跟卖店铺数量: {total_count}")

        asyncio.run(run_test())

    def test_scenario_2_with_competitors(self):
        """
        场景2：测试有跟卖店铺的商品
        URL: https://www.ozon.ru/product/144042159
        """
        async def run_test():
            test_case = self.test_cases['with_competitors']
            logging.info(f"🧪 开始{test_case['name']}测试")

            url = test_case['url']

            # 测试价格信息抓取
            price_result = self.scraper.scrape_product_prices(url)

            # 断言价格抓取成功
            self.assertTrue(price_result.success, f"价格信息抓取失败: {price_result.error_message}")

            # 验证价格数据
            price_data = price_result.data
            self.assertIsInstance(price_data, dict, "价格数据应该是字典类型")

            # 记录价格信息
            green_price = price_data.get('green_price')
            black_price = price_data.get('black_price')
            competitor_count = price_data.get('competitor_count')

            logging.info(f"💰 绿标价格: {green_price}₽, 黑标价格: {black_price}₽")
            logging.info(f"📊 页面显示跟卖数量: {competitor_count}")

            # 测试跟卖店铺抓取
            competitor_result = self.scraper.scrape_competitor_stores(url, max_competitors=10)

            # 断言跟卖店铺抓取成功
            self.assertTrue(competitor_result.success, f"跟卖店铺抓取失败: {competitor_result.error_message}")

            # 验证跟卖店铺数据
            competitors_data = competitor_result.data
            competitors = competitors_data.get('competitors', [])
            total_count = competitors_data.get('total_count', 0)

            # 验证有跟卖店铺
            self.assertGreater(total_count, 0, "预期有跟卖店铺，但未找到任何跟卖店铺")

            # 验证跟卖店铺数据结构
            if competitors:
                first_competitor = competitors[0]
                self.assertIn('store_name', first_competitor, "跟卖店铺数据应包含店铺名称")
                self.assertIn('price', first_competitor, "跟卖店铺数据应包含价格")

                # 记录跟卖店铺信息
                logging.info(f"📋 找到{total_count}个跟卖店铺:")
                for i, comp in enumerate(competitors[:3], 1):
                    store_name = comp.get('store_name', 'N/A')
                    price = comp.get('price', 'N/A')
                    store_id = comp.get('store_id', 'N/A')
                    logging.info(f"   {i}. {store_name} - {price}₽ (ID: {store_id})")

            logging.info(f"✅ {test_case['name']}测试通过 - 跟卖店铺数量: {total_count}")

        asyncio.run(run_test())

    def test_scenario_3_with_many_competitors(self):
        """
        场景3：测试有跟卖店铺的商品，跟卖店铺超过10个
        URL: https://www.ozon.ru/product/2369901364
        """
        async def run_test():
            test_case = self.test_cases['many_competitors']
            logging.info(f"🧪 开始{test_case['name']}测试")

            url = test_case['url']

            # 测试价格信息抓取
            price_result = self.scraper.scrape_product_prices(url)

            # 断言价格抓取成功
            self.assertTrue(price_result.success, f"价格信息抓取失败: {price_result.error_message}")

            # 记录价格信息
            price_data = price_result.data
            green_price = price_data.get('green_price')
            black_price = price_data.get('black_price')
            competitor_count = price_data.get('competitor_count')

            logging.info(f"💰 绿标价格: {green_price}₽, 黑标价格: {black_price}₽")
            logging.info(f"📊 页面显示跟卖数量: {competitor_count}")

            # 测试跟卖店铺抓取，获取更多店铺
            competitor_result = self.scraper.scrape_competitor_stores(url, max_competitors=15)

            # 断言跟卖店铺抓取成功
            self.assertTrue(competitor_result.success, f"跟卖店铺抓取失败: {competitor_result.error_message}")

            # 验证跟卖店铺数据
            competitors_data = competitor_result.data
            competitors = competitors_data.get('competitors', [])
            total_count = competitors_data.get('total_count', 0)

            # 验证跟卖店铺数量符合预期（超过10个）
            expected_min = test_case.get('expected_min_competitors', 10)
            self.assertGreaterEqual(total_count, expected_min,
                                   f"预期至少{expected_min}个跟卖店铺，但只找到{total_count}个")

            # 记录跟卖店铺信息
            if competitors:
                logging.info(f"📋 找到{total_count}个跟卖店铺:")
                for i, comp in enumerate(competitors[:5], 1):  # 显示前5个
                    store_name = comp.get('store_name', 'N/A')
                    price = comp.get('price', 'N/A')
                    store_id = comp.get('store_id', 'N/A')
                    logging.info(f"   {i}. {store_name} - {price}₽ (ID: {store_id})")

            logging.info(f"✅ {test_case['name']}测试通过 - 跟卖店铺数量: {total_count}")

        asyncio.run(run_test())

    def test_price_data_validation(self):
        """测试价格数据验证"""
        async def run_test():
            logging.info("🧪 开始价格数据验证测试")

            # 使用第一个测试用例进行价格数据验证
            url = self.test_cases['no_competitors']['url']

            price_result = self.scraper.scrape_product_prices(url)
            self.assertTrue(price_result.success, "价格抓取应该成功")
            
            price_data = price_result.data
            
            # 验证价格数据类型
            green_price = price_data.get('green_price')
            black_price = price_data.get('black_price')
            
            if green_price is not None:
                self.assertIsInstance(green_price, (int, float), "绿标价格应该是数字类型")
                self.assertGreater(green_price, 0, "绿标价格应该大于0")
            
            if black_price is not None:
                self.assertIsInstance(black_price, (int, float), "黑标价格应该是数字类型")
                self.assertGreater(black_price, 0, "黑标价格应该大于0")
            
            # 验证图片URL
            image_url = price_data.get('image_url')
            if image_url:
                self.assertIsInstance(image_url, str, "图片URL应该是字符串类型")
                self.assertTrue(image_url.startswith('http'), "图片URL应该是有效的HTTP链接")
            
            logging.info("✅ 价格数据验证测试通过")
        
        asyncio.run(run_test())

    def test_competitor_data_validation(self):
        """测试跟卖店铺数据验证"""
        async def run_test():
            logging.info("🧪 开始跟卖店铺数据验证测试")
            
            # 使用有跟卖店铺的测试用例
            url = self.test_cases['with_competitors']['url']
            
            competitor_result = self.scraper.scrape_competitor_stores(url, max_competitors=5)
            self.assertTrue(competitor_result.success, "跟卖店铺抓取应该成功")
            
            competitors_data = competitor_result.data
            competitors = competitors_data.get('competitors', [])
            total_count = competitors_data.get('total_count', 0)
            
            # 验证总数类型
            self.assertIsInstance(total_count, int, "跟卖店铺总数应该是整数类型")
            self.assertGreaterEqual(total_count, 0, "跟卖店铺总数应该大于等于0")
            
            # 验证跟卖店铺列表
            self.assertIsInstance(competitors, list, "跟卖店铺列表应该是列表类型")
            
            # 如果有跟卖店铺，验证数据结构
            if competitors:
                for competitor in competitors:
                    self.assertIsInstance(competitor, dict, "每个跟卖店铺应该是字典类型")
                    
                    # 验证必要字段
                    self.assertIn('store_name', competitor, "跟卖店铺应包含店铺名称")
                    self.assertIn('price', competitor, "跟卖店铺应包含价格")
                    
                    # 验证价格类型
                    price = competitor.get('price')
                    if price is not None and price != 'N/A':
                        self.assertIsInstance(price, (int, float, str), "跟卖店铺价格应该是数字或字符串类型")
            
            logging.info("✅ 跟卖店铺数据验证测试通过")
        
        asyncio.run(run_test())

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
