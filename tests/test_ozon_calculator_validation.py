#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OZON利润计算器验证测试
验证计算器逻辑与商品.xlsx中的利润计算结果是否一致
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from playweight.scenes.ozon_calculator import OzonCalculator, ProductInfo

class TestOzonCalculatorValidation(unittest.TestCase):
    """OZON计算器验证测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 初始化计算器，使用默认配置（内置测试数据）
        products_file = os.path.join(os.path.dirname(__file__), 'resources', '商品.xlsx')

        try:
            # 尝试使用默认初始化
            cls.calculator = OzonCalculator()
            channel_summary = cls.calculator.get_channel_summary()
            print(f"✅ 成功初始化计算器（使用Excel数据）")
            print(f"📊 加载了 {sum(channel_summary.values())} 个物流渠道")
            for provider, count in channel_summary.items():
                print(f"  {provider}: {count} 个渠道")
        except Exception as e:
            print(f"⚠️ Excel文件加载失败，创建内置测试数据: {e}")
            # 创建带有内置测试数据的计算器
            cls.calculator = cls._create_test_calculator()
            if cls.calculator:
                channel_summary = cls.calculator.get_channel_summary()
                print(f"✅ 成功创建测试计算器")
                print(f"📊 加载了 {sum(channel_summary.values())} 个物流渠道")
                for provider, count in channel_summary.items():
                    print(f"  {provider}: {count} 个渠道")
            else:
                print(f"❌ 创建测试计算器失败")
                cls.calculator = None
        
        # 读取商品数据
        try:
            cls.products_df = pd.read_excel(products_file)
            print(f"📦 成功加载商品数据: {len(cls.products_df)} 个商品")
        except Exception as e:
            print(f"❌ 加载商品数据失败: {e}")
            cls.products_df = None
        
        # 汇率设置（人民币转卢布）
        cls.exchange_rate = 13.5  # 1人民币 = 13.5卢布
        
        # 比较容差
        cls.profit_tolerance = 0.01  # 利润容差（元）
        cls.margin_tolerance = 0.001  # 利润率容差（0.1%）
    
    @classmethod
    def _create_test_calculator(cls):
        """创建带有内置测试数据的计算器"""
        try:
            from playweight.scenes.ozon_calculator import LogisticsChannel

            # 创建一个空的计算器实例
            calculator = OzonCalculator.__new__(OzonCalculator)
            calculator.excel_path = "test_data"
            calculator.channels = {}
            calculator.exchange_rate = 13.5

            # 手动添加测试渠道
            test_channels = [
                LogisticsChannel(
                    name="CEL Express Economy",
                    service_level="经济快递",
                    base_fee=16.0,
                    weight_fee=0.045,
                    weight_unit="g",
                    max_weight_kg=2.0,
                    max_value_rub=7000,
                    max_dimensions=150,
                    max_single_side=60,
                    delivery_days="5-10天"
                ),
                LogisticsChannel(
                    name="CEL Standard",
                    service_level="标准快递",
                    base_fee=25.0,
                    weight_fee=0.035,
                    weight_unit="g",
                    max_weight_kg=5.0,
                    max_value_rub=15000,
                    max_dimensions=200,
                    max_single_side=80,
                    delivery_days="3-7天"
                ),
                LogisticsChannel(
                    name="GUOO Budget",
                    service_level="低客单标准件",
                    base_fee=20.0,
                    weight_fee=0.040,
                    weight_unit="g",
                    max_weight_kg=25.0,
                    max_value_rub=1500,
                    max_dimensions=180,
                    max_single_side=70,
                    delivery_days="7-15天"
                ),
                LogisticsChannel(
                    name="GUOO Small",
                    service_level="轻小件",
                    base_fee=18.0,
                    weight_fee=0.050,
                    weight_unit="g",
                    max_weight_kg=2.0,
                    max_value_rub=7000,
                    max_dimensions=160,
                    max_single_side=65,
                    delivery_days="5-12天"
                )
            ]

            # 将测试渠道添加到计算器
            calculator.channels = {
                "CEL": [test_channels[0], test_channels[1]],
                "GUOO": [test_channels[2], test_channels[3]]
            }

            return calculator

        except Exception as e:
            print(f"创建测试计算器失败: {e}")
            return None

    def parse_dimensions(self, dimensions_str: str) -> str:
        """
        解析尺寸字符串
        输入: "长:120.1,宽:20.0,高:10.1"
        输出: "120.1x20.0x10.1"
        """
        if pd.isna(dimensions_str) or not dimensions_str:
            return "0x0x0"
        
        try:
            # 提取数字
            import re
            numbers = re.findall(r'[\d.]+', str(dimensions_str))
            if len(numbers) >= 3:
                return f"{numbers[0]}x{numbers[1]}x{numbers[2]}"
            else:
                return "0x0x0"
        except:
            return "0x0x0"
    
    def create_product_info(self, row: pd.Series) -> ProductInfo:
        """
        从商品数据行创建ProductInfo对象
        """
        # 处理缺失值
        def safe_float(value, default=0.0):
            if pd.isna(value):
                return default
            try:
                return float(value)
            except:
                return default
        
        # 创建ProductInfo对象
        product = ProductInfo(
            sku=str(row.get('ozon产品SKU', 'UNKNOWN')),
            weight_kg=safe_float(row.get('ozon重量（kg）'), 0.1),
            dimensions_cm=self.parse_dimensions(row.get('ozon尺寸', '')),
            ozon_price_rub=safe_float(row.get('ozon平台售价（¥）')) * self.exchange_rate,  # 人民币转卢布
            purchase_price_cny=safe_float(row.get('1688拿货成本（¥）')),
            exchange_rate=self.exchange_rate
        )
        
        return product
    
    def compare_results(self, calculated_result, expected_profit: float, expected_margin: float) -> Dict:
        """
        比较计算结果与期望结果
        """
        # 处理缺失值
        if pd.isna(expected_profit):
            expected_profit = 0.0
        if pd.isna(expected_margin):
            expected_margin = 0.0
        
        # 计算差异
        profit_diff = abs(calculated_result.profit_cny - expected_profit)
        margin_diff = abs(calculated_result.profit_margin / 100 - expected_margin)  # 转换为小数
        
        # 判断是否匹配
        profit_match = profit_diff <= self.profit_tolerance
        margin_match = margin_diff <= self.margin_tolerance
        
        return {
            'profit_match': profit_match,
            'margin_match': margin_match,
            'profit_diff': profit_diff,
            'margin_diff': margin_diff,
            'calculated_profit': calculated_result.profit_cny,
            'expected_profit': expected_profit,
            'calculated_margin': calculated_result.profit_margin / 100,
            'expected_margin': expected_margin,
            'best_channel': calculated_result.best_channel,
            'warnings': calculated_result.warnings
        }
    
    def test_calculator_validation(self):
        """主要验证测试"""
        if self.calculator is None or self.products_df is None:
            self.skipTest("计算器或商品数据未正确加载")
        
        print(f"\n🔍 开始验证前100个商品的利润计算...")
        
        # 选择前100个商品进行测试
        test_products = self.products_df.head(100)
        
        results = []
        success_count = 0
        error_count = 0
        
        for index, row in test_products.iterrows():
            try:
                # 创建商品信息
                product = self.create_product_info(row)
                
                # 计算利润
                calculated_result = self.calculator.calculate_profit(product)
                
                # 获取期望结果
                expected_profit = row.get('利润', 0.0)
                expected_margin = row.get('利润率', 0.0)
                
                # 比较结果
                comparison = self.compare_results(calculated_result, expected_profit, expected_margin)
                
                # 记录结果
                result = {
                    'index': index,
                    'sku': product.sku,
                    'product_name': row.get('ozon产品名称', 'Unknown')[:50] + '...',
                    **comparison
                }
                results.append(result)
                
                # 统计成功率
                if comparison['profit_match'] and comparison['margin_match']:
                    success_count += 1
                else:
                    error_count += 1
                    # 打印不匹配的详细信息
                    print(f"❌ 商品 {product.sku}: 利润差异={comparison['profit_diff']:.2f}, 利润率差异={comparison['margin_diff']:.3f}")
                
            except Exception as e:
                error_count += 1
                print(f"❌ 处理商品 {index} 时出错: {e}")
                results.append({
                    'index': index,
                    'sku': 'ERROR',
                    'error': str(e)
                })
        
        # 输出统计结果
        total_count = len(results)
        success_rate = success_count / total_count * 100 if total_count > 0 else 0
        
        print(f"\n📊 验证结果统计:")
        print(f"总商品数: {total_count}")
        print(f"计算成功: {success_count}")
        print(f"计算失败: {error_count}")
        print(f"成功率: {success_rate:.1f}%")
        
        # 详细分析
        if results:
            profit_diffs = [r.get('profit_diff', 0) for r in results if 'profit_diff' in r]
            margin_diffs = [r.get('margin_diff', 0) for r in results if 'margin_diff' in r]
            
            if profit_diffs:
                print(f"\n📈 利润差异分析:")
                print(f"平均差异: {np.mean(profit_diffs):.2f}元")
                print(f"最大差异: {np.max(profit_diffs):.2f}元")
                print(f"标准差: {np.std(profit_diffs):.2f}元")
            
            if margin_diffs:
                print(f"\n📉 利润率差异分析:")
                print(f"平均差异: {np.mean(margin_diffs):.3f} ({np.mean(margin_diffs)*100:.1f}%)")
                print(f"最大差异: {np.max(margin_diffs):.3f} ({np.max(margin_diffs)*100:.1f}%)")
                print(f"标准差: {np.std(margin_diffs):.3f}")
        
        # 保存详细结果到文件
        self.save_validation_results(results)
        
        # 断言测试结果
        self.assertGreater(success_rate, 80, f"计算成功率 {success_rate:.1f}% 低于80%，可能存在计算逻辑问题")
        
        return results
    
    def save_validation_results(self, results: List[Dict]):
        """保存验证结果到文件"""
        try:
            results_file = os.path.join(os.path.dirname(__file__), 'resources', 'validation_results.xlsx')
            
            # 转换为DataFrame
            df_results = pd.DataFrame(results)
            
            # 保存到Excel
            df_results.to_excel(results_file, index=False)
            print(f"💾 验证结果已保存到: {results_file}")
            
        except Exception as e:
            print(f"⚠️ 保存验证结果失败: {e}")
    
    def test_sample_products(self):
        """测试几个样本商品的详细计算过程"""
        if self.calculator is None or self.products_df is None:
            self.skipTest("计算器或商品数据未正确加载")
        
        print(f"\n🔬 详细分析前5个商品的计算过程...")
        
        for i in range(min(5, len(self.products_df))):
            row = self.products_df.iloc[i]
            
            print(f"\n--- 商品 {i+1} ---")
            print(f"SKU: {row.get('ozon产品SKU')}")
            print(f"名称: {row.get('ozon产品名称', '')[:50]}...")
            print(f"售价: {row.get('ozon平台售价（¥）')}元")
            print(f"成本: {row.get('1688拿货成本（¥）')}元")
            print(f"重量: {row.get('ozon重量（kg）')}kg")
            print(f"尺寸: {row.get('ozon尺寸')}")
            
            try:
                # 创建商品信息并计算
                product = self.create_product_info(row)
                result = self.calculator.calculate_profit(product)
                
                print(f"计算结果:")
                print(f"  分类: {result.category.value}")
                print(f"  最佳渠道: {result.best_channel}")
                print(f"  物流费用: {result.shipping_cost_cny:.2f}元")
                print(f"  计算利润: {result.profit_cny:.2f}元")
                print(f"  计算利润率: {result.profit_margin:.1f}%")
                
                print(f"期望结果:")
                print(f"  期望利润: {row.get('利润', 'N/A')}元")
                print(f"  期望利润率: {row.get('利润率', 'N/A')}")
                
                if result.warnings:
                    print(f"  警告: {result.warnings}")
                
            except Exception as e:
                print(f"  ❌ 计算失败: {e}")

def run_validation_test():
    """运行验证测试"""
    print("🚀 开始OZON计算器验证测试...")
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOzonCalculatorValidation)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # 运行验证测试
    success = run_validation_test()
    
    if success:
        print("\n✅ 所有验证测试通过！")
    else:
        print("\n❌ 验证测试失败，请检查计算逻辑！")
        sys.exit(1)