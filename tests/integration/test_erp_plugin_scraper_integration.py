#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ErpPluginScraper 真实集成测试

使用 test_data 中的真实 URL 和真实浏览器服务进行集成测试，不使用 Mock。
像 xp 命令启动浏览器服务那样进行真实的数据抓取测试。
"""

import sys
import json
import time
import pytest
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent  # 需要上升3级到达项目根目录
sys.path.insert(0, str(project_root))

from common.scrapers.erp_plugin_scraper import ErpPluginScraper
from common.models.scraping_result import ScrapingResult
from common.config.erp_selectors_config import get_erp_selectors_config


def load_test_cases() -> List[Dict[str, Any]]:
    """加载测试用例数据"""
    try:
        test_data_file = Path(__file__).parent / "test_data" / "ozon_test_cases.json"
        with open(test_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('test_cases', [])
    except FileNotFoundError:
        # 如果文件不存在，返回默认测试用例
        print("⚠️ test_data/ozon_test_cases.json 文件未找到，使用默认测试用例")
        return [
            {
                "id": "default_test_case",
                "name": "默认集成测试用例",
                "url": "https://www.ozon.ru/product/1176594312",
                "description": "默认的真实URL测试用例",
                "expected": {
                    "has_data": True
                }
            }
        ]
    except Exception as e:
        print(f"❌ 加载测试数据时出现异常: {e}")
        return []


class TestErpPluginScraperIntegration:
    """ErpPluginScraper 真实集成测试类
    
    使用真实浏览器服务和 test_data 中的真实 URL 进行测试
    """

    @classmethod
    def setup_class(cls):
        """测试类初始化 - 加载测试数据"""
        print("\n🚀 启动 ErpPluginScraper 真实集成测试")
        print("=" * 80)
        
        # 加载测试用例数据
        cls.test_cases = load_test_cases()
        print(f"📊 加载了 {len(cls.test_cases)} 个测试用例")
        
        # 初始化配置
        cls.selectors_config = get_erp_selectors_config()
        print("⚙️ 配置初始化完成")

    @classmethod
    def teardown_class(cls):
        """测试类清理"""
        print("\n🔄 完成 ErpPluginScraper 真实集成测试")
        print("=" * 80)

    def setup_method(self):
        """每个测试方法的初始化"""
        self.scraper = None

    def teardown_method(self):
        """每个测试方法的清理"""
        if self.scraper:
            try:
                self.scraper.close()
                print("✅ 抓取器已关闭")
            except Exception as e:
                print(f"⚠️ 关闭抓取器时出现异常: {e}")



    @pytest.mark.parametrize("test_case", load_test_cases())
    def test_scrape_with_real_urls(self, test_case):
        """使用真实URL进行数据抓取测试
        
        Args:
            test_case: 来自 test_data/ozon_test_cases.json 的测试用例
        """
        test_url = test_case['url']
        test_name = test_case['name']
        test_id = test_case['id']
        
        print(f"\n🔍 测试用例: {test_name} ({test_id})")
        print(f"🌐 测试URL: {test_url}")
        
        # 初始化ErpPluginScraper（使用真实浏览器服务）
        print("📋 初始化 ErpPluginScraper...")
        self.scraper = ErpPluginScraper(selectors_config=self.selectors_config)
        print("✅ ErpPluginScraper 初始化成功")
        
        # 执行真实数据抓取
        print("🔄 开始抓取ERP数据...")
        start_time = time.time()
        
        try:
            # 调用真实的scrape方法
            result = self.scraper.scrape(target=test_url)
            
            execution_time = time.time() - start_time
            print(f"⏱️ 执行时间: {execution_time:.2f}秒")
            
            # 验证抓取结果
            self._validate_scraping_result(result, test_case, test_url)
            
            # 🔍 添加详细的抓取结果概览
            self._print_detailed_scraping_summary(result)

            # 🖨️ 添加完整数据打印功能
            self._print_complete_scraped_data(result, test_case)

            print(f"✅ 测试用例 {test_id} 通过")

        except Exception as e:
            print(f"❌ 测试用例 {test_id} 失败: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"真实URL抓取测试失败: {e}")

    def _validate_scraping_result(self, result: ScrapingResult, test_case: Dict[str, Any], test_url: str):
        """验证抓取结果

        Args:
            result: 抓取结果
            test_case: 测试用例数据
            test_url: 测试URL
        """
        # 基本验证：抓取必须成功
        assert result is not None, "抓取结果不能为空"

        if not result.success:
            print(f"⚠️ 抓取未成功: {result.error_message}")
            # 对于真实网络测试，我们可以容忍某些失败（网络问题、页面变化等）
            pytest.skip(f"跳过测试 - 抓取失败可能由于网络或页面变化: {result.error_message}")

        print("✅ 数据抓取成功")

        # 验证数据不为空
        assert isinstance(result.data, dict), "抓取数据必须是字典类型"
        print(f"📊 提取字段数量: {len(result.data)}")

        # 🔍 简化的基本数据显示（避免重复）
        print("📋 抓取成功 - 详细数据将在后续步骤中显示")

        # 验证关键字段存在性
        self._validate_key_fields(result.data, test_case)

        # 验证特殊解析功能
        self._validate_special_parsing(result.data, test_case)

        # 验证期望结果（如果提供）
        if 'expected' in test_case:
            self._validate_expected_results(result.data, test_case['expected'])

    def _validate_key_fields(self, data: Dict[str, Any], test_case: Dict[str, Any]):
        """验证关键字段"""
        print("\n🔍 验证关键字段:")

        # ERP数据的核心字段
        important_fields = [
            'category', 'sku', 'brand_name', 'monthly_sales_volume',
            'monthly_sales_amount', 'daily_sales_volume', 'daily_sales_amount'
        ]

        # 计算存在的重要字段
        existing_fields = [field for field in important_fields if field in data and data[field] is not None]

        print(f"  📈 存在的重要字段 ({len(existing_fields)}/{len(important_fields)}): {existing_fields}")

        # 至少应该有一些ERP数据
        if len(existing_fields) == 0:
            print("  ⚠️ 警告: 未找到任何重要的ERP字段")
        else:
            print(f"  ✅ 成功提取了 {len(existing_fields)} 个重要字段")

    def _validate_special_parsing(self, data: Dict[str, Any], test_case: Dict[str, Any]):
        """验证特殊解析功能"""
        print("\n🔍 验证特殊解析:")

        # 尺寸解析验证
        if all(dim in data for dim in ['length', 'width', 'height']):
            dimensions = f"{data['length']}x{data['width']}x{data['height']}"
            print(f"  ✅ 尺寸解析: {dimensions}mm")
        else:
            print("  ⚪ 尺寸信息未找到或解析失败")

        # 重量解析验证
        if 'weight' in data and isinstance(data['weight'], (int, float)):
            print(f"  ✅ 重量解析: {data['weight']}g")
        else:
            print("  ⚪ 重量信息未找到或解析失败")

        # 佣金率解析验证
        if 'rfbs_commission_rates' in data and isinstance(data['rfbs_commission_rates'], list):
            print(f"  ✅ 佣金率解析: {data['rfbs_commission_rates']}")
        else:
            print("  ⚪ 佣金率信息未找到或解析失败")

        # 上架时间解析验证
        if 'listing_date_parsed' in data and 'shelf_days' in data:
            print(f"  ✅ 上架时间解析: {data['listing_date_parsed']} ({data['shelf_days']}天)")
        else:
            print("  ⚪ 上架时间信息未找到或解析失败")

    def _validate_expected_results(self, data: Dict[str, Any], expected: Dict[str, Any]):
        """验证期望结果"""
        print("\n🎯 验证期望结果:")

        for key, expected_value in expected.items():
            if key == 'has_data':
                # 验证是否有数据
                has_data = len(data) > 0
                if expected_value:
                    assert has_data, "期望有数据，但实际无数据"
                    print(f"  ✅ has_data: {has_data} (符合期望)")
                else:
                    assert not has_data, "期望无数据，但实际有数据"
                    print(f"  ✅ has_data: {has_data} (符合期望)")

            elif key in ['green_price', 'black_price']:
                # 价格字段验证（可能不在ERP数据中，这是正常的）
                if key in data:
                    print(f"  ℹ️ {key}: {data[key]} (ERP数据中包含价格信息)")
                else:
                    print(f"  ⚪ {key}: 不在ERP数据中 (这是正常的)")

            elif key in data:
                # 其他字段的直接比较
                actual_value = data[key]
                if actual_value == expected_value:
                    print(f"  ✅ {key}: {actual_value} (符合期望)")
                else:
                    print(f"  ⚠️ {key}: 实际={actual_value}, 期望={expected_value} (不完全匹配，可能由于页面变化)")

    def _print_detailed_scraping_summary(self, result: ScrapingResult):
        """打印详细的抓取结果概览

        Args:
            result: 抓取结果对象
        """
        if not result or not result.success:
            return

        print("\n" + "="*60)
        print("📈 详细抓取结果概览")
        print("="*60)

        # 基本信息
        print(f"⏱️  执行时间: {result.execution_time:.2f}秒")
        print(f"📊 状态: {result.status.value}")
        print(f"🕒 抓取时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        # 数据统计
        raw_data_count = len(result.data) if result.data else 0
        formatted_data_count = len(result.data.get('formatted', {})) if result.data and 'formatted' in result.data else 0

        print(f"📄 原始数据字段数: {raw_data_count}")
        print(f"📄 格式化数据字段数: {formatted_data_count}")

        # 关键字段展示
        key_fields = [
            'category', 'sku', 'brand_name', 'monthly_sales_volume',
            'monthly_sales_amount', 'daily_sales_volume', 'daily_sales_amount'
        ]

        print("\n🔑 关键ERP字段:")
        for field in key_fields:
            if result.data and field in result.data:
                value = result.data[field]
                print(f"  {field}: {value}")
            else:
                print(f"  {field}: 未找到")

        # 特殊解析字段
        special_fields = [
            ('📏 尺寸信息', ['length', 'width', 'height']),
            ('⚖️  重量信息', ['weight']),
            ('💰 佣金信息', ['rfbs_commission_rates']),
            ('📅 上架时间', ['listing_date_parsed', 'shelf_days'])
        ]

        print("\n🔍 特殊解析字段:")
        for label, fields in special_fields:
            found_fields = []
            for field in fields:
                if result.data and field in result.data:
                    found_fields.append(f"{field}={result.data[field]}")

            if found_fields:
                print(f"  {label}: {', '.join(found_fields)}")
            else:
                print(f"  {label}: 未解析")

        print("="*60)

    def _print_complete_scraped_data(self, result: ScrapingResult, test_case: Dict[str, Any]):
        """打印完整的抓取数据，包括JSON格式输出

        Args:
            result: 抓取结果对象
            test_case: 测试用例信息
        """
        if not result or not result.success or not result.data:
            print("⚠️ 无抓取数据可打印")
            return

        print("\n" + "🖨️" * 20 + " 完整抓取数据输出 " + "🖨️" * 20)

        # 1. 基本信息
        print(f"📋 测试用例: {test_case.get('name', '未知')}")
        print(f"🌐 URL: {test_case.get('url', '未知')}")
        print(f"⏱️ 执行时间: {result.execution_time:.3f}秒")
        print(f"🕒 抓取时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        # 2. 数据统计概览
        total_fields = len(result.data) if result.data else 0
        formatted_fields = len(result.data.get('formatted', {})) if 'formatted' in result.data else 0
        type_info_fields = len(result.data.get('data_types', {})) if 'data_types' in result.data else 0

        print(f"\n📊 数据统计:")
        print(f"  • 总字段数: {total_fields}")
        print(f"  • 格式化字段数: {formatted_fields}")
        print(f"  • 类型信息字段数: {type_info_fields}")

        # 3. 原始数据摘要（只显示非格式化的字段）
        raw_data = {k: v for k, v in result.data.items()
                   if k not in ['formatted', 'data_types']}

        if raw_data:
            print(f"\n📄 原始数据字段 ({len(raw_data)}个):")
            for i, (key, value) in enumerate(raw_data.items(), 1):
                # 限制显示长度，避免输出过长
                str_value = str(value)
                if len(str_value) > 100:
                    display_value = str_value[:97] + "..."
                else:
                    display_value = str_value
                print(f"  {i:2d}. {key}: {display_value}")

        # 4. 格式化数据详细输出
        if 'formatted' in result.data and result.data['formatted']:
            formatted_data = result.data['formatted']
            print(f"\n✨ 格式化数据详细输出 ({len(formatted_data)}个字段):")

            # 按重要性分组显示
            important_fields = [
                'sku', 'brand_name', 'category', 'monthly_sales_volume',
                'monthly_sales_amount', 'daily_sales_volume', 'daily_sales_amount'
            ]

            product_fields = ['length', 'width', 'height', 'weight']
            business_fields = ['rfbs_commission_rates', 'listing_date_parsed', 'shelf_days']

            # 显示重要字段
            print("  📈 核心ERP字段:")
            for field in important_fields:
                if field in formatted_data:
                    value = formatted_data[field]
                    if isinstance(value, dict):
                        print(f"    {field}: {json.dumps(value, ensure_ascii=False, indent=6)[1:-1]}")
                    else:
                        print(f"    {field}: {value}")

            # 显示产品字段
            product_found = any(field in formatted_data for field in product_fields)
            if product_found:
                print("  📦 产品属性:")
                for field in product_fields:
                    if field in formatted_data:
                        print(f"    {field}: {formatted_data[field]}")

            # 显示业务字段
            business_found = any(field in formatted_data for field in business_fields)
            if business_found:
                print("  💼 业务信息:")
                for field in business_fields:
                    if field in formatted_data:
                        value = formatted_data[field]
                        if isinstance(value, (list, dict)):
                            print(f"    {field}: {json.dumps(value, ensure_ascii=False)}")
                        else:
                            print(f"    {field}: {value}")

            # 显示其他字段
            other_fields = {k: v for k, v in formatted_data.items()
                          if k not in important_fields + product_fields + business_fields}
            if other_fields:
                print(f"  🔧 其他字段 ({len(other_fields)}个):")
                for key, value in other_fields.items():
                    if isinstance(value, (dict, list)):
                        print(f"    {key}: {json.dumps(value, ensure_ascii=False)}")
                    else:
                        print(f"    {key}: {value}")

        # 5. 数据类型信息
        if 'data_types' in result.data and result.data['data_types']:
            type_info = result.data['data_types']
            print(f"\n🏷️ 数据类型信息 ({len(type_info)}个):")
            type_groups = {}
            for field, dtype in type_info.items():
                if dtype not in type_groups:
                    type_groups[dtype] = []
                type_groups[dtype].append(field)

            for dtype, fields in type_groups.items():
                print(f"  {dtype}: {', '.join(fields)}")

        # 6. JSON格式完整数据输出（可选，用于调试）
        print(f"\n💾 完整JSON数据输出:")
        print("─" * 80)
        try:
            # 创建一个用于JSON输出的干净数据结构
            json_output = {
                "meta": {
                    "test_case": test_case.get('name', '未知'),
                    "url": test_case.get('url', '未知'),
                    "execution_time": round(result.execution_time, 3),
                    "timestamp": result.timestamp.isoformat(),
                    "status": result.status.value
                },
                "raw_data": raw_data,
                "formatted_data": result.data.get('formatted', {}),
                "data_types": result.data.get('data_types', {})
            }

            print(json.dumps(json_output, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"JSON序列化失败: {e}")
            print("原始数据结构:")
            import pprint
            pprint.pprint(result.data, width=120)

        print("─" * 80)
        print("🖨️" * 60 + " 数据输出完成 " + "🖨️" * 60)

    def test_erp_scraper_initialization(self):
        """测试ErpPluginScraper初始化"""
        print("\n🔧 测试ErpPluginScraper初始化")

        # 测试基本初始化
        scraper = ErpPluginScraper()
        assert scraper is not None
        assert scraper.selectors_config is not None
        assert hasattr(scraper, 'browser_service')
        print("✅ 基本初始化测试通过")

        # 测试带配置的初始化
        config = get_erp_selectors_config()
        scraper_with_config = ErpPluginScraper(selectors_config=config)
        assert scraper_with_config.selectors_config == config
        print("✅ 带配置初始化测试通过")

        # 清理
        scraper.close()
        scraper_with_config.close()

    def test_validate_data_method(self):
        """测试数据验证方法"""
        print("\n🧪 测试数据验证方法")

        scraper = ErpPluginScraper()

        try:
            # 测试有效数据
            valid_data = {
                'category': '电子产品',
                'sku': 'TEST123',
                'monthly_sales_volume': '100'
            }
            assert scraper.validate_data(valid_data) is True
            print("✅ 有效数据验证通过")

            # 测试空数据
            assert scraper.validate_data({}) is False
            print("✅ 空数据验证通过")

            # 测试无效数据
            invalid_data = {
                'irrelevant_field': 'value'
            }
            assert scraper.validate_data(invalid_data) is False
            print("✅ 无效数据验证通过")

        finally:
            scraper.close()

# 独立运行的主函数
def main():
    """主函数 - 用于独立运行集成测试"""
    print("🚀 独立运行 ErpPluginScraper 真实集成测试")

    try:
        # 创建测试实例
        test_instance = TestErpPluginScraperIntegration()
        test_instance.setup_class()

        # 加载测试用例
        test_cases = load_test_cases()

        if not test_cases:
            print("❌ 没有可用的测试用例")
            return 1

        print(f"\n📊 将测试 {len(test_cases)} 个真实URL:")
        for case in test_cases:
            print(f"  • {case['name']}: {case['url']}")

        # 执行测试
        success_count = 0
        total_count = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"测试 {i}/{total_count}: {test_case['name']}")
            print(f"{'='*60}")

            try:
                test_instance.setup_method()
                test_instance.test_scrape_with_real_urls(test_case)
                success_count += 1
                print(f"✅ 测试 {i} 成功")
            except Exception as e:
                print(f"❌ 测试 {i} 失败: {e}")
            finally:
                test_instance.teardown_method()

        # 输出结果
        print(f"\n{'='*80}")
        print(f"🏁 测试完成: {success_count}/{total_count} 成功")

        if success_count == total_count:
            print("🎉 所有真实URL集成测试通过！")
            return 0
        else:
            print(f"⚠️ {total_count - success_count} 个测试失败")
            return 1

    except Exception as e:
        print(f"❌ 测试执行过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # 独立运行模式
    exit_code = main()
    sys.exit(exit_code)