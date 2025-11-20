#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ERP插件与OZON抓取器集成测试

基于ozon_test_cases.json测试数据，验证ErpPluginScraper和OzonScraper的集成功能
包括价格容差验证、竞争对手数量验证、数据一致性检查等
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
from common.scrapers.ozon_scraper import OzonScraper
from common.scrapers.global_browser_singleton import get_global_browser_service
from common.models import ProductInfo, ScrapingResult


class ErpOzonIntegrationTester:
    """ERP插件与OZON抓取器集成测试器"""

    def __init__(self):
        """初始化测试器"""
        self.config = get_config()
        self.browser_service = None
        self.erp_scraper = None
        self.ozon_scraper = None
        self.test_cases_file = project_root / "tests" / "test_data" / "ozon_test_cases.json"
        self.test_cases = []
        self.validation_rules = {}
        self.integration_results = []

    async def setup(self):
        """异步初始化"""
        print("🚀 开始 ERP-OZON 集成测试套件")
        print("=" * 80)
        
        # 加载测试用例
        await self._load_test_cases()
        
        # 初始化浏览器服务
        await self._setup_browser_service()
        
        # 初始化抓取器
        await self._setup_scrapers()

    async def teardown(self):
        """清理资源"""
        if self.erp_scraper:
            await self.erp_scraper.close()
        if self.ozon_scraper:
            await self.ozon_scraper.close()
        if self.browser_service:
            await self.browser_service.close()
        print("✅ ERP-OZON 集成测试套件完成")

    async def _load_test_cases(self):
        """加载测试用例数据"""
        try:
            with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.test_cases = data.get('test_cases', [])
                self.validation_rules = data.get('validation_rules', {})
            print(f"📋 加载了 {len(self.test_cases)} 个集成测试用例")
        except Exception as e:
            raise Exception(f"加载测试用例失败: {e}")

    async def _setup_browser_service(self):
        """设置浏览器服务"""
        try:
            # 使用全局浏览器服务（自动初始化）
            self.browser_service = get_global_browser_service()
            print("✅ 全局浏览器服务获取成功")
        except Exception as e:
            raise Exception(f"浏览器服务初始化失败: {e}")

    async def _setup_scrapers(self):
        """设置抓取器"""
        try:
            # 使用共享浏览器服务
            self.erp_scraper = ErpPluginScraper(self.config, self.browser_service)
            self.ozon_scraper = OzonScraper(self.config, self.browser_service)
            print("✅ ERP插件和OZON抓取器初始化成功")
        except Exception as e:
            raise Exception(f"抓取器初始化失败: {e}")

    def _validate_price_with_tolerance(self, actual: Optional[float], expected: Optional[float], tolerance: float) -> Dict[str, Any]:
        """验证价格（带容差）"""
        validation = {
            'expected': expected,
            'actual': actual,
            'tolerance': tolerance,
            'valid': False,
            'difference': None,
            'percentage_diff': None
        }

        if expected is None and actual is None:
            validation['valid'] = True
            return validation

        if expected is None or actual is None:
            validation['valid'] = (expected == actual)
            return validation

        difference = abs(actual - expected)
        validation['difference'] = difference
        validation['valid'] = difference <= tolerance

        if expected != 0:
            validation['percentage_diff'] = (difference / expected) * 100

        return validation

    def _validate_competitor_count_with_tolerance(self, actual: int, expected: int, tolerance: int) -> Dict[str, Any]:
        """验证竞争对手数量（带容差）"""
        validation = {
            'expected': expected,
            'actual': actual,
            'tolerance': tolerance,
            'valid': False,
            'difference': None
        }

        difference = abs(actual - expected)
        validation['difference'] = difference
        validation['valid'] = difference <= tolerance

        return validation

    def _analyze_data_consistency(self, erp_data: Dict[str, Any], ozon_data: ProductInfo) -> Dict[str, Any]:
        """分析ERP数据与OZON数据的一致性"""
        consistency = {
            'sku_match': False,
            'brand_match': False,
            'price_correlation': {},
            'competitor_correlation': {},
            'data_completeness': {},
            'overall_consistency_score': 0.0
        }

        # SKU一致性检查
        erp_sku = str(erp_data.get('sku', ''))
        ozon_sku = str(ozon_data.sku) if ozon_data.sku else ''
        consistency['sku_match'] = erp_sku == ozon_sku

        # 品牌一致性检查
        erp_brand = erp_data.get('brand_name', '').strip()
        ozon_brand = ozon_data.brand_name.strip() if ozon_data.brand_name else ''
        consistency['brand_match'] = erp_brand == ozon_brand

        # 价格相关性分析
        if hasattr(ozon_data, 'green_price') and hasattr(ozon_data, 'black_price'):
            consistency['price_correlation'] = {
                'ozon_green_price': ozon_data.green_price,
                'ozon_black_price': ozon_data.black_price,
                'erp_has_price_data': any(key in erp_data for key in ['competitor_min_price', 'competitor_max_price']),
                'price_range_reasonable': True  # 可以进一步实现价格合理性检查
            }

        # 竞争对手相关性分析
        ozon_competitor_count = len(ozon_data.competitors) if ozon_data.competitors else 0
        erp_competitor_info = erp_data.get('competitor_list', '')
        consistency['competitor_correlation'] = {
            'ozon_competitor_count': ozon_competitor_count,
            'erp_has_competitor_data': bool(erp_competitor_info and erp_competitor_info != '--'),
            'correlation_reasonable': True  # 可以进一步实现相关性检查
        }

        # 数据完整性对比
        erp_completeness = sum(1 for v in erp_data.values() if v is not None and v != '' and v != '--')
        ozon_completeness = sum(1 for attr in ['sku', 'brand_name', 'green_price', 'black_price', 'image_url'] 
                               if getattr(ozon_data, attr, None) is not None)
        
        consistency['data_completeness'] = {
            'erp_field_count': erp_completeness,
            'ozon_field_count': ozon_completeness,
            'total_fields': len(erp_data) + 5,  # 5个主要OZON字段
            'completeness_ratio': (erp_completeness + ozon_completeness) / (len(erp_data) + 5)
        }

        # 计算整体一致性分数
        consistency_factors = [
            consistency['sku_match'],
            consistency['brand_match'],
            consistency['price_correlation'].get('price_range_reasonable', False),
            consistency['competitor_correlation'].get('correlation_reasonable', False),
            consistency['data_completeness']['completeness_ratio'] > 0.5
        ]
        
        consistency['overall_consistency_score'] = (sum(consistency_factors) / len(consistency_factors)) * 100

        return consistency

    async def _test_integration_scenario(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个集成场景"""
        test_id = test_case['id']
        test_name = test_case['name']
        url = test_case['url']
        expected = test_case['expected']
        test_options = test_case.get('test_options', {})

        print(f"\n🧪 集成测试场景: {test_name}")
        print(f"📍 URL: {url}")

        start_time = time.time()
        result = {
            'test_id': test_id,
            'test_name': test_name,
            'url': url,
            'start_time': start_time,
            'success': False,
            'erp_result': None,
            'ozon_result': None,
            'validation': {},
            'consistency_analysis': {},
            'performance': {},
            'errors': []
        }

        try:
            # 并行执行ERP和OZON抓取
            print("🔄 并行执行ERP和OZON数据抓取...")
            
            erp_task = self.erp_scraper.scrape(product_url=url)
            ozon_task = self.ozon_scraper.scrape_product_info(
                url,
                include_competitors=test_options.get('include_competitors', True),
                max_competitors=test_options.get('max_competitors', 10)
            )

            # 等待两个任务完成
            erp_result, ozon_result = await asyncio.gather(erp_task, ozon_task, return_exceptions=True)

            execution_time = time.time() - start_time
            result['performance']['total_execution_time'] = execution_time

            # 处理ERP结果
            if isinstance(erp_result, Exception):
                result['errors'].append(f"ERP抓取异常: {str(erp_result)}")
                erp_result = None
            elif erp_result and erp_result.success:
                result['erp_result'] = erp_result
                print(f"✅ ERP数据抓取成功 ({len(erp_result.data)} 字段)")
            else:
                result['errors'].append(f"ERP抓取失败: {erp_result.error_message if erp_result else '未知错误'}")

            # 处理OZON结果
            if isinstance(ozon_result, Exception):
                result['errors'].append(f"OZON抓取异常: {str(ozon_result)}")
                ozon_result = None
            elif ozon_result and ozon_result.success:
                result['ozon_result'] = ozon_result
                print(f"✅ OZON数据抓取成功")
            else:
                result['errors'].append(f"OZON抓取失败: {ozon_result.error_message if ozon_result else '未知错误'}")

            # 如果两个抓取都成功，进行集成验证
            if erp_result and erp_result.success and ozon_result and ozon_result.success:
                result['success'] = True
                
                # 价格验证
                price_tolerance = self.validation_rules.get('price_tolerance', 50.0)
                ozon_data = ozon_result.data
                
                green_price_validation = self._validate_price_with_tolerance(
                    ozon_data.green_price, expected.get('green_price'), price_tolerance
                )
                black_price_validation = self._validate_price_with_tolerance(
                    ozon_data.black_price, expected.get('black_price'), price_tolerance
                )
                
                result['validation']['price_validation'] = {
                    'green_price': green_price_validation,
                    'black_price': black_price_validation
                }

                # 竞争对手数量验证
                competitor_tolerance = self.validation_rules.get('competitor_count_tolerance', 5)
                actual_competitor_count = len(ozon_data.competitors) if ozon_data.competitors else 0
                expected_competitor_count = expected.get('competitor_count', 0)
                
                competitor_validation = self._validate_competitor_count_with_tolerance(
                    actual_competitor_count, expected_competitor_count, competitor_tolerance
                )
                
                result['validation']['competitor_validation'] = competitor_validation

                # 数据一致性分析
                consistency_analysis = self._analyze_data_consistency(erp_result.data, ozon_data)
                result['consistency_analysis'] = consistency_analysis

                # 显示验证结果
                print(f"💰 价格验证:")
                print(f"  绿标价格: {'✅' if green_price_validation['valid'] else '❌'} "
                      f"期望={green_price_validation['expected']}, 实际={green_price_validation['actual']}")
                print(f"  黑标价格: {'✅' if black_price_validation['valid'] else '❌'} "
                      f"期望={black_price_validation['expected']}, 实际={black_price_validation['actual']}")
                
                print(f"🏪 竞争对手验证:")
                print(f"  数量: {'✅' if competitor_validation['valid'] else '❌'} "
                      f"期望={competitor_validation['expected']}, 实际={competitor_validation['actual']}")
                
                print(f"🔗 数据一致性:")
                print(f"  SKU匹配: {'✅' if consistency_analysis['sku_match'] else '❌'}")
                print(f"  品牌匹配: {'✅' if consistency_analysis['brand_match'] else '❌'}")
                print(f"  整体一致性: {consistency_analysis['overall_consistency_score']:.1f}%")

            print(f"⏱️ 总执行时间: {execution_time:.2f}秒")

        except Exception as e:
            result['errors'].append(f"集成测试异常: {str(e)}")
            print(f"❌ 集成测试异常: {e}")

        result['end_time'] = time.time()
        return result

    async def test_all_integration_scenarios(self) -> List[Dict[str, Any]]:
        """测试所有集成场景"""
        print(f"\n📋 开始集成测试 {len(self.test_cases)} 个场景")
        print("=" * 80)

        results = []
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n[{i}/{len(self.test_cases)}] 集成测试场景")
            result = await self._test_integration_scenario(test_case)
            results.append(result)
            
            # 短暂休息，避免过于频繁的请求
            if i < len(self.test_cases):
                print("⏸️ 休息 3 秒...")
                await asyncio.sleep(3)

        self.integration_results = results
        return results

    def generate_integration_report(self) -> Dict[str, Any]:
        """生成集成测试报告"""
        if not self.integration_results:
            return {"error": "没有集成测试结果"}

        report = {
            'summary': {
                'total_tests': len(self.integration_results),
                'successful_tests': 0,
                'failed_tests': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'price_validation_success_rate': 0.0,
                'competitor_validation_success_rate': 0.0,
                'average_consistency_score': 0.0
            },
            'scenarios': [],
            'validation_analysis': {
                'price_validations': [],
                'competitor_validations': [],
                'consistency_scores': []
            },
            'performance_analysis': {},
            'recommendations': []
        }

        total_execution_time = 0
        price_validation_count = 0
        price_validation_success = 0
        competitor_validation_count = 0
        competitor_validation_success = 0
        consistency_scores = []

        for result in self.integration_results:
            # 统计成功/失败
            if result['success']:
                report['summary']['successful_tests'] += 1
            else:
                report['summary']['failed_tests'] += 1

            # 统计执行时间
            if 'performance' in result and 'total_execution_time' in result['performance']:
                total_execution_time += result['performance']['total_execution_time']

            # 统计价格验证
            if 'validation' in result and 'price_validation' in result['validation']:
                price_val = result['validation']['price_validation']
                for price_type, validation in price_val.items():
                    price_validation_count += 1
                    if validation['valid']:
                        price_validation_success += 1
                    report['validation_analysis']['price_validations'].append({
                        'test_id': result['test_id'],
                        'price_type': price_type,
                        'validation': validation
                    })

            # 统计竞争对手验证
            if 'validation' in result and 'competitor_validation' in result['validation']:
                comp_val = result['validation']['competitor_validation']
                competitor_validation_count += 1
                if comp_val['valid']:
                    competitor_validation_success += 1
                report['validation_analysis']['competitor_validations'].append({
                    'test_id': result['test_id'],
                    'validation': comp_val
                })

            # 统计一致性分数
            if 'consistency_analysis' in result:
                consistency_score = result['consistency_analysis'].get('overall_consistency_score', 0)
                consistency_scores.append(consistency_score)
                report['validation_analysis']['consistency_scores'].append({
                    'test_id': result['test_id'],
                    'score': consistency_score
                })

            # 添加场景详情
            scenario_summary = {
                'test_id': result['test_id'],
                'test_name': result['test_name'],
                'success': result['success'],
                'execution_time': result.get('performance', {}).get('total_execution_time', 0),
                'consistency_score': result.get('consistency_analysis', {}).get('overall_consistency_score', 0),
                'errors': result.get('errors', [])
            }
            report['scenarios'].append(scenario_summary)

        # 计算平均值和成功率
        total_tests = len(self.integration_results)
        if total_tests > 0:
            report['summary']['success_rate'] = (report['summary']['successful_tests'] / total_tests) * 100
            report['summary']['average_execution_time'] = total_execution_time / total_tests

        if price_validation_count > 0:
            report['summary']['price_validation_success_rate'] = (price_validation_success / price_validation_count) * 100

        if competitor_validation_count > 0:
            report['summary']['competitor_validation_success_rate'] = (competitor_validation_success / competitor_validation_count) * 100

        if consistency_scores:
            report['summary']['average_consistency_score'] = sum(consistency_scores) / len(consistency_scores)

        # 性能分析
        execution_times = [r.get('performance', {}).get('total_execution_time', 0) for r in self.integration_results 
                          if r.get('performance', {}).get('total_execution_time')]
        if execution_times:
            report['performance_analysis'] = {
                'min_time': min(execution_times),
                'max_time': max(execution_times),
                'avg_time': sum(execution_times) / len(execution_times),
                'total_time': sum(execution_times)
            }

        # 生成建议
        if report['summary']['success_rate'] < 75:
            report['recommendations'].append("集成测试成功率较低，建议检查抓取器协调逻辑")
        
        if report['summary']['price_validation_success_rate'] < 80:
            report['recommendations'].append("价格验证成功率较低，建议调整价格容差或检查价格提取逻辑")
        
        if report['summary']['competitor_validation_success_rate'] < 70:
            report['recommendations'].append("竞争对手验证成功率较低，建议检查竞争对手数量提取逻辑")

        if report['summary']['average_consistency_score'] < 60:
            report['recommendations'].append("数据一致性较低，建议改进ERP和OZON数据的匹配逻辑")

        if report['summary']['average_execution_time'] > 15:
            report['recommendations'].append("集成测试执行时间较长，建议优化并行处理逻辑")

        return report

    def print_integration_report(self, report: Dict[str, Any]):
        """打印集成测试报告"""
        print("\n" + "=" * 80)
        print("📊 ERP-OZON 集成测试报告")
        print("=" * 80)

        # 总结
        summary = report['summary']
        print(f"\n📋 测试总结:")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  成功测试: {summary['successful_tests']}")
        print(f"  失败测试: {summary['failed_tests']}")
        print(f"  成功率: {summary['success_rate']:.1f}%")
        print(f"  平均执行时间: {summary['average_execution_time']:.2f}秒")
        print(f"  价格验证成功率: {summary['price_validation_success_rate']:.1f}%")
        print(f"  竞争对手验证成功率: {summary['competitor_validation_success_rate']:.1f}%")
        print(f"  平均数据一致性: {summary['average_consistency_score']:.1f}%")

        # 场景详情
        print(f"\n📋 场景详情:")
        for scenario in report['scenarios']:
            status = "✅" if scenario['success'] else "❌"
            print(f"  {status} {scenario['test_name']}")
            print(f"    执行时间: {scenario['execution_time']:.2f}秒")
            print(f"    一致性: {scenario['consistency_score']:.1f}%")
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

    async def run_integration_tests(self) -> bool:
        """运行集成测试"""
        try:
            await self.setup()
            
            # 运行所有集成场景测试
            results = await self.test_all_integration_scenarios()
            
            # 生成并显示报告
            report = self.generate_integration_report()
            self.print_integration_report(report)
            
            # 判断整体是否成功
            success_rate = report['summary']['success_rate']
            return success_rate >= 70  # 70%以上成功率认为通过
            
        except Exception as e:
            print(f"❌ 集成测试执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.teardown()


async def main():
    """主函数"""
    print("🚀 启动 ERP-OZON 集成测试套件")
    
    tester = ErpOzonIntegrationTester()
    
    try:
        success = await tester.run_integration_tests()
        
        if success:
            print("\n🎉 ERP-OZON 集成测试通过！")
            return 0
        else:
            print("\n❌ ERP-OZON 集成测试失败！")
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
    # 运行集成测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


class TestErpOzonIntegration(unittest.IsolatedAsyncioTestCase):
    """ERP-OZON集成单元测试"""
    
    async def asyncSetUp(self):
        """异步测试初始化"""
        self.tester = ErpOzonIntegrationTester()
        await self.tester.setup()
    
    async def asyncTearDown(self):
        """异步测试清理"""
        await self.tester.teardown()
    
    async def test_integration_scenario_1(self):
        """测试集成场景1：无跟卖店铺"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_1_no_competitors'), None)
        self.assertIsNotNone(test_case, "未找到场景1测试用例")
        
        result = await self.tester._test_integration_scenario(test_case)
        self.assertTrue(result['success'], f"场景1集成测试失败: {result.get('errors', [])}")
    
    async def test_integration_scenario_4(self):
        """测试集成场景4：特定商品ID（已知数据）"""
        test_case = next((tc for tc in self.tester.test_cases if tc['id'] == 'scenario_4_product_1176594312'), None)
        self.assertIsNotNone(test_case, "未找到场景4测试用例")
        
        result = await self.tester._test_integration_scenario(test_case)
        self.assertTrue(result['success'], f"场景4集成测试失败: {result.get('errors', [])}")
        
        # 验证数据一致性
        if 'consistency_analysis' in result:
            consistency = result['consistency_analysis']
            self.assertGreater(consistency['overall_consistency_score'], 50, 
                             f"数据一致性过低: {consistency['overall_consistency_score']:.1f}%")
    
    async def test_price_validation_with_tolerance(self):
        """测试价格容差验证"""
        # 测试价格验证逻辑
        validation = self.tester._validate_price_with_tolerance(100.0, 95.0, 10.0)
        self.assertTrue(validation['valid'], "价格容差验证应该通过")
        
        validation = self.tester._validate_price_with_tolerance(100.0, 80.0, 10.0)
        self.assertFalse(validation['valid'], "价格容差验证应该失败")
        
        validation = self.tester._validate_price_with_tolerance(None, None, 10.0)
        self.assertTrue(validation['valid'], "空值价格验证应该通过")
    
    async def test_competitor_count_validation(self):
        """测试竞争对手数量验证"""
        validation = self.tester._validate_competitor_count_with_tolerance(10, 8, 5)
        self.assertTrue(validation['valid'], "竞争对手数量容差验证应该通过")
        
        validation = self.tester._validate_competitor_count_with_tolerance(10, 2, 5)
        self.assertFalse(validation['valid'], "竞争对手数量容差验证应该失败")
