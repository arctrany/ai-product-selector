"""
Excel利润计算器单元测试

测试Excel利润计算器的各项功能，包括：
- 基本计算功能
- 路径处理
- 异常处理
- 性能测试
- 集成接口测试

Author: AI Assistant
Date: 2025-10-29
"""

import unittest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apps.xuanping.common.excel_calculator import (
    ExcelProfitCalculator,
    ProfitCalculatorInput,
    ProfitCalculatorResult,
    ExcelCalculatorError,
    calculate_profit_from_excel,
    batch_calculate_profits,
    quick_calculate,
    create_sample_excel_file,
    ProfitCalculatorService,
    get_default_service
)


class TestExcelProfitCalculator(unittest.TestCase):
    """Excel利润计算器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 使用用户指定的Excel文件路径
        cls.test_excel_path = Path.home() / 'Downloads' / 'profits.xlsx'
        
        # 确保测试Excel文件存在
        if not cls.test_excel_path.exists():

            create_sample_excel_file(cls.test_excel_path)
        
        print(f"使用测试Excel文件: {cls.test_excel_path}")
    
    def setUp(self):
        """每个测试方法前的初始化"""
        self.calculator = None
    
    def tearDown(self):
        """每个测试方法后的清理"""
        if self.calculator:
            self.calculator.close()
    
    def test_excel_file_initialization(self):
        """测试Excel文件初始化"""
        # 测试正常初始化
        self.calculator = ExcelProfitCalculator(self.test_excel_path)
        self.assertIsNotNone(self.calculator.workbook)
        self.assertIsNotNone(self.calculator.worksheet)
        self.assertEqual(self.calculator.worksheet.title, "利润计算表")
    
    def test_invalid_file_path(self):
        """测试无效文件路径"""
        # 测试不存在的文件
        with self.assertRaises(ExcelCalculatorError):
            ExcelProfitCalculator("nonexistent_file.xlsx")
        
        # 测试不支持的文件格式
        with self.assertRaises(ExcelCalculatorError):
            ExcelProfitCalculator("test.txt")
    
    def test_path_normalization(self):
        """测试路径规范化"""
        # 测试相对路径（使用实际存在的文件）
        self.calculator = ExcelProfitCalculator(self.test_excel_path)
        self.assertIsNotNone(self.calculator.workbook)
    
    def test_basic_profit_calculation(self):
        """测试基本利润计算功能"""
        self.calculator = ExcelProfitCalculator(self.test_excel_path)
        
        # 测试用例1: 盈利情况
        result = self.calculator.calculate_profit(
            black_price=100.0,
            green_price=120.0,
            commission_rate=10.0,  # 10%
            weight=500.0
        )
        
        self.assertIsInstance(result, ProfitCalculatorResult)
        self.assertEqual(result.profit_amount, 10.0)  # 120 - 100 - 100*0.1 = 10
        self.assertEqual(result.profit_rate, 10.0)    # 10/100 = 0.1 = 10%
        self.assertFalse(result.is_loss)
        self.assertGreater(result.calculation_time, 0)
        
        # 测试用例2: 亏损情况
        result2 = self.calculator.calculate_profit(
            black_price=100.0,
            green_price=80.0,
            commission_rate=12.0,  # 12%
            weight=300.0
        )
        
        self.assertEqual(result2.profit_amount, -32.0)  # 80 - 100 - 100*0.12 = -32
        self.assertEqual(result2.profit_rate, -32.0)    # -32/100 = -0.32 = -32%
        self.assertTrue(result2.is_loss)
    
    def test_input_validation(self):
        """测试输入参数验证"""
        self.calculator = ExcelProfitCalculator(self.test_excel_path)
        
        # 测试负数价格
        with self.assertRaises(ExcelCalculatorError):
            self.calculator.calculate_profit(-100.0, 80.0, 12.0, 500.0)
        
        # 测试无效佣金率
        with self.assertRaises(ExcelCalculatorError):
            self.calculator.calculate_profit(100.0, 80.0, 150.0, 500.0)  # 超过100%
        
        # 测试负重量
        with self.assertRaises(ExcelCalculatorError):
            self.calculator.calculate_profit(100.0, 80.0, 12.0, -500.0)
    
    def test_zero_black_price_handling(self):
        """测试黑标价格为0的处理"""
        self.calculator = ExcelProfitCalculator(self.test_excel_path)
        
        # 黑标价格为0时，利润率应该为0
        result = self.calculator.calculate_profit(
            black_price=0.01,  # 很小的正数
            green_price=10.0,
            commission_rate=5.0,
            weight=100.0
        )
        
        self.assertIsNotNone(result.profit_rate)
    
    def test_convenience_functions(self):
        """测试便捷接口函数"""
        # 测试 calculate_profit_from_excel
        result = calculate_profit_from_excel(
            self.test_excel_path,
            black_price=100.0,
            green_price=110.0,
            commission_rate=8.0,
            weight=400.0
        )
        
        self.assertIsInstance(result, ProfitCalculatorResult)
        self.assertEqual(result.profit_amount, 2.0)  # 110 - 100 - 100*0.08 = 2
        
        # 测试 quick_calculate
        result2 = quick_calculate(
            black_price=200.0,
            green_price=220.0,
            commission_rate=5.0,
            weight=600.0,
            excel_path=self.test_excel_path
        )
        
        self.assertIsInstance(result2, ProfitCalculatorResult)
        self.assertEqual(result2.profit_amount, 10.0)  # 220 - 200 - 200*0.05 = 10
    
    def test_batch_calculation(self):
        """测试批量计算功能"""
        calculations = [
            {"black_price": 100, "green_price": 110, "commission_rate": 5, "weight": 500},
            {"black_price": 200, "green_price": 210, "commission_rate": 8, "weight": 600},
            {"black_price": 150, "green_price": 140, "commission_rate": 10, "weight": 400}  # 亏损案例
        ]
        
        results = batch_calculate_profits(self.test_excel_path, calculations)
        
        self.assertEqual(len(results), 3)
        
        # 第一个结果：盈利
        self.assertEqual(results[0].profit_amount, 5.0)  # 110 - 100 - 100*0.05 = 5
        self.assertFalse(results[0].is_loss)
        
        # 第二个结果：盈利
        self.assertEqual(results[1].profit_amount, -6.0)  # 210 - 200 - 200*0.08 = -6
        self.assertTrue(results[1].is_loss)
        
        # 第三个结果：亏损
        self.assertEqual(results[2].profit_amount, -25.0)  # 140 - 150 - 150*0.1 = -25
        self.assertTrue(results[2].is_loss)
    
    def test_performance_and_reuse(self):
        """测试性能和实例复用"""
        self.calculator = ExcelProfitCalculator(self.test_excel_path)
        
        # 测试连续计算的性能
        start_time = time.time()
        results = []
        
        for i in range(5):
            result = self.calculator.calculate_profit(
                black_price=100 + i * 10,
                green_price=120 + i * 5,
                commission_rate=10 + i,
                weight=500 + i * 50
            )
            results.append(result)
        
        total_time = time.time() - start_time
        avg_time = total_time / 5
        
        # 验证所有计算都成功
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, ProfitCalculatorResult)
        
        # 验证性能要求（每次计算应该在合理时间内完成）
        self.assertLess(avg_time, 1.0, f"平均计算时间 {avg_time:.3f}s 超过1秒")
        
        print(f"性能测试: 5次计算总耗时 {total_time:.3f}s, 平均 {avg_time:.3f}s/次")
    
    def test_service_class(self):
        """测试服务类功能"""
        service = ProfitCalculatorService(self.test_excel_path)
        
        # 测试基本计算
        result = service.calculate(100.0, 110.0, 5.0, 500.0)
        self.assertIsInstance(result, ProfitCalculatorResult)
        
        # 测试性能统计
        stats = service.get_performance_stats()
        self.assertIn('cached_calculators', stats)
        self.assertIn('cache_keys', stats)
        
        # 清理缓存
        service.clear_cache()
        stats_after = service.get_performance_stats()
        self.assertEqual(stats_after['cached_calculators'], 0)
    
    def test_default_service(self):
        """测试默认服务实例"""
        service1 = get_default_service(self.test_excel_path)
        service2 = get_default_service()
        
        # 应该返回同一个实例
        self.assertIs(service1, service2)
    
    def test_data_models(self):
        """测试数据模型"""
        # 测试输入模型
        input_data = ProfitCalculatorInput(
            black_price=100.0,
            green_price=110.0,
            commission_rate=10.0,
            weight=500.0
        )
        
        self.assertEqual(input_data.black_price, 100.0)
        self.assertEqual(input_data.green_price, 110.0)
        self.assertEqual(input_data.commission_rate, 10.0)
        self.assertEqual(input_data.weight, 500.0)
        
        # 测试结果模型
        result = ProfitCalculatorResult(
            profit_amount=10.0,
            profit_rate=10.0,
            is_loss=False,
            input_summary={"test": "data"},
            calculation_time=0.1,
            log_info={"status": "success"}
        )
        
        self.assertEqual(result.profit_amount, 10.0)
        self.assertEqual(result.profit_rate, 10.0)
        self.assertFalse(result.is_loss)
        
        # 测试结果属性
        self.assertEqual(result.profit_amount, 10.0)
        self.assertEqual(result.profit_rate, 10.0)
        self.assertFalse(result.is_loss)
    
    def test_edge_cases(self):
        """测试边界情况"""
        self.calculator = ExcelProfitCalculator(self.test_excel_path)
        
        # 测试极小值
        result = self.calculator.calculate_profit(0.01, 0.01, 0.01, 0.01)
        self.assertIsInstance(result, ProfitCalculatorResult)
        
        # 测试较大值
        result = self.calculator.calculate_profit(10000.0, 12000.0, 15.0, 5000.0)
        self.assertIsInstance(result, ProfitCalculatorResult)
        
        # 测试佣金率边界值
        result = self.calculator.calculate_profit(100.0, 110.0, 0.0, 500.0)  # 0%佣金
        self.assertEqual(result.profit_amount, 10.0)
        
        result = self.calculator.calculate_profit(100.0, 110.0, 100.0, 500.0)  # 100%佣金
        self.assertEqual(result.profit_amount, -90.0)  # 110 - 100 - 100*1.0 = -90
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试文件不存在的情况
        with self.assertRaises(ExcelCalculatorError) as context:
            ExcelProfitCalculator("nonexistent.xlsx")
        
        self.assertIn("文件不存在", str(context.exception))
        
        # 测试无效文件格式
        with self.assertRaises(ExcelCalculatorError) as context:
            ExcelProfitCalculator("test.txt")
        
        self.assertIn("不支持的文件格式", str(context.exception))


class TestExcelFileCreation(unittest.TestCase):
    """测试Excel文件创建功能"""
    
    def test_create_sample_excel_file(self):
        """测试创建示例Excel文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_profits.xlsx"
            
            # 创建文件
            created_file = create_sample_excel_file(test_file)
            
            # 验证文件创建成功
            self.assertTrue(created_file.exists())
            self.assertEqual(created_file, test_file)
            
            # 验证文件可以被计算器使用
            calculator = ExcelProfitCalculator(created_file)
            result = calculator.calculate_profit(100.0, 110.0, 10.0, 500.0)
            self.assertIsInstance(result, ProfitCalculatorResult)
            calculator.close()


def run_comprehensive_test():
    """运行综合测试"""
    print("=" * 80)
    print("Excel利润计算器综合测试")
    print("=" * 80)
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加所有测试
    suite.addTest(unittest.makeSuite(TestExcelProfitCalculator))
    suite.addTest(unittest.makeSuite(TestExcelFileCreation))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print("\n" + "=" * 80)
    print("测试结果摘要")
    print("=" * 80)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # 运行综合测试
    success = run_comprehensive_test()
    
    if success:
        print("\n🎉 所有测试通过！Excel利润计算器功能正常。")
    else:
        print("\n❌ 部分测试失败，请检查问题。")
        exit(1)