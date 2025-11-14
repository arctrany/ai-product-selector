#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ERP插件抓取器增强测试套件

基于ozon_test_cases.json的测试数据，提供全面的ERP插件功能验证
包括多场景测试、数据验证、性能测试等
"""

import asyncio
import json
import os
import sys
import time
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.config import get_config
from common.scrapers.erp_plugin_scraper import ErpPluginScraper
from common.scrapers.xuanping_browser_service import XuanpingBrowserService
from common.models import ScrapingResult


class ErpPluginEnhancedTester:
    """ERP插件增强测试器"""

    def __init__(self):
        """初始化测试器"""
        self.config = get_config()
        self.scraper = None
        self.browser_service = None
        self.test_cases_file = project_root / "tests" / "test_data" / "ozon_test_cases.json"
        self.test_cases = []
        self.validation_rules = {}
        self.test_results = []

    async def setup(self):
        """异步初始化"""
        print("🚀 开始 ERP插件增强测试套件")
        print("=" * 80)
        
        # 加载测试用例
        await self._load_test_cases()
        
        # 初始化浏览器服务
        await self._setup_browser_service()
        
        # 初始化抓取器
        await self._setup_scraper()

    async def teardown(self):
        """清理资源"""
        if self.scraper:
            await self.scraper.close()
        if self.browser_service:
            await self.browser_service.close()
        print("✅ ERP插件增强测试套件完成")

    async def _load_test_cases(self):
        """加载测试用例数据"""
        try:
            with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.test_cases = data.get('test_cases', [])
                self.validation_rules = data.get('validation_rules', {})
            print(f"📋 加载了 {len(self.test_cases)} 个测试用例")
        except Exception as e:
            raise Exception(f"加载测试用例失败: {e}")

    async def _setup_browser_service(self):
        """设置浏览器服务"""
        try:
            browser_config = {
                'browser_type': 'edge',
                'headless': False,
                'port': 9222
            }
            self.browser_service = XuanpingBrowserService(browser_config)
            await self.browser_service.initialize()
            await self.browser_service.start_browser()
            print("✅ 浏览器服务初始化成功")
        except Exception as e:
            raise Exception(f"浏览器服务初始化失败: {e}")

    async def _setup_scraper(self):
        """设置抓取器"""
        try:
            self.scraper = ErpPluginScraper(self.config, self.browser_service)
            print("✅ ERP插件抓取器初始化成功")
        except Exception as e:
            raise Exception(f"ERP插件抓取器初始化失败: {e}")

    def _validate_erp_data_completeness(self, erp_data: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """验证ERP数据完整性"""
        validation = {
            'required_fields': [],
            'optional_fields': [],
            'missing_fields': [],
            'present_fields': [],
            'completeness_score': 0.0
        }

        # 定义必需字段和可选字段
        required_fields = [
            'category', 'sku', 'brand_name', 'monthly_sales_volume',
            'shipping_mode', 'rfbs_commission_rates'
        ]
        
        optional_fields = [
            'dimensions', 'weight', 'listing_date_parsed', 'shelf_days',
            'competitor_list', 'competitor_min_price', 'competitor_max_price',
            'daily_sales_volume', 'daily_sales_amount', 'ad_cost_ratio'
        ]

        validation['required_fields'] = required_fields
        validation['optional_fields'] = optional_fields

        # 检查必需字段
        for field in required_fields:
            if field in erp_data and erp_data[field] is not None:
                validation['present_fields'].append(field)
            else:
                validation['missing_fields'].append(field)

        # 检查可选字段
        for field in optional_fields:
            if field in erp_data and erp_data[field] is not None:
                validation['present_fields'].append(field)

        # 计算完整性分数
        total_fields = len(required_fields) + len(optional_fields)
        present_count = len(validation['present_fields'])
        validation['completeness_score'] = (present_count / total_fields) * 100

        return validation

    def _validate_erp_data_quality(self, erp_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证ERP数据质量"""
        quality_validation = {
            'data_types': {},
            'value_ranges': {},
            'format_validation': {},
            'quality_score': 0.0,
            'issues': []
        }

        # 数据类型验证
        type_checks = {
            'sku': (str, int),
            'monthly_sales_volume': (str, int, float),
            'length': (int, float, type(None)),
            'width': (int, float, type(None)),
            'height': (int, float, type(None)),
            'weight': (int, float, type(None)),
            'shelf_days': (int, type(None)),
            'rfbs_commission_rates': (list, type(None))
        }

        for field, expected_types in type_checks.items():
            if field in erp_data:
                value = erp_data[field]
                is_valid_type = isinstance(value, expected_types)
                quality_validation['data_types'][field] = {
                    'value': value,
                    'expected_types': [t.__name__ for t in expected_types if t != type(None)],
                    'actual_type': type(value).__name__,
                    'valid': is_valid_type
                }
                if not is_valid_type:
                    quality_validation['issues'].append(f"{field} 类型错误: 期望 {expected_types}, 实际 {type(value)}")

        # 数值范围验证
        range_checks = {
            'length': (0, 10000),  # mm
            'width': (0, 10000),   # mm
            'height': (0, 10000),  # mm
            'weight': (0, 100000), # g
            'shelf_days': (0, 10000)  # days
        }

        for field, (min_val, max_val) in range_checks.items():
            if field in erp_data and isinstance(erp_data[field], (int, float)):
                value = erp_data[field]
                is_in_range = min_val <= value <= max_val
                quality_validation['value_ranges'][field] = {
                    'value': value,
                    'min': min_val,
                    'max': max_val,
                    'valid': is_in_range
                }
                if not is_in_range:
                    quality_validation['issues'].append(f"{field} 超出合理范围: {value} (期望 {min_val}-{max_val})")

        # 格式验证
        if 'rfbs_commission_rates' in erp_data and isinstance(erp_data['rfbs_commission_rates'], list):
            rates = erp_data['rfbs_commission_rates']
            is_valid_rates = all(isinstance(rate, (int, float)) and 0 <= rate <= 100 for rate in rates)
            quality_validation['format_validation']['rfbs_commission_rates'] = {
                'value': rates,
                'valid': is_valid_rates
            }
            if not is_valid_rates:
                quality_validation['issues'].append(f"佣金率格式错误: {rates}")

        # 计算质量分数
        total_checks = len(quality_validation['data_types']) + len(quality_validation['value_ranges']) + len(quality_validation['format_validation'])
        if total_checks > 0:
            valid_checks = sum(1 for checks in [quality_validation['data_types'], quality_validation['value_ranges'], quality_validation['format_validation']] 
                             for check in checks.values() if check.get('valid', False))
            quality_validation['quality_score'] = (valid_checks / total_checks) * 100

        return quality_validation

    async def _test_single_scenario(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个场景"""
        test_id = test_case['id']
        test_name = test_case['name']
        url = test_case['url']
        description = test_case['description']

        print(f"\n🧪 测试场景: {test_name}")
        print(f"📋 描述: {description}")
        print(f"📍 URL: {url}")

        start_time = time.time()
        result = {
            'test_id': test_id,
            'test_name': test_name,
            'url': url,
            'start_time': start_time,
            'success': False,
            'erp_data': {},
            'validation': {},
            'performance': {},
            'errors': []
        }

        try:
            # 执行ERP数据抓取
            print("🔄 开始抓取ERP数据...")
            scrape_result = await self.scraper.scrape(product_url=url)
            
            execution_time = time.time() - start_time
            result['performance']['execution_time'] = execution_time
            result['performance']['erp_detection_time'] = getattr(scrape_result, 'erp_detection_time', None)

            if scrape_result.success and scrape_result.data:
                result['success'] = True
                result['erp_data'] = scrape_result.data
                
                print(f"✅ ERP数据抓取成功")
                print(f"📊 提取字段数量: {len(scrape_result.data)}")
                print(f"⏱️ 执行时间: {execution_time:.2f}秒")

                # 数据完整性验证
                completeness_validation = self._validate_erp_data_completeness(scrape_result.data, test_case)
                result['validation']['completeness'] = completeness_validation

                # 数据质量验证
                quality_validation = self._validate_erp_data_quality(scrape_result.data)
                result['validation']['quality'] = quality_validation

                # 显示验证结果
                print(f"📈 数据完整性: {completeness_validation['completeness_score']:.1f}%")
                print(f"📈 数据质量: {quality_validation['quality_score']:.1f}%")

                if completeness_validation['missing_fields']:
                    print(f"⚠️ 缺失字段: {completeness_validation['missing_fields']}")

                if quality_validation['issues']:
                    print(f"⚠️ 质量问题: {quality_validation['issues']}")

            else:
                result['success'] = False
                error_msg = scrape_result.error_message if hasattr(scrape_result, 'error_message') else "未知错误"
                result['errors'].append(f"ERP数据抓取失败: {error_msg}")
                print(f"❌ ERP数据抓取失败: {error_msg}")

        except Exception as e:
            result['success'] = False
            result['errors'].append(f"测试异常: {str(e)}")
            print(f"❌ 测试异常: {e}")

        result['end_time'] = time.time()
        return result

    async def test_all_scenarios(self) -> List[Dict[str, Any]]:
        """测试所有场景"""
        print(f"\n📋 开始测试 {len(self.test_cases)} 个场景")
        print("=" * 80)

        results = []
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n[{i}/{len(self.test_cases)}] 测试场景")
            result = await self._test_single_scenario(test_case)
            results.append(result)
            
            # 短暂休息，避免过于频繁的请求
            if i < len(self.test_cases):
                print("⏸️ 休息 2 秒...")
                await asyncio.sleep(2)

        self.test_results = results
        return results

    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        if not self.test_results:
            return {"error": "没有测试结果"}

        report = {
            'summary': {
                'total_tests': len(self.test_results),
                'successful_tests': 0,
                'failed_tests': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'average_completeness_score': 0.0,
                'average_quality_score': 0.0
            },
            'scenarios': [],
            'performance_analysis': {},
            'data_quality_analysis': {},
            'recommendations': []
        }

        total_execution_time = 0
        total_completeness_score = 0
        total_quality_score = 0
        completeness_count = 0
        quality_count = 0

        for result in self.test_results:
            # 统计成功/失败
            if result['success']:
                report['summary']['successful_tests'] += 1
            else:
                report['summary']['failed_tests'] += 1

            # 统计执行时间
            if 'performance' in result and 'execution_time' in result['performance']:
                total_execution_time += result['performance']['execution_time']

            # 统计完整性和质量分数
            if 'validation' in result:
                if 'completeness' in result['validation']:
                    total_completeness_score += result['validation']['completeness']['completeness_score']
                    completeness_count += 1
                
                if 'quality' in result['validation']:
                    total_quality_score += result['validation']['quality']['quality_score']
                    quality_count += 1

            # 添加场景详情
            scenario_summary = {
                'test_id': result['test_id'],
                'test_name': result['test_name'],
                'success': result['success'],
                'execution_time': result.get('performance', {}).get('execution_time', 0),
                'completeness_score': result.get('validation', {}).get('completeness', {}).get('completeness_score', 0),
                'quality_score': result.get('validation', {}).get('quality', {}).get('quality_score', 0),
                'errors': result.get('errors', [])
            }
            report['scenarios'].append(scenario_summary)

        # 计算平均值
        total_tests = len(self.test_results)
        if total_tests > 0:
            report['summary']['success_rate'] = (report['summary']['successful_tests'] / total_tests) * 100
            report['summary']['average_execution_time'] = total_execution_time / total_tests

        if completeness_count > 0:
            report['summary']['average_completeness_score'] = total_completeness_score / completeness_count

        if quality_count > 0:
            report['summary']['average_quality_score'] = total_quality_score / quality_count

        # 性能分析
        execution_times = [r.get('performance', {}).get('execution_time', 0) for r in self.test_results if r.get('performance', {}).get('execution_time')]
        if execution_times:
            report['performance_analysis'] = {
                'min_time': min(execution_times),
                'max_time': max(execution_times),
                'avg_time': sum(execution_times) / len(execution_times),
                'total_time': sum(execution_times)
            }

        # 生成建议
        if report['summary']['success_rate'] < 80:
            report['recommendations'].append("成功率较低，建议检查ERP插件检测逻辑")
        
        if report['summary']['average_completeness_score'] < 70:
            report['recommendations'].append("数据完整性较低，建议增强字段提取逻辑")
        
        if report['summary']['average_quality_score'] < 80:
            report['recommendations'].append("数据质量较低，建议改进数据验证和清洗逻辑")

        if report['summary']['average_execution_time'] > 10:
            report['recommendations'].append("执行时间较长，建议优化性能")

        return report

    def print_test_report(self, report: Dict[str, Any]):
        """打印测试报告"""
        print("\n" + "=" * 80)
        print("📊 ERP插件增强测试报告")
        print("=" * 80)

        # 总结
        summary = report['summary']
        print(f"\n📋 测试总结:")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  成功测试: {summary['successful_tests']}")
        print(f"  失败测试: {summary['failed_tests']}")
        print(f"  成功率: {summary['success_rate']:.1f}%")
        print(f"  平均执行时间: {summary['average_execution_time']:.2f}秒")
        print(f"  平均完整性分数: {summary['average_completeness_score']:.1f}%")
        print(f"  平均质量分数: {summary['average_quality_score']:.1f}%")

        # 场景详情
        print(f"\n📋 场景详情:")
        for scenario in report['scenarios']:
            status = "✅" if scenario['success'] else "❌"
            print(f"  {status} {scenario['test_name']}")
            print(f"    执行时间: {scenario['execution_time']:.2f}秒")
            print(f"    完整性: {scenario['completeness_score']:.1f}%")
            print(f"    质量: {scenario['quality_score']:.1f}%")
            if scenario['errors']:
                print(f"    错误: {scenario['errors']}")

        # 性能分析
        if 'performance_analysis' in report and report['performance_analysis']:
            perf = report['performance_analysis']
            print(f"\n⚡ 性能分析:")
            print(f"  最快时间: {perf['min_time']:.2f}秒")
            print(f"  最慢时间: {perf['max_time']:.2f}秒")
            print(f"  平均时间: {perf['avg_time']:.2f}秒")
            print(f"  总耗时: {perf['total_time']:.2f}秒")

        # 建议
        if report['recommendations']:
            print(f"\n💡 改进建议:")
            for i, recommendation in enumerate(report['recommendations'], 1):
                print(f"  {i}. {recommendation}")

    async def run_enhanced_tests(self) -> bool:
        """运行增强测试"""
        try:
            await self.setup()
            
            # 运行所有场景测试
            results = await self.test_all_scenarios()
            
            # 生成并显示报告
            report = self.generate_test_report()
            self.print_test_report(report)
            
            # 判断整体是否成功
            success_rate = report['summary']['success_rate']
            return success_rate >= 75  # 75%以上成功率认为通过
            
        except Exception as e:
            print(f"❌ 增强测试执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.teardown()


async def main():
    """主函数"""
    print("🚀 启动 ERP插件增强测试套件")
    
    tester = ErpPluginEnhancedTester()
    
    try:
        success = await tester.run_enhanced_tests()
        
        if success:
            print("\n🎉 ERP插件增强测试通过！")
            return 0
        else:
            print("\n❌ ERP插件增强测试失败！")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # 运行增强测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


class TestErpPluginEnhanced(unittest.IsolatedAsyncioTestCase):
    """ERP插件增强单元测试"""
    
    async def asyncSetUp(self):
        """异步测试初始化"""
        self.tester = ErpPluginEnhancedTester()
        await self.tester.setup()
    
    async def asyncTearDown(self):
        """异步测试清理"""
        await self.tester.teardown()
    
    async def test_scenario_1_no_competitors(self):
        """测试场景1：无跟卖店铺"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_1_no_competitors'), None)
        self.assertIsNotNone(test_case, "未找到场景1测试用例")
        
        result = await self.tester._test_single_scenario(test_case)
        self.assertTrue(result['success'], f"场景1测试失败: {result.get('errors', [])}")
    
    async def test_scenario_2_with_competitors(self):
        """测试场景2：有跟卖店铺"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_2_with_competitors'), None)
        self.assertIsNotNone(test_case, "未找到场景2测试用例")
        
        result = await self.tester._test_single_scenario(test_case)
        self.assertTrue(result['success'], f"场景2测试失败: {result.get('errors', [])}")
    
    async def test_scenario_3_many_competitors(self):
        """测试场景3：大量跟卖店铺"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_3_many_competitors'), None)
        self.assertIsNotNone(test_case, "未找到场景3测试用例")
        
        result = await self.tester._test_single_scenario(test_case)
        self.assertTrue(result['success'], f"场景3测试失败: {result.get('errors', [])}")
    
    async def test_scenario_4_product_1176594312(self):
        """测试场景4：特定商品ID"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_4_product_1176594312'), None)
        self.assertIsNotNone(test_case, "未找到场景4测试用例")
        
        result = await self.tester._test_single_scenario(test_case)
        self.assertTrue(result['success'], f"场景4测试失败: {result.get('errors', [])}")
    
    async def test_all_scenarios_batch(self):
        """批量测试所有场景"""
        results = await self.tester.test_all_scenarios()
        
        # 验证至少有一些测试成功
        successful_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        success_rate = (successful_count / total_count) * 100 if total_count > 0 else 0
        
        self.assertGreater(success_rate, 50, f"成功率过低: {success_rate:.1f}% ({successful_count}/{total_count})")
        
        # 验证每个测试都有基本的结果结构
        for result in results:
            self.assertIn('test_id', result)
            self.assertIn('success', result)
            self.assertIn('erp_data', result)
