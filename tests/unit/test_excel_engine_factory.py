"""
Unit tests for Excel Engine Factory
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import platform

from common.excel_engine.engine_factory import EngineFactory, create_engine
from common.models.exceptions import EngineError


class TestEngineFactory(unittest.TestCase):
    """Test EngineFactory functionality"""
    
    def setUp(self):
        """Test setup"""
        # Clear cache before each test
        EngineFactory.clear_cache()
        
    def tearDown(self):
        """Test cleanup"""
        EngineFactory.clear_cache()
        
    @patch('common.excel_engine.engine_factory.get_engine_config')
    def test_create_python_engine(self, mock_config):
        """Test creating Python engine"""
        # Mock configuration
        config = Mock()
        config.get_engine_type.return_value = "python"
        mock_config.return_value = config
        
        # Create engine
        engine = EngineFactory.create_engine()
        
        # Verify
        self.assertIsNotNone(engine)
        engine_info = engine.get_engine_info()
        self.assertEqual(engine_info['type'], 'python')
        
    @patch('platform.system')
    @patch('common.excel_engine.engine_factory.get_engine_config')
    def test_auto_engine_linux(self, mock_config, mock_platform):
        """Test auto engine selection on Linux"""
        # Mock Linux platform
        mock_platform.return_value = "Linux"
        
        # Mock configuration
        config = Mock()
        config.get_engine_type.return_value = "auto"
        mock_config.return_value = config
        
        # Create engine
        engine = EngineFactory.create_engine()
        
        # Should get Python engine on Linux
        self.assertIsNotNone(engine)
        engine_info = engine.get_engine_info()
        self.assertEqual(engine_info['type'], 'python')
        
    @patch('platform.system')
    @patch('common.excel_engine.engine_factory.get_engine_config')
    def test_auto_engine_windows_fallback(self, mock_config, mock_platform):
        """Test auto engine fallback on Windows when xlwings unavailable"""
        # Mock Windows platform
        mock_platform.return_value = "Windows"
        
        # Mock configuration
        config = Mock()
        config.get_engine_type.return_value = "auto"
        config.get_calculator_path.return_value = "test.xlsx"
        mock_config.return_value = config
        
        # Mock xlwings import failure
        with patch('common.excel_engine.engine_factory.EngineFactory._create_xlwings_engine',
                  side_effect=EngineError("xlwings not available")):
            # Create engine
            engine = EngineFactory.create_engine()
            
            # Should fallback to Python engine
            self.assertIsNotNone(engine)
            engine_info = engine.get_engine_info()
            self.assertEqual(engine_info['type'], 'python')
            
    def test_create_engine_with_config(self):
        """Test creating engine with specific configuration"""
        config = {"engine": "python"}
        engine = EngineFactory.create_engine(config)
        
        self.assertIsNotNone(engine)
        engine_info = engine.get_engine_info()
        self.assertEqual(engine_info['type'], 'python')
        
    def test_invalid_engine_type(self):
        """Test creating engine with invalid type"""
        config = {"engine": "invalid_engine"}
        
        with self.assertRaises(EngineError) as context:
            EngineFactory.create_engine(config)
            
        self.assertIn("Unknown engine type", str(context.exception))
        
    @patch('common.excel_engine.engine_factory.get_engine_config')
    def test_engine_caching(self, mock_config):
        """Test engine instance caching"""
        # Mock configuration with cache enabled
        config = Mock()
        config.get_engine_type.return_value = "python"
        config.is_cache_enabled.return_value = True
        mock_config.return_value = config
        
        # Create first engine
        engine1 = EngineFactory.create_engine()
        
        # Create second engine (should be cached)
        engine2 = EngineFactory.create_engine()
        
        # Should be the same instance
        self.assertIs(engine1, engine2)
        
        # Force new instance
        engine3 = EngineFactory.create_engine(force_new=True)
        
        # Should be different instance
        self.assertIsNot(engine1, engine3)
        
    def test_module_level_create_engine(self):
        """Test module-level create_engine function"""
        engine = create_engine("python")
        
        self.assertIsNotNone(engine)
        engine_info = engine.get_engine_info()
        self.assertEqual(engine_info['type'], 'python')
        
    def test_clear_cache(self):
        """Test clearing engine cache"""
        # Create some engines
        engine1 = create_engine("python")
        
        # Add to cache
        EngineFactory._engine_cache["test"] = engine1
        
        # Clear cache
        EngineFactory.clear_cache()
        
        # Cache should be empty
        self.assertEqual(len(EngineFactory._engine_cache), 0)


class TestPythonEngineIntegration(unittest.TestCase):
    """Integration tests for Python engine"""
    
    def test_python_engine_calculation(self):
        """Test Python engine can perform calculations"""
        from common.models import ProfitCalculatorInput
        
        # Create engine
        engine = create_engine("python")
        
        # Create test input
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
        
        # Calculate
        result = engine.calculate_profit(calc_input)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.engine_used, "python")
        self.assertIsInstance(result.profit_amount, float)
        self.assertIsInstance(result.profit_rate, float)
        
    def test_python_engine_shipping_calculation(self):
        """Test Python engine shipping calculation"""
        engine = create_engine("python")
        
        # Calculate shipping
        shipping = engine.calculate_shipping(
            weight=500.0,
            dimensions=(10, 10, 10),
            price=100.0,
            delivery_type="pickup"
        )
        
        # Verify
        self.assertIsInstance(shipping, float)
        self.assertGreater(shipping, 0)
        
    def test_python_engine_validation(self):
        """Test Python engine validation"""
        engine = create_engine("python")
        
        # Validate connection
        is_valid = engine.validate_connection()
        self.assertTrue(is_valid)


if __name__ == '__main__':
    unittest.main()