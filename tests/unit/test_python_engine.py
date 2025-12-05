"""
Unit tests for Python calculation engine
"""

import unittest
from unittest.mock import Mock, patch

from common.excel_engine.python_engine import PythonEngine
from common.models import ProfitCalculatorInput, ProfitCalculatorResult
from common.models.exceptions import EngineError


class TestPythonEngine(unittest.TestCase):
    """Test Python engine functionality"""
    
    def setUp(self):
        """Test setup"""
        self.engine = PythonEngine()
        
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertTrue(self.engine._initialized)
        engine_info = self.engine.get_engine_info()
        self.assertEqual(engine_info['type'], 'python')
        self.assertEqual(engine_info['platform_support'], 'all')
        
    def test_profit_calculation(self):
        """Test basic profit calculation"""
        calc_input = ProfitCalculatorInput(
            black_price=120.0,
            green_price=100.0,
            list_price=95.0,
            purchase_price=50.0,
            commission_rate=10.0,
            weight=500.0,
            length=10.0,
            width=10.0,
            height=10.0
        )
        
        result = self.engine.calculate_profit(calc_input)
        
        # Verify result structure
        self.assertIsInstance(result, ProfitCalculatorResult)
        self.assertEqual(result.engine_used, "python")
        self.assertIsNotNone(result.profit_amount)
        self.assertIsNotNone(result.profit_rate)
        self.assertIsNotNone(result.shipping_cost)
        self.assertIsNotNone(result.commission_amount)
        
        # Verify calculations
        self.assertGreater(result.shipping_cost, 0)
        self.assertAlmostEqual(result.commission_amount, 95.0 * 0.10, places=2)
        
    def test_shipping_calculation(self):
        """Test shipping cost calculation using real 6-channel logic"""
        # Test pickup shipping - K8 channel (1-500g, 0-1500 RUB)
        # Formula: 3 + 500 * 0.025 = 15.5
        pickup_cost = self.engine.calculate_shipping(
            weight=500.0,
            dimensions=(10, 10, 10),
            price=100.0,  # Low price -> K8 channel
            delivery_type="pickup"
        )
        self.assertAlmostEqual(pickup_cost, 15.5, places=2)

        # Test with higher price (1501-7000 RUB) -> K22 channel
        # K22 pickup: 16 + 500 * 0.025 = 28.5
        pickup_cost_k22 = self.engine.calculate_shipping(
            weight=500.0,
            dimensions=(10, 10, 10),
            price=2000.0,  # Medium price -> K22 channel
            delivery_type="pickup"
        )
        self.assertAlmostEqual(pickup_cost_k22, 28.5, places=2)

        # Test delivery for K22 channel: 19.5 + 500 * 0.025 = 32.0
        delivery_cost = self.engine.calculate_shipping(
            weight=500.0,
            dimensions=(10, 10, 10),
            price=2000.0,
            delivery_type="delivery"
        )
        self.assertAlmostEqual(delivery_cost, 32.0, places=2)
        
    def test_weight_ranges(self):
        """Test shipping calculation for different weight ranges using real 6-channel logic

        Channels (for price 100 RUB = low price tier 0-1500):
        - K8: 1-500g, pickup: 3 + weight*0.025
        - K15: 501-25000g, pickup: 23 + weight*0.017
        """
        # Using price=100 RUB which selects K8 (1-500g) or K15 (501-25000g)
        test_cases = [
            # (weight, delivery_type, expected) - price=100 RUB
            (25, "pickup", 3 + 25 * 0.025),        # K8: 3.625
            (100, "pickup", 3 + 100 * 0.025),      # K8: 5.5
            (300, "pickup", 3 + 300 * 0.025),      # K8: 10.5
            (500, "pickup", 3 + 500 * 0.025),      # K8: 15.5
            (600, "pickup", 23 + 600 * 0.017),     # K15: 33.2
            (1000, "pickup", 23 + 1000 * 0.017),   # K15: 40.0
            (2000, "pickup", 23 + 2000 * 0.017),   # K15: 57.0
            (5000, "pickup", 23 + 5000 * 0.017),   # K15: 108.0
        ]

        for weight, delivery_type, expected in test_cases:
            cost = self.engine.calculate_shipping(
                weight=weight,
                dimensions=(10, 10, 10),
                price=100.0,  # Low price -> K8 or K15
                delivery_type=delivery_type
            )
            self.assertAlmostEqual(cost, expected, places=2,
                msg=f"Weight {weight}g should have cost {expected:.2f}, got {cost:.2f}")
                
    def test_validate_connection(self):
        """Test connection validation"""
        self.assertTrue(self.engine.validate_connection())
        
    def test_engine_not_initialized(self):
        """Test operations when engine not initialized"""
        self.engine._initialized = False
        
        with self.assertRaises(EngineError):
            self.engine.calculate_profit(Mock())
            
        with self.assertRaises(EngineError):
            self.engine.calculate_shipping(500, (10, 10, 10), 100)
            
    def test_invalid_input(self):
        """Test handling of invalid input"""
        invalid_input = ProfitCalculatorInput(
            black_price=-100.0,  # Invalid negative price
            green_price=100.0,
            list_price=95.0,
            purchase_price=50.0,
            commission_rate=10.0,
            weight=500.0,
            length=10.0,
            width=10.0,
            height=10.0
        )
        
        # Should raise EngineError (which wraps the ValueError)
        with self.assertRaises(EngineError) as context:
            self.engine.calculate_profit(invalid_input)
            
        # Verify the error message contains the validation error
        self.assertIn("黑标价格必须为正数", str(context.exception))
            
    def test_reload_rules(self):
        """Test reloading compiled rules"""
        # Should not raise exception
        self.engine.reload_rules()
        self.assertTrue(self.engine._initialized)


if __name__ == '__main__':
    unittest.main()