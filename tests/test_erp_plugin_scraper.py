#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ERP插件抓取器测试

测试 ErpPluginScraper 的功能，包括数据解析和字段映射
"""

import asyncio
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
from common.scrapers.erp_plugin_scraper import ErpPluginScraper
from common.models import ScrapingResult

class ErpPluginScraperTester:
    """ERP插件抓取器测试器"""

    def __init__(self):
        """初始化测试器"""
        self.config = get_config()
        self.scraper = None
        self.test_html_path = Path(__file__).parent / "resources" / "erp_plugin_debug_1702055870.html"
        self.expected_data = self._get_expected_data()

    def _get_expected_data(self) -> Dict[str, Any]:
        """获取期望的测试数据"""
        return {
            'category': '小百货和配饰/锁匙扣',
            'rfbs_commission': '12% 14% 20.5%',
            'rfbs_commission_rates': [12.0, 14.0, 20.5],
            'sku': '1702055870',
            'brand_name': 'Папа Карлов',
            'monthly_sales_volume': '4289',
            'monthly_sales_amount': '₽190.31万 ≈ ¥16.71万',
            'monthly_turnover_trend': '-59.9%',
            'daily_sales_volume': '150.04',
            'daily_sales_amount': '41296.65₽',
            'ad_cost_ratio': '16.19%',
            'promotion_days': '21',
            'promotion_discount': '30.15%',
            'promotion_conversion_rate': '63.55%',
            'paid_promotion_days': '28',
            'product_card_views': '164789',
            'product_card_add_rate': '9.18%',
            'search_catalog_views': '930393',
            'search_catalog_add_rate': '0.07%',
            'display_conversion_rate': '0.02%',
            'product_click_rate': '0.77%',
            'shipping_mode': 'FBO',
            'return_cancel_rate': '5.2%',
            'dimensions': '50 x 37 x 43mm',
            'length': 50.0,
            'width': 37.0,
            'height': 43.0,
            'weight': 40.0,
            'listing_date': '2024-09-23(415天)',
            'listing_date_parsed': '2024-09-23',
            'shelf_days': 415,
            'competitor_list': 'Шиюнь ун...等50个卖家',
            'competitor_min_price': '102',
            'competitor_max_price': '₽10230.00 ≈ ¥898.19'
        }

    def _setup_scraper(self):
        """初始化抓取器"""
        try:
            self.scraper = ErpPluginScraper(self.config)
            print("✅ ErpPluginScraper 初始化成功")
            return True
        except Exception as e:
            print(f"❌ ErpPluginScraper 初始化失败: {e}")
            return False

    def _load_test_html(self) -> str:
        """加载测试HTML文件"""
        try:
            if not self.test_html_path.exists():
                raise FileNotFoundError(f"测试HTML文件不存在: {self.test_html_path}")
            
            with open(self.test_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            print(f"✅ 成功加载测试HTML文件: {self.test_html_path}")
            return html_content
            
        except Exception as e:
            print(f"❌ 加载测试HTML文件失败: {e}")
            raise

    def _validate_basic_fields(self, actual_data: Dict[str, Any]) -> bool:
        """验证基础字段"""
        print("\n🔍 验证基础字段")
        
        basic_fields = [
            'category', 'sku', 'brand_name', 'monthly_sales_volume',
            'daily_sales_volume', 'shipping_mode'
        ]
        
        for field in basic_fields:
            expected_value = self.expected_data.get(field)
            actual_value = actual_data.get(field)
            
            if expected_value is None:
                continue
                
            if actual_value != expected_value:
                print(f"❌ {field} 验证失败: 期望 '{expected_value}', 实际 '{actual_value}'")
                return False
            else:
                print(f"✅ {field}: {actual_value}")
        
        return True

    def _validate_numeric_fields(self, actual_data: Dict[str, Any]) -> bool:
        """验证数值字段"""
        print("\n🔍 验证数值字段")
        
        numeric_fields = {
            'length': 50.0,
            'width': 37.0,
            'height': 43.0,
            'weight': 40.0,
            'shelf_days': 415
        }
        
        for field, expected_value in numeric_fields.items():
            actual_value = actual_data.get(field)
            
            if actual_value is None:
                print(f"❌ {field} 验证失败: 期望 {expected_value}, 实际 None")
                return False
            
            if abs(actual_value - expected_value) > 0.1:  # 允许小误差
                print(f"❌ {field} 验证失败: 期望 {expected_value}, 实际 {actual_value}")
                return False
            else:
                print(f"✅ {field}: {actual_value}")
        
        return True

    def _validate_commission_rates(self, actual_data: Dict[str, Any]) -> bool:
        """验证佣金率解析"""
        print("\n🔍 验证佣金率解析")
        
        expected_rates = [12.0, 14.0, 20.5]
        actual_rates = actual_data.get('rfbs_commission_rates')
        
        if actual_rates is None:
            print(f"❌ 佣金率验证失败: 期望 {expected_rates}, 实际 None")
            return False
        
        if actual_rates != expected_rates:
            print(f"❌ 佣金率验证失败: 期望 {expected_rates}, 实际 {actual_rates}")
            return False
        
        print(f"✅ 佣金率解析: {actual_rates}")
        return True

    def _validate_date_parsing(self, actual_data: Dict[str, Any]) -> bool:
        """验证日期解析"""
        print("\n🔍 验证日期解析")
        
        expected_date = '2024-09-23'
        expected_days = 415
        
        actual_date = actual_data.get('listing_date_parsed')
        actual_days = actual_data.get('shelf_days')
        
        if actual_date != expected_date:
            print(f"❌ 上架日期验证失败: 期望 '{expected_date}', 实际 '{actual_date}'")
            return False
        
        if actual_days != expected_days:
            print(f"❌ 上架天数验证失败: 期望 {expected_days}, 实际 {actual_days}")
            return False
        
        print(f"✅ 上架日期: {actual_date}")
        print(f"✅ 上架天数: {actual_days}")
        return True

    def test_html_parsing(self) -> bool:
        """测试HTML解析功能"""
        print("\n" + "="*80)
        print("🧪 测试ERP插件HTML解析功能")
        print("="*80)
        
        try:
            # 加载测试HTML
            html_content = self._load_test_html()
            
            # 直接调用解析方法
            start_time = time.time()
            erp_data = self.scraper._extract_erp_data_from_content(html_content)
            execution_time = time.time() - start_time
            
            print(f"⏱️ 解析时间: {execution_time:.3f}秒")
            print(f"📊 提取字段数量: {len(erp_data)}")
            
            if not erp_data:
                print("❌ 未提取到任何ERP数据")
                return False
            
            # 显示提取的数据
            print(f"\n📋 提取的数据字段:")
            for key, value in erp_data.items():
                print(f"  {key}: {value}")
            
            # 验证各类字段
            if not self._validate_basic_fields(erp_data):
                return False
            
            if not self._validate_numeric_fields(erp_data):
                return False
            
            if not self._validate_commission_rates(erp_data):
                return False
            
            if not self._validate_date_parsing(erp_data):
                return False
            
            print(f"\n🎉 HTML解析测试通过！")
            return True
            
        except Exception as e:
            print(f"❌ HTML解析测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_field_mappings(self) -> bool:
        """测试字段映射完整性"""
        print("\n" + "="*80)
        print("🧪 测试字段映射完整性")
        print("="*80)
        
        try:
            expected_mappings = {
                '类目': 'category',
                'rFBS佣金': 'rfbs_commission',
                'SKU': 'sku',
                '品牌': 'brand_name',
                '月销量': 'monthly_sales_volume',
                '月销售额': 'monthly_sales_amount',
                '月周转动态': 'monthly_turnover_trend',
                '日销量': 'daily_sales_volume',
                '日销售额': 'daily_sales_amount',
                '广告费占比': 'ad_cost_ratio',
                '参与促销天数': 'promotion_days',
                '参与促销的折扣': 'promotion_discount',
                '促销活动的转化率': 'promotion_conversion_rate',
                '付费推广天数': 'paid_promotion_days',
                '商品卡浏览量': 'product_card_views',
                '商品卡加购率': 'product_card_add_rate',
                '搜索目录浏览量': 'search_catalog_views',
                '搜索目录加购率': 'search_catalog_add_rate',
                '展示转化率': 'display_conversion_rate',
                '商品点击率': 'product_click_rate',
                '发货模式': 'shipping_mode',
                '退货取消率': 'return_cancel_rate',
                '长 宽 高': 'dimensions',
                '重 量': 'weight',
                '上架时间': 'listing_date',
                '跟卖列表': 'competitor_list',
                '跟卖最低价': 'competitor_min_price',
                '跟卖最高价': 'competitor_max_price'
            }
            
            actual_mappings = self.scraper.field_mappings
            
            print(f"📊 期望映射数量: {len(expected_mappings)}")
            print(f"📊 实际映射数量: {len(actual_mappings)}")
            
            # 检查缺失的映射
            missing_mappings = []
            for chinese_label, english_key in expected_mappings.items():
                if chinese_label not in actual_mappings:
                    missing_mappings.append(chinese_label)
                elif actual_mappings[chinese_label] != english_key:
                    print(f"❌ 映射不匹配: '{chinese_label}' -> 期望 '{english_key}', 实际 '{actual_mappings[chinese_label]}'")
                    return False
            
            if missing_mappings:
                print(f"❌ 缺失的字段映射: {missing_mappings}")
                return False
            
            # 检查多余的映射
            extra_mappings = []
            for chinese_label in actual_mappings:
                if chinese_label not in expected_mappings:
                    extra_mappings.append(chinese_label)
            
            if extra_mappings:
                print(f"⚠️ 多余的字段映射: {extra_mappings}")
            
            print(f"✅ 字段映射完整性验证通过")
            return True
            
        except Exception as e:
            print(f"❌ 字段映射测试异常: {e}")
            return False

    def test_special_parsing_methods(self) -> bool:
        """测试特殊解析方法"""
        print("\n" + "="*80)
        print("🧪 测试特殊解析方法")
        print("="*80)
        
        try:
            # 测试尺寸解析
            print("\n🔍 测试尺寸解析")
            dimensions_result = self.scraper._parse_dimensions("50 x 37 x 43mm")
            expected_dimensions = {'length': 50.0, 'width': 37.0, 'height': 43.0}
            
            if dimensions_result != expected_dimensions:
                print(f"❌ 尺寸解析失败: 期望 {expected_dimensions}, 实际 {dimensions_result}")
                return False
            print(f"✅ 尺寸解析: {dimensions_result}")
            
            # 测试重量解析
            print("\n🔍 测试重量解析")
            weight_result = self.scraper._parse_weight("40g")
            expected_weight = 40.0
            
            if weight_result != expected_weight:
                print(f"❌ 重量解析失败: 期望 {expected_weight}, 实际 {weight_result}")
                return False
            print(f"✅ 重量解析: {weight_result}")
            
            # 测试上架时间解析
            print("\n🔍 测试上架时间解析")
            date_result = self.scraper._parse_listing_date("2024-09-23(415天)")
            expected_date = {'listing_date_parsed': '2024-09-23', 'shelf_days': 415}
            
            if date_result != expected_date:
                print(f"❌ 上架时间解析失败: 期望 {expected_date}, 实际 {date_result}")
                return False
            print(f"✅ 上架时间解析: {date_result}")
            
            # 测试佣金率解析
            print("\n🔍 测试佣金率解析")
            commission_result = self.scraper._parse_rfbs_commission("12% 14% 20.5%")
            expected_commission = [12.0, 14.0, 20.5]
            
            if commission_result != expected_commission:
                print(f"❌ 佣金率解析失败: 期望 {expected_commission}, 实际 {commission_result}")
                return False
            print(f"✅ 佣金率解析: {commission_result}")
            
            print(f"\n🎉 特殊解析方法测试通过！")
            return True
            
        except Exception as e:
            print(f"❌ 特殊解析方法测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始 ErpPluginScraper 测试")
        
        if not self._setup_scraper():
            return False
        
        tests = [
            ("字段映射完整性", self.test_field_mappings),
            ("特殊解析方法", self.test_special_parsing_methods),
            ("HTML解析功能", self.test_html_parsing),
        ]
        
        results = []
        
        for test_name, test_method in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                success = test_method()
                results.append((test_name, success))
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
                results.append((test_name, False))
        
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
            print("🎉 所有测试通过！ErpPluginScraper 工作正常")
        else:
            print("⚠️ 部分测试失败，需要检查相关功能")
        
        return success_count == len(results)

    def close(self):
        """关闭测试器"""
        if self.scraper:
            self.scraper.close()

async def main():
    """主函数"""
    tester = ErpPluginScraperTester()
    
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
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

class TestErpPluginScraper(unittest.IsolatedAsyncioTestCase):
    """ErpPluginScraper 单元测试"""
    
    def setUp(self):
        """测试初始化"""
        self.tester = ErpPluginScraperTester()
    
    def tearDown(self):
        """测试清理"""
        self.tester.close()
    
    def test_field_mappings(self):
        """测试字段映射"""
        self.assertTrue(self.tester._setup_scraper(), "ErpPluginScraper 初始化失败")
        success = self.tester.test_field_mappings()
        self.assertTrue(success, "字段映射测试失败")
    
    def test_special_parsing_methods(self):
        """测试特殊解析方法"""
        self.assertTrue(self.tester._setup_scraper(), "ErpPluginScraper 初始化失败")
        success = self.tester.test_special_parsing_methods()
        self.assertTrue(success, "特殊解析方法测试失败")
    
    def test_html_parsing(self):
        """测试HTML解析"""
        self.assertTrue(self.tester._setup_scraper(), "ErpPluginScraper 初始化失败")
        success = self.tester.test_html_parsing()
        self.assertTrue(success, "HTML解析测试失败")
