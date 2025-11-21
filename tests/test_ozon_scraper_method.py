#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OZON Scraper scrape() 方法单独测试 - 同步版本

测试 OzonScraper.scrape() 方法的功能，使用JSON配置的测试用例
"""

import json
import os
import sys
import time
import unittest
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.config import get_config
from common.scrapers.ozon_scraper import OzonScraper


class OzonScraperMethodTester:
    """OzonScraper.scrape() 方法测试器"""

    def __init__(self):
        """初始化测试器"""
        self.config = get_config()
        self.scraper = None
        self.test_cases = []
        self.validation_rules = {}
        self._load_test_data()

    def _load_test_data(self):
        """加载测试数据"""
        try:
            test_data_path = Path(__file__).parent / "test_data" / "ozon_test_cases.json"
            
            if not test_data_path.exists():
                raise FileNotFoundError(f"测试数据文件不存在: {test_data_path}")
            
            with open(test_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.test_cases = data.get('test_cases', [])
            self.validation_rules = data.get('validation_rules', {})
            
            print(f"✅ 成功加载 {len(self.test_cases)} 个测试用例")
            
        except Exception as e:
            print(f"❌ 加载测试数据失败: {e}")
            raise

    def _setup_scraper(self):
        """初始化爬虫"""
        try:
            self.scraper = OzonScraper(self.config)
            print("✅ OzonScraper 初始化成功")
            return True
        except Exception as e:
            print(f"❌ OzonScraper 初始化失败: {e}")
            return False

    def _validate_price_data(self, actual_data: Dict[str, Any], expected: Dict[str, Any], test_case_id: str) -> bool:
        """验证价格数据"""
        print(f"\n🔍 验证价格数据 - {test_case_id}")
        
        price_data = actual_data.get('price_data', {})
        tolerance = self.validation_rules.get('price_tolerance', 50.0)
        
        # 验证必需字段（允许价格字段为空）
        required_fields = self.validation_rules.get('required_fields', [])
        for field in required_fields:
            if field not in price_data:
                print(f"❌ 缺少必需字段: {field}")
                return False
        
        # 验证绿标价格
        expected_green = expected.get('green_price')
        actual_green = price_data.get('green_price')
        
        if expected_green is not None:
            if actual_green is None:
                print(f"❌ 绿标价格验证失败: 期望 {expected_green}₽, 实际 None")
                return False
            elif abs(actual_green - expected_green) > tolerance:
                print(f"❌ 绿标价格验证失败: 期望 {expected_green}₽, 实际 {actual_green}₽ (误差超过 {tolerance}₽)")
                return False
            else:
                print(f"✅ 绿标价格验证通过: {actual_green}₽")
        else:
            if actual_green is not None:
                print(f"⚠️ 绿标价格意外存在: {actual_green}₽ (期望为空)")
            else:
                print(f"✅ 绿标价格验证通过: 无绿标价格")
        
        # 验证黑标价格
        expected_black = expected.get('black_price')
        actual_black = price_data.get('black_price')
        
        if expected_black is not None:
            if actual_black is None:
                print(f"❌ 黑标价格验证失败: 期望 {expected_black}₽, 实际 None")
                return False
            elif abs(actual_black - expected_black) > tolerance:
                print(f"❌ 黑标价格验证失败: 期望 {expected_black}₽, 实际 {actual_black}₽ (误差超过 {tolerance}₽)")
                return False
            else:
                print(f"✅ 黑标价格验证通过: {actual_black}₽")
        else:
            if actual_black is not None:
                print(f"⚠️ 黑标价格意外存在: {actual_black}₽ (期望为空)")
            else:
                print(f"✅ 黑标价格验证通过: 无黑标价格")
        
        # 验证图片URL
        image_url = price_data.get('image_url')
        has_image_expected = expected.get('has_image', True)
        
        if has_image_expected:
            if image_url:
                print(f"✅ 商品图片验证通过: {image_url}")
            else:
                print(f"❌ 商品图片验证失败: 期望有图片但未找到")
                return False
        else:
            if image_url:
                print(f"⚠️ 意外找到商品图片: {image_url}")
            else:
                print(f"✅ 商品图片验证通过: 无图片")
        
        # 判断是否有更优跟卖价格
        has_better_price = self._check_has_better_competitor_price(price_data)

        # 验证跟卖数量 - 只有当 has_better_price 为 True 时才验证
        expected_count = expected.get('competitor_count')
        actual_count = actual_data.get('competitor_count')  # 从根级别获取，不是从 price_data
        count_tolerance = self.validation_rules.get('competitor_count_tolerance', 5)

        if not has_better_price:
            print(f"ℹ️ 跟卖价格不优于主价格，跳过跟卖数量验证")
        elif expected_count is not None:
            if actual_count is None:
                print(f"❌ 跟卖数量验证失败: 期望 {expected_count}, 实际 None")
                return False
            elif abs(actual_count - expected_count) > count_tolerance:
                print(f"❌ 跟卖数量验证失败: 期望 {expected_count}, 实际 {actual_count} (误差超过 {count_tolerance})")
                return False
            else:
                print(f"✅ 跟卖数量验证通过: {actual_count}")
        else:
            print(f"ℹ️ 跟卖数量: {actual_count} (未设置期望值)")
        
        return True

    def _check_has_better_competitor_price(self, price_data: Dict[str, Any]) -> bool:
        """
        检查是否有更优的跟卖价格

        Args:
            price_data: 价格数据字典

        Returns:
            bool: 如果跟卖价格更优返回True，否则返回False
        """
        try:
            green_price = price_data.get('green_price')
            black_price = price_data.get('black_price')
            competitor_price = price_data.get('competitor_price')

            # 跟卖价格无效时返回 False
            if not competitor_price or competitor_price <= 0:
                return False

            # 没有主价格时返回 False
            if not black_price:
                return False

            # 优先比较绿标价格，其次比较黑标价格
            compare_price = green_price if green_price else black_price

            return competitor_price < compare_price

        except Exception as e:
            print(f"⚠️ 判断跟卖价格优势时出错: {e}")
            return False

    def _validate_competitor_data(self, actual_data: Dict[str, Any], expected: Dict[str, Any], test_case_id: str) -> bool:
        """验证跟卖店铺数据"""
        print(f"\n🔍 验证跟卖店铺数据 - {test_case_id}")
        
        competitors = actual_data.get('competitors', [])
        has_competitors_expected = expected.get('has_competitors', False)
        
        if not has_competitors_expected:
            if len(competitors) == 0:
                print(f"✅ 跟卖店铺验证通过: 无跟卖店铺")
                return True
            else:
                print(f"⚠️ 意外发现跟卖店铺: {len(competitors)} 个")
                return True  # 不算错误，只是意外情况
        
        if len(competitors) == 0:
            print(f"❌ 跟卖店铺验证失败: 期望有跟卖店铺但未找到")
            return False
        
        print(f"✅ 找到 {len(competitors)} 个跟卖店铺")
        
        # 验证跟卖店铺字段
        required_fields = self.validation_rules.get('competitor_required_fields', [])
        
        for i, competitor in enumerate(competitors[:3], 1):  # 只验证前3个
            print(f"  验证第{i}个跟卖店铺:")
            
            for field in required_fields:
                if field not in competitor:
                    print(f"    ❌ 缺少必需字段: {field}")
                    return False
                else:
                    value = competitor[field]
                    print(f"    ✅ {field}: {value}")
            
            # 验证价格合理性
            if competitor.get('price'):
                actual_price = competitor['price']
                if actual_price <= 0:
                    print(f"    ❌ 价格异常: {actual_price}₽ (价格应大于0)")
                    return False
        
        return True

    def test_single_case(self, test_case: Dict[str, Any]) -> bool:
        """测试单个用例 - 同步版本"""
        test_id = test_case['id']
        test_name = test_case['name']
        url = test_case['url']
        expected = test_case['expected']
        options = test_case.get('test_options', {})

        print(f"\n" + "="*80)
        print(f"🧪 {test_name} ({test_id})")
        print("="*80)
        print(f"📍 测试URL: {url}")
        print(f"📋 测试选项: {options}")

        try:
            start_time = time.time()

            # 调用同步 scrape 方法
            include_competitors = options.get('include_competitors', False)
            result = self.scraper.scrape(url, include_competitors=include_competitors)
            
            execution_time = time.time() - start_time
            print(f"⏱️ 执行时间: {execution_time:.2f}秒")
            
            if not result.success:
                print(f"❌ scrape() 方法调用失败: {result.error_message}")
                return False
            
            print(f"✅ scrape() 方法调用成功")
            print(f"📊 返回数据结构: {list(result.data.keys())}")
            
            # 验证价格数据
            if not self._validate_price_data(result.data, expected, test_id):
                return False
            
            # 如果包含跟卖信息，验证跟卖数据
            if include_competitors:
                if not self._validate_competitor_data(result.data, expected, test_id):
                    return False
            
            print(f"🎉 {test_name} 测试通过！")
            return True
            
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_all_tests(self) -> bool:
        """运行所有测试用例 - 同步版本"""
        print("🚀 开始 OzonScraper.scrape() 方法测试")
        print(f"📋 共 {len(self.test_cases)} 个测试用例")

        if not self._setup_scraper():
            return False

        results = []

        for test_case in self.test_cases:
            success = self.test_single_case(test_case)
            results.append((test_case['name'], success))
        
        # 输出测试结果总结
        print("\n" + "="*80)
        print("📊 测试结果总结")
        print("="*80)
        
        success_count = 0
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{status} {test_name}")
            if success:
                success_count += 1
        
        print(f"\n🎯 总体结果: {success_count}/{len(results)} 个测试通过")
        
        if success_count == len(results):
            print("🎉 所有测试通过！OzonScraper.scrape() 方法工作正常")
        else:
            print("⚠️ 部分测试失败，需要检查相关功能")
        
        return success_count == len(results)

    def close(self):
        """关闭测试器"""
        if self.scraper:
            self.scraper.close()


async def main():
    """主函数"""
    tester = OzonScraperMethodTester()
    
    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        tester.close()


if __name__ == "__main__":
    # 运行同步测试
    exit_code = main()
    sys.exit(exit_code)


class TestOzonScraperMethod(unittest.TestCase):
    """OzonScraper.scrape() 方法单元测试 - 同步版本"""

    def setUp(self):
        """测试初始化"""
        self.tester = OzonScraperMethodTester()

    def tearDown(self):
        """测试清理"""
        self.tester.close()

    def test_scenario_1_no_competitors(self):
        """测试场景1：无跟卖店铺 - 同步版本"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_1_no_competitors'), None)
        self.assertIsNotNone(test_case, "找不到测试用例 scenario_1_no_competitors")

        self.assertTrue(self.tester._setup_scraper(), "OzonScraper 初始化失败")
        success = self.tester.test_single_case(test_case)
        self.assertTrue(success, f"测试用例 {test_case['name']} 失败")

    def test_scenario_2_with_competitors(self):
        """测试场景2：有跟卖店铺 - 同步版本"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_2_with_competitors'), None)
        self.assertIsNotNone(test_case, "找不到测试用例 scenario_2_with_competitors")

        self.assertTrue(self.tester._setup_scraper(), "OzonScraper 初始化失败")
        success = self.tester.test_single_case(test_case)
        self.assertTrue(success, f"测试用例 {test_case['name']} 失败")

    def test_scenario_3_many_competitors(self):
        """测试场景3：跟卖店铺超过10个 - 同步版本"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_3_many_competitors'), None)
        self.assertIsNotNone(test_case, "找不到测试用例 scenario_3_many_competitors")

        self.assertTrue(self.tester._setup_scraper(), "OzonScraper 初始化失败")
        success = self.tester.test_single_case(test_case)
        self.assertTrue(success, f"测试用例 {test_case['name']} 失败")

    def test_scenario_4_product_1176594312(self):
        """测试场景4：商品ID 1176594312 - 同步版本"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_4_product_1176594312'), None)
        self.assertIsNotNone(test_case, "找不到测试用例 scenario_4_product_1176594312")

        self.assertTrue(self.tester._setup_scraper(), "OzonScraper 初始化失败")
        success = self.tester.test_single_case(test_case)
        self.assertTrue(success, f"测试用例 {test_case['name']} 失败")
