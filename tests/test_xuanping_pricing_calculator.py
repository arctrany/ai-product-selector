"""
测试好店筛选系统的定价计算器

测试价格计算、汇率转换和利润评估功能。
"""

import pytest
from unittest.mock import Mock, patch

from apps.xuanping.common.business.pricing_calculator import PricingCalculator
from apps.xuanping.common.models import PriceCalculationResult
from apps.xuanping.common.config import GoodStoreSelectorConfig, PriceCalculationConfig


class TestPricingCalculator:
    """测试定价计算器"""
    
    def setup_method(self):
        """测试前的设置"""
        self.config = GoodStoreSelectorConfig()
        self.calculator = PricingCalculator(self.config)
    
    def test_pricing_calculator_initialization(self):
        """测试定价计算器初始化"""
        assert self.calculator.config is not None
        assert self.calculator.logger is not None
        
        # 测试使用默认配置初始化
        calculator_default = PricingCalculator()
        assert calculator_default.config is not None
    
    def test_convert_rub_to_cny(self):
        """测试卢布转人民币"""
        # 使用默认汇率 0.075
        result = self.calculator.convert_rub_to_cny(1000.0)
        assert result == 75.0
        
        result = self.calculator.convert_rub_to_cny(0.0)
        assert result == 0.0
        
        # 测试自定义汇率
        custom_config = GoodStoreSelectorConfig()
        custom_config.price_calculation.rub_to_cny_rate = 0.08
        custom_calculator = PricingCalculator(custom_config)
        
        result = custom_calculator.convert_rub_to_cny(1000.0)
        assert result == 80.0
    
    def test_calculate_real_selling_price_case1(self):
        """测试真实售价计算 - 情况1: 价格 <= 90人民币"""
        # 黑标价格 <= 90人民币：真实售价 = 黑标价格
        green_price = 70.0
        black_price = 80.0
        
        result = self.calculator.calculate_real_selling_price(green_price, black_price)
        assert result == 80.0  # 应该等于黑标价格
        
        # 只有黑标价格的情况
        result = self.calculator.calculate_real_selling_price(None, 85.0)
        assert result == 85.0
    
    def test_calculate_real_selling_price_case2(self):
        """测试真实售价计算 - 情况2: 90 < 价格 <= 120人民币"""
        # 90人民币 < 黑标价格 <= 120人民币：真实售价 = 黑标价格 + 5
        green_price = 95.0
        black_price = 100.0
        
        result = self.calculator.calculate_real_selling_price(green_price, black_price)
        assert result == 105.0  # 100 + 5
        
        # 边界值测试
        result = self.calculator.calculate_real_selling_price(None, 120.0)
        assert result == 125.0  # 120 + 5
    
    def test_calculate_real_selling_price_case3(self):
        """测试真实售价计算 - 情况3: 价格 > 120人民币"""
        # 黑标价格 > 120人民币：真实售价 = (黑标 - 绿标) × 2.2 + 黑标
        green_price = 100.0
        black_price = 150.0
        
        result = self.calculator.calculate_real_selling_price(green_price, black_price)
        expected = (150.0 - 100.0) * 2.2 + 150.0  # 50 * 2.2 + 150 = 260
        assert result == expected
        
        # 只有黑标价格的情况（价格 > 120）
        result = self.calculator.calculate_real_selling_price(None, 150.0)
        assert result == 150.0  # 没有绿标价格时直接使用黑标价格
    
    def test_calculate_real_selling_price_edge_cases(self):
        """测试真实售价计算的边界情况"""
        # 没有价格信息
        result = self.calculator.calculate_real_selling_price(None, None)
        assert result == 0.0
        
        # 只有绿标价格
        result = self.calculator.calculate_real_selling_price(100.0, None)
        assert result == 105.0  # 100 + 5 (因为在90-120区间)
        
        # 负数价格（应该返回0）
        result = self.calculator.calculate_real_selling_price(-50.0, -30.0)
        assert result == 0.0
    
    def test_calculate_product_pricing(self):
        """测试商品定价计算（95折）"""
        real_selling_price = 100.0
        result = self.calculator.calculate_product_pricing(real_selling_price)
        assert result == 95.0  # 100 * 0.95
        
        # 测试自定义折扣率
        custom_config = GoodStoreSelectorConfig()
        custom_config.price_calculation.pricing_discount_rate = 0.90
        custom_calculator = PricingCalculator(custom_config)
        
        result = custom_calculator.calculate_product_pricing(100.0)
        assert result == 90.0  # 100 * 0.90
    
    def test_calculate_complete_pricing(self):
        """测试完整的定价计算流程"""
        green_price_rub = 1000.0  # 卢布
        black_price_rub = 1200.0  # 卢布
        
        result = self.calculator.calculate_complete_pricing(green_price_rub, black_price_rub)
        
        assert isinstance(result, PriceCalculationResult)
        assert result.calculation_details['input_green_price_rub'] == 1000.0
        assert result.calculation_details['input_black_price_rub'] == 1200.0
        assert result.calculation_details['exchange_rate'] == 0.075
        
        # 验证汇率转换
        green_price_cny = 1000.0 * 0.075  # 75.0
        black_price_cny = 1200.0 * 0.075  # 90.0
        assert result.calculation_details['green_price_cny'] == green_price_cny
        assert result.calculation_details['black_price_cny'] == black_price_cny
        
        # 验证真实售价计算（90人民币，应该等于黑标价格）
        assert result.real_selling_price == black_price_cny
        
        # 验证商品定价（95折）
        assert result.product_pricing == black_price_cny * 0.95
        
        # 验证利润计算
        expected_profit = result.real_selling_price - result.product_pricing
        assert result.profit_amount == expected_profit
        
        expected_profit_rate = (expected_profit / result.real_selling_price) * 100
        assert result.profit_rate == expected_profit_rate
    
    def test_calculate_complete_pricing_with_none_values(self):
        """测试包含None值的完整定价计算"""
        # 只有黑标价格
        result = self.calculator.calculate_complete_pricing(None, 1600.0)  # 1600卢布 = 120人民币
        
        assert result.calculation_details['input_green_price_rub'] is None
        assert result.calculation_details['input_black_price_rub'] == 1600.0
        assert result.calculation_details['green_price_cny'] is None
        assert result.calculation_details['black_price_cny'] == 120.0
        
        # 120人民币应该加5
        assert result.real_selling_price == 125.0
        assert result.product_pricing == 125.0 * 0.95
    
    def test_validate_prices(self):
        """测试价格验证"""
        # 有效价格
        assert self.calculator.validate_prices(100.0, 120.0) == True
        assert self.calculator.validate_prices(None, 120.0) == True
        assert self.calculator.validate_prices(100.0, None) == True
        
        # 无效价格
        assert self.calculator.validate_prices(None, None) == False
        assert self.calculator.validate_prices(-50.0, 120.0) == False
        assert self.calculator.validate_prices(100.0, -30.0) == False
        assert self.calculator.validate_prices(0.0, 120.0) == False
        assert self.calculator.validate_prices(100.0, 0.0) == False
        
        # 绿标价格大于黑标价格（会记录警告但不返回False）
        with patch.object(self.calculator.logger, 'warning') as mock_warning:
            result = self.calculator.validate_prices(150.0, 120.0)
            assert result == True  # 不直接返回False
            mock_warning.assert_called_once()
    
    def test_get_pricing_summary(self):
        """测试定价摘要生成"""
        result = PriceCalculationResult(
            real_selling_price=100.0,
            product_pricing=95.0,
            profit_amount=5.0,
            profit_rate=5.26,
            is_profitable=False,
            calculation_details={}
        )
        
        summary = self.calculator.get_pricing_summary(result)
        expected = "定价摘要: 真实售价 ¥100.00, 商品定价 ¥95.00, 利润率 5.26%, 无利润"
        assert summary == expected
        
        # 测试有利润的情况
        result.is_profitable = True
        summary = self.calculator.get_pricing_summary(result)
        assert "有利润" in summary
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试convert_rub_to_cny的错误处理
        with patch.object(self.calculator.logger, 'error') as mock_error:
            # 模拟异常
            with patch.object(self.calculator.config.price_calculation, 'rub_to_cny_rate', side_effect=Exception("Test error")):
                result = self.calculator.convert_rub_to_cny(1000.0)
                assert result == 1000.0  # 应该返回原值
                mock_error.assert_called_once()
        
        # 测试calculate_complete_pricing的错误处理
        with patch.object(self.calculator, 'calculate_real_selling_price', side_effect=Exception("Test error")):
            result = self.calculator.calculate_complete_pricing(1000.0, 1200.0)
            assert result.real_selling_price == 0.0
            assert result.is_profitable == False
            assert 'error' in result.calculation_details
    
    def test_custom_thresholds(self):
        """测试自定义阈值"""
        # 创建自定义配置
        custom_config = GoodStoreSelectorConfig()
        custom_config.price_calculation.price_adjustment_threshold_1 = 100.0  # 改为100
        custom_config.price_calculation.price_adjustment_threshold_2 = 150.0  # 改为150
        custom_config.price_calculation.price_adjustment_amount = 10.0  # 改为10
        custom_config.price_calculation.price_multiplier = 3.0  # 改为3.0
        
        custom_calculator = PricingCalculator(custom_config)
        
        # 测试新的阈值1（价格 <= 100）
        result = custom_calculator.calculate_real_selling_price(80.0, 95.0)
        assert result == 95.0  # 应该等于黑标价格
        
        # 测试新的阈值2（100 < 价格 <= 150）
        result = custom_calculator.calculate_real_selling_price(120.0, 130.0)
        assert result == 140.0  # 130 + 10
        
        # 测试超过阈值2（价格 > 150）
        result = custom_calculator.calculate_real_selling_price(150.0, 200.0)
        expected = (200.0 - 150.0) * 3.0 + 200.0  # 50 * 3.0 + 200 = 350
        assert result == expected


class TestPricingCalculatorIntegration:
    """测试定价计算器的集成场景"""
    
    def test_real_world_scenario_1(self):
        """测试真实场景1：低价商品"""
        calculator = PricingCalculator()
        
        # 模拟一个低价商品：绿标60卢布，黑标80卢布
        green_price_rub = 800.0  # 60人民币
        black_price_rub = 1067.0  # 80人民币
        
        result = calculator.calculate_complete_pricing(green_price_rub, black_price_rub)
        
        # 验证汇率转换
        assert result.calculation_details['green_price_cny'] == 60.0
        assert result.calculation_details['black_price_cny'] == 80.025  # 1067 * 0.075
        
        # 80人民币 <= 90，所以真实售价 = 黑标价格
        assert result.real_selling_price == 80.025
        
        # 商品定价 = 真实售价 * 0.95
        assert result.product_pricing == 80.025 * 0.95
        
        # 验证利润率
        assert result.profit_rate == 5.0  # (1 - 0.95) * 100
    
    def test_real_world_scenario_2(self):
        """测试真实场景2：中价商品"""
        calculator = PricingCalculator()
        
        # 模拟一个中价商品：绿标100卢布，黑标110卢布
        green_price_rub = 1333.0  # 约100人民币
        black_price_rub = 1467.0  # 约110人民币
        
        result = calculator.calculate_complete_pricing(green_price_rub, black_price_rub)
        
        green_cny = 1333.0 * 0.075  # 99.975
        black_cny = 1467.0 * 0.075  # 110.025
        
        # 110人民币在90-120区间，所以真实售价 = 黑标价格 + 5
        expected_real_price = black_cny + 5.0
        assert result.real_selling_price == expected_real_price
        
        # 验证商品定价
        assert result.product_pricing == expected_real_price * 0.95
    
    def test_real_world_scenario_3(self):
        """测试真实场景3：高价商品"""
        calculator = PricingCalculator()
        
        # 模拟一个高价商品：绿标150卢布，黑标200卢布
        green_price_rub = 2000.0  # 150人民币
        black_price_rub = 2667.0  # 200人民币
        
        result = calculator.calculate_complete_pricing(green_price_rub, black_price_rub)
        
        green_cny = 2000.0 * 0.075  # 150.0
        black_cny = 2667.0 * 0.075  # 200.025
        
        # 200人民币 > 120，所以真实售价 = (黑标 - 绿标) × 2.2 + 黑标
        expected_real_price = (black_cny - green_cny) * 2.2 + black_cny
        assert result.real_selling_price == expected_real_price
        
        # 验证利润率是否合理
        assert result.profit_rate > 0  # 应该有正利润率


if __name__ == "__main__":
    pytest.main([__file__, "-v"])