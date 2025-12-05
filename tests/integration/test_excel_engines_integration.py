"""
Integration tests for Excel calculation engines

Tests the complete engine system including factory, engines, and validation.
"""

import unittest
import platform
from unittest.mock import patch
import tempfile
import os

from common.models import ProfitCalculatorInput
from common.excel_engine import EngineFactory, create_engine
from common.excel_engine.validation_engine import ValidationEngine
from common.config.excel_engine_config import EngineConfig, get_engine_config


class TestEngineIntegration(unittest.TestCase):
    """Integration tests for engine system"""
    
    def setUp(self):
        """Test setup"""
        # Clear any cached engines
        EngineFactory.clear_cache()
        
    def test_python_engine_full_calculation(self):
        """Test Python engine with full calculation flow"""
        # Create engine
        engine = create_engine("python")
        
        # Create realistic input
        calc_input = ProfitCalculatorInput(
            black_price=150.0,      # 黑标价格
            green_price=120.0,      # 绿标价格
            list_price=114.0,       # 定价 (120 * 0.95)
            purchase_price=60.0,    # 采购价
            commission_rate=12.0,   # 12% 佣金率
            weight=750.0,           # 750克
            length=20.0,
            width=15.0,
            height=10.0
        )
        
        # Calculate
        result = engine.calculate_profit(calc_input)
        
        # Verify results
        self.assertEqual(result.engine_used, "python")
        self.assertIsInstance(result.profit_amount, float)
        self.assertIsInstance(result.profit_rate, float)
        self.assertIsInstance(result.shipping_cost, float)
        self.assertIsInstance(result.commission_amount, float)
        
        # Verify calculations make sense
        self.assertGreater(result.shipping_cost, 0)  # Should have shipping cost
        self.assertAlmostEqual(result.commission_amount, 114.0 * 0.12, places=2)  # 12% of list price
        
        # Profit should be: list_price - purchase_price - shipping - label_fee - commission
        expected_profit = 114.0 - 60.0 - result.shipping_cost - 2.0 - result.commission_amount
        self.assertAlmostEqual(result.profit_amount, expected_profit, places=2)
        
    def test_engine_auto_selection(self):
        """Test automatic engine selection based on platform"""
        # Use auto mode
        config = {"engine": "auto"}
        engine = EngineFactory.create_engine(config)
        
        # Verify appropriate engine selected
        engine_info = engine.get_engine_info()
        
        if platform.system() == "Linux":
            self.assertEqual(engine_info['type'], 'python')
        else:
            # Windows/macOS might get xlwings or fallback to python
            self.assertIn(engine_info['type'], ['xlwings', 'python'])
            
    def test_batch_calculation(self):
        """Test batch calculation functionality"""
        engine = create_engine("python")
        
        # Create multiple inputs
        inputs = []
        for i in range(5):
            inputs.append(ProfitCalculatorInput(
                black_price=100.0 + i * 10,
                green_price=80.0 + i * 10,
                list_price=76.0 + i * 9.5,
                purchase_price=40.0 + i * 5,
                commission_rate=10.0,
                weight=500.0 + i * 100,
                length=10.0,
                width=10.0,
                height=10.0
            ))
        
        # Batch calculate
        if hasattr(engine, 'batch_calculate'):
            results = engine.batch_calculate(inputs)
        else:
            # Fallback to sequential
            from common.business.excel_calculator import ExcelProfitCalculator
            calculator = ExcelProfitCalculator()
            results = calculator.batch_calculate(inputs)
        
        # Verify
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsNotNone(result.profit_amount)
            self.assertIsNotNone(result.profit_rate)
            
    def test_configuration_loading(self):
        """Test configuration loading and engine creation"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "engine": {
                    "default": "python",
                    "cache_enabled": False
                },
                "logging": {
                    "level": "DEBUG"
                }
            }
            import json
            json.dump(config_data, f)
            config_file = f.name
            
        try:
            # Load config from file
            config = EngineConfig.from_file(config_file)
            
            # Verify configuration
            self.assertEqual(config.get_engine_type(), "python")
            self.assertFalse(config.is_cache_enabled())
            
            # Create engine with config
            engine = EngineFactory.create_engine({"engine": {"default": "python", "cache_enabled": False}})
            
            # Verify engine
            engine_info = engine.get_engine_info()
            self.assertEqual(engine_info['type'], 'python')
            
        finally:
            # Cleanup
            os.unlink(config_file)
            
    def test_shipping_calculation_variations(self):
        """Test shipping calculation with different weights and delivery types"""
        engine = create_engine("python")
        
        # Test different weights
        test_cases = [
            (50, "pickup", 5.0),      # Light, pickup
            (500, "pickup", 9.0),     # Medium, pickup
            (2000, "pickup", 13.0),   # Heavy, pickup
            (500, "delivery", 11.0),  # Medium, delivery
        ]
        
        for weight, delivery_type, expected_min in test_cases:
            shipping = engine.calculate_shipping(
                weight=weight,
                dimensions=(10, 10, 10),
                price=100.0,
                delivery_type=delivery_type
            )
            
            self.assertGreaterEqual(shipping, expected_min,
                f"Shipping for {weight}g {delivery_type} should be at least {expected_min}")
                
    @patch('common.excel_engine.xlwings_engine.XLWINGS_AVAILABLE', False)
    def test_xlwings_unavailable_fallback(self):
        """Test fallback when xlwings is not available"""
        # Try to create xlwings engine when not available
        with self.assertRaises(Exception):
            engine = create_engine("xlwings")
            
        # Auto mode should fallback gracefully
        engine = create_engine("auto")
        self.assertIsNotNone(engine)
        self.assertEqual(engine.get_engine_info()['type'], 'python')
        
    def test_validation_engine_integration(self):
        """Test validation engine comparing results"""
        # Create validation engine
        validation_engine = ValidationEngine(
            primary_engine="python",
            comparison_engines=["python"],  # Compare with itself
            tolerance=0.001  # Very tight tolerance
        )
        
        # Create input
        calc_input = ProfitCalculatorInput(
            black_price=100.0,
            green_price=80.0,
            list_price=76.0,
            purchase_price=40.0,
            commission_rate=10.0,
            weight=500.0,
            length=10.0,
            width=10.0,
            height=10.0
        )
        
        # Calculate with validation
        result = validation_engine.calculate_profit(calc_input)
        
        # Should be valid (comparing with itself)
        validation_info = result.log_info['validation']
        self.assertTrue(validation_info['is_valid'])
        self.assertEqual(len(validation_info['discrepancies']), 0)


class TestExcelCalculatorIntegration(unittest.TestCase):
    """Test the refactored ExcelProfitCalculator"""
    
    def test_calculator_with_engine_switching(self):
        """Test calculator can switch engines"""
        from common.business.excel_calculator import ExcelProfitCalculator
        
        # Create calculator
        calculator = ExcelProfitCalculator()
        
        # Get initial engine
        initial_engine = calculator.get_engine_info()['type']
        
        # Switch to python engine
        calculator.switch_engine("python")
        
        # Verify switch
        new_engine = calculator.get_engine_info()['type']
        self.assertEqual(new_engine, "python")
        
        # Perform calculation
        calc_input = ProfitCalculatorInput(
            black_price=100.0,
            green_price=80.0,
            list_price=76.0,
            purchase_price=40.0,
            commission_rate=10.0,
            weight=500.0,
            length=10.0,
            width=10.0,
            height=10.0
        )
        
        result = calculator.calculate_profit(calc_input)
        self.assertEqual(result.engine_used, "python")
        
    def test_calculator_statistics(self):
        """Test calculator statistics tracking"""
        from common.business.excel_calculator import ExcelProfitCalculator
        
        calculator = ExcelProfitCalculator()
        
        # Perform some calculations
        for i in range(3):
            calc_input = ProfitCalculatorInput(
                black_price=100.0 + i,
                green_price=80.0 + i,
                list_price=76.0 + i,
                purchase_price=40.0 + i,
                commission_rate=10.0,
                weight=500.0,
                length=10.0,
                width=10.0,
                height=10.0
            )
            calculator.calculate_profit(calc_input)
            
        # Get statistics
        stats = calculator.get_statistics()
        
        # Verify
        self.assertEqual(stats['calculation_count'], 3)
        self.assertGreater(stats['total_calculation_time'], 0)
        self.assertGreater(stats['average_calculation_time'], 0)
        
    def test_calculator_context_manager(self):
        """Test calculator as context manager"""
        from common.business.excel_calculator import ExcelProfitCalculator
        
        with ExcelProfitCalculator() as calculator:
            # Use calculator
            calc_input = ProfitCalculatorInput(
                black_price=100.0,
                green_price=80.0,
                list_price=76.0,
                purchase_price=40.0,
                commission_rate=10.0,
                weight=500.0,
                length=10.0,
                width=10.0,
                height=10.0
            )
            
            result = calculator.calculate_profit(calc_input)
            self.assertIsNotNone(result)
            
        # Calculator should be closed after context


if __name__ == '__main__':
    unittest.main()