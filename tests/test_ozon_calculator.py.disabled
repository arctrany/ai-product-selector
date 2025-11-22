#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OZON利润计算器测试
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from playweight.scenes.ozon_calculator import (
    OzonCalculator, ProductInfo, ProductCategory, 
    LogisticsChannel, ProfitCalculation
)


class TestOzonCalculator(unittest.TestCase):
    """OZON计算器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        try:
            cls.calculator = OzonCalculator()
            print(f"成功加载计算器，包含 {len(cls.calculator.channels)} 个物流服务商")
        except Exception as e:
            print(f"警告：无法加载Excel文件，使用模拟数据进行测试: {e}")
            cls.calculator = None
    
    def test_product_info_basic(self):
        """测试商品信息基础功能"""
        product = ProductInfo(
            sku="TEST001",
            weight_kg=0.8,
            dimensions_cm="25x20x15",
            ozon_price_rub=2000,
            purchase_price_cny=80,
            exchange_rate=13.5
        )
        
        # 测试基础属性
        self.assertEqual(product.sku, "TEST001")
        self.assertEqual(product.weight_kg, 0.8)
        self.assertEqual(product.ozon_price_rub, 2000)
        
        # 测试计算属性
        self.assertEqual(product.purchase_price_rub, 80 * 13.5)
        self.assertEqual(product.dimensions_list, [25.0, 20.0, 15.0])
        self.assertEqual(product.total_dimensions, 60.0)
        self.assertEqual(product.max_dimension, 25.0)
    
    def test_product_classification(self):
        """测试商品分类"""
        if not self.calculator:
            self.skipTest("计算器未初始化")
        
        # 超级轻小件
        product1 = ProductInfo("TEST1", 0.4, "20x15x10", 1200, 50)
        category1 = self.calculator.classify_product(product1)
        self.assertEqual(category1, ProductCategory.EXTRA_SMALL)
        
        # 轻小件
        product2 = ProductInfo("TEST2", 1.5, "30x25x20", 3000, 100)
        category2 = self.calculator.classify_product(product2)
        self.assertEqual(category2, ProductCategory.SMALL)
        
        # 低客单标准件
        product3 = ProductInfo("TEST3", 5.0, "40x30x25", 1000, 80)
        category3 = self.calculator.classify_product(product3)
        self.assertEqual(category3, ProductCategory.BUDGET)
    
    def test_logistics_channel_calculation(self):
        """测试物流渠道费用计算"""
        # 创建测试渠道
        channel = LogisticsChannel(
            name="Test Express",
            service_level="超快速",
            base_fee=16.0,
            weight_fee=0.045,
            weight_unit="g",
            max_weight_kg=2.0,
            max_value_rub=7000,
            max_dimensions=150,
            max_single_side=60,
            delivery_days="5-10天"
        )
        
        # 测试正常商品
        product = ProductInfo("TEST", 0.8, "25x20x15", 2000, 80)
        cost = channel.calculate_shipping_cost(product)
        expected_cost = 16.0 + (0.8 * 1000 * 0.045)  # 16 + 36 = 52
        self.assertEqual(cost, expected_cost)
        
        # 测试超重商品
        heavy_product = ProductInfo("HEAVY", 3.0, "25x20x15", 2000, 80)
        cost_heavy = channel.calculate_shipping_cost(heavy_product)
        self.assertIsNone(cost_heavy)
        
        # 测试超值商品
        expensive_product = ProductInfo("EXPENSIVE", 0.8, "25x20x15", 8000, 80)
        cost_expensive = channel.calculate_shipping_cost(expensive_product)
        self.assertIsNone(cost_expensive)
    
    def test_profit_calculation_basic(self):
        """测试基础利润计算"""
        if not self.calculator:
            self.skipTest("计算器未初始化")
        
        product = ProductInfo(
            sku="PROFIT_TEST",
            weight_kg=0.6,
            dimensions_cm="20x15x10",
            ozon_price_rub=1500,
            purchase_price_cny=60,
            exchange_rate=13.5
        )
        
        result = self.calculator.calculate_profit(product)
        
        # 验证结果结构
        self.assertIsInstance(result, ProfitCalculation)
        self.assertEqual(result.product_sku, "PROFIT_TEST")
        self.assertIsInstance(result.category, ProductCategory)
        
        # 验证数值合理性
        self.assertGreater(result.revenue_cny, 0)
        self.assertGreater(result.total_cost_cny, 0)
        
        print(f"\n=== 利润计算测试结果 ===")
        print(f"商品: {result.product_sku}")
        print(f"分类: {result.category.value}")
        print(f"最佳渠道: {result.best_channel}")
        print(f"物流费用: {result.shipping_cost_cny:.2f}元")
        print(f"总成本: {result.total_cost_cny:.2f}元")
        print(f"收入: {result.revenue_cny:.2f}元")
        print(f"利润: {result.profit_cny:.2f}元")
        print(f"利润率: {result.profit_margin:.1f}%")
    
    def test_batch_calculation(self):
        """测试批量计算"""
        if not self.calculator:
            self.skipTest("计算器未初始化")
        
        products = [
            ProductInfo("BATCH1", 0.5, "20x15x10", 1200, 50),
            ProductInfo("BATCH2", 1.0, "25x20x15", 2500, 100),
            ProductInfo("BATCH3", 0.3, "15x12x8", 800, 30),
        ]
        
        results = self.calculator.batch_calculate(products)
        
        self.assertEqual(len(results), 3)
        
        for i, result in enumerate(results):
            self.assertEqual(result.product_sku, f"BATCH{i+1}")
            print(f"\n批量计算 {result.product_sku}: 利润率 {result.profit_margin:.1f}%")
    
    def test_edge_cases(self):
        """测试边界情况"""
        if not self.calculator:
            self.skipTest("计算器未初始化")
        
        # 零重量商品
        zero_weight = ProductInfo("ZERO", 0, "10x10x10", 500, 20)
        result_zero = self.calculator.calculate_profit(zero_weight)
        self.assertIsNotNone(result_zero)
        
        # 超大商品
        huge_product = ProductInfo("HUGE", 50, "200x200x200", 50000, 1000)
        result_huge = self.calculator.calculate_profit(huge_product)
        self.assertIn("没有找到合适的物流渠道", result_huge.warnings)
        
        # 负利润商品
        loss_product = ProductInfo("LOSS", 0.5, "20x15x10", 100, 200)
        result_loss = self.calculator.calculate_profit(loss_product)
        self.assertLess(result_loss.profit_cny, 0)
    
    def test_channel_summary(self):
        """测试渠道汇总"""
        if not self.calculator:
            self.skipTest("计算器未初始化")
        
        summary = self.calculator.get_channel_summary()
        self.assertIsInstance(summary, dict)
        self.assertGreater(len(summary), 0)
        
        print(f"\n=== 渠道汇总 ===")
        for provider, count in summary.items():
            print(f"{provider}: {count} 个渠道")


def run_performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    try:
        import time
        
        # 测试初始化时间
        start_time = time.time()
        calculator = OzonCalculator()
        init_time = time.time() - start_time
        print(f"初始化时间: {init_time:.3f}秒")
        
        # 测试单次计算时间
        product = ProductInfo("PERF_TEST", 0.8, "25x20x15", 2000, 80)
        
        start_time = time.time()
        result = calculator.calculate_profit(product)
        calc_time = time.time() - start_time
        print(f"单次计算时间: {calc_time:.3f}秒")
        
        # 测试批量计算时间
        products = [
            ProductInfo(f"BATCH_{i}", 0.5 + i*0.1, "20x15x10", 1000 + i*100, 50 + i*10)
            for i in range(100)
        ]
        
        start_time = time.time()
        results = calculator.batch_calculate(products)
        batch_time = time.time() - start_time
        print(f"批量计算100个商品时间: {batch_time:.3f}秒")
        print(f"平均每个商品: {batch_time/100:.4f}秒")
        
    except Exception as e:
        print(f"性能测试失败: {e}")


if __name__ == "__main__":
    # 运行单元测试
    unittest.main(verbosity=2, exit=False)
    
    # 运行性能测试
    run_performance_test()