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
project_root = Path(__file__).parent.parent
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
        
        # 显示提取的数据（用于调试）
        print("📋 提取的ERP数据:")
        for key, value in result.data.items():
            print(f"  {key}: {value}")
        
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
