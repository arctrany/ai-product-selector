"""
Unit tests for Validation Engine
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from common.excel_engine.validation_engine import ValidationEngine, ValidationResult
from common.models import ProfitCalculatorInput, ProfitCalculatorResult


class TestValidationEngine(unittest.TestCase):
    """Test ValidationEngine functionality"""
    
    @patch('common.excel_engine.validation_engine.EngineFactory')
    def test_validation_engine_creation(self, mock_factory):
        """Test creating validation engine"""
        # Mock engines
        mock_primary = Mock()
        mock_primary.get_engine_info.return_value = {"type": "xlwings"}
        
        mock_comparison = Mock()
        mock_comparison.get_engine_info.return_value = {"type": "python"}
        
        mock_factory.create_engine.side_effect = [mock_primary, mock_comparison]
        
        # Create validation engine
        engine = ValidationEngine(
            primary_engine="xlwings",
            comparison_engines=["python"],
            tolerance=0.01
        )
        
        # Verify
        self.assertIsNotNone(engine)
        self.assertEqual(engine.primary_engine_type, "xlwings")
        self.assertEqual(list(engine.comparison_engines.keys()), ["python"])
        
    @patch('common.excel_engine.validation_engine.EngineFactory')
    def test_calculate_profit_with_validation(self, mock_factory):
        """Test profit calculation with validation"""
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
        
        # Mock primary result
        primary_result = ProfitCalculatorResult(
            profit_amount=35.5,
            profit_rate=71.0,
            is_loss=False,
            shipping_cost=9.0,
            commission_amount=9.5,
            engine_used="xlwings",
            input_summary={},
            calculation_time=0.1,
            log_info={}
        )
        
        # Mock comparison result (slightly different)
        comparison_result = ProfitCalculatorResult(
            profit_amount=35.3,  # 0.2 difference
            profit_rate=70.6,    # 0.4% difference
            is_loss=False,
            shipping_cost=9.0,
            commission_amount=9.5,
            engine_used="python",
            input_summary={},
            calculation_time=0.05,
            log_info={}
        )
        
        # Setup mocks
        mock_primary = Mock()
        mock_primary.calculate_profit.return_value = primary_result
        
        mock_comparison = Mock()
        mock_comparison.calculate_profit.return_value = comparison_result
        
        mock_factory.create_engine.side_effect = [mock_primary, mock_comparison]
        
        # Create engine with 1% tolerance
        engine = ValidationEngine(tolerance=0.01)
        
        # Calculate
        result = engine.calculate_profit(calc_input)
        
        # Verify
        self.assertEqual(result.profit_amount, 35.5)  # Primary result
        self.assertIn('validation', result.log_info)
        
        validation_info = result.log_info['validation']
        self.assertTrue(validation_info['is_valid'])  # Should pass with 1% tolerance
        self.assertEqual(len(validation_info['discrepancies']), 0)
        
    @patch('common.excel_engine.validation_engine.EngineFactory')
    def test_validation_with_discrepancies(self, mock_factory):
        """Test validation with discrepancies exceeding tolerance"""
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
        
        # Mock results with significant differences
        primary_result = ProfitCalculatorResult(
            profit_amount=35.5,
            profit_rate=71.0,
            is_loss=False,
            shipping_cost=9.0,
            commission_amount=9.5,
            engine_used="xlwings",
            input_summary={},
            calculation_time=0.1,
            log_info={}
        )
        
        comparison_result = ProfitCalculatorResult(
            profit_amount=30.0,  # 5.5 difference (>1%)
            profit_rate=60.0,    # 11% difference
            is_loss=False,
            shipping_cost=12.0,  # Different shipping
            commission_amount=9.5,
            engine_used="python",
            input_summary={},
            calculation_time=0.05,
            log_info={}
        )
        
        # Setup mocks
        mock_primary = Mock()
        mock_primary.calculate_profit.return_value = primary_result
        
        mock_comparison = Mock()
        mock_comparison.calculate_profit.return_value = comparison_result
        
        mock_factory.create_engine.side_effect = [mock_primary, mock_comparison]
        
        # Create engine with 1% tolerance
        engine = ValidationEngine(tolerance=0.01)
        
        # Calculate
        result = engine.calculate_profit(calc_input)
        
        # Verify
        validation_info = result.log_info['validation']
        self.assertFalse(validation_info['is_valid'])
        self.assertGreater(len(validation_info['discrepancies']), 0)
        
        # Check specific discrepancies
        discrepancies = validation_info['discrepancies']
        fields_with_discrepancies = [d['field'] for d in discrepancies]
        self.assertIn('profit_amount', fields_with_discrepancies)
        self.assertIn('profit_rate', fields_with_discrepancies)
        self.assertIn('shipping_cost', fields_with_discrepancies)
        
    def test_validation_result_creation(self):
        """Test ValidationResult dataclass"""
        result = ValidationResult(
            is_valid=True,
            discrepancies=[],
            engine_results={},
            summary="All good"
        )
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.summary, "All good")
        
    @patch('common.excel_engine.validation_engine.EngineFactory')
    def test_generate_validation_report(self, mock_factory):
        """Test generating validation report for multiple inputs"""
        # Create test inputs
        inputs = [
            ProfitCalculatorInput(
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
            for _ in range(3)
        ]
        
        # Mock results
        primary_result = ProfitCalculatorResult(
            profit_amount=35.5,
            profit_rate=71.0,
            is_loss=False,
            engine_used="xlwings",
            input_summary={},
            calculation_time=0.1,
            log_info={'validation': {'is_valid': True, 'discrepancies': []}}
        )
        
        # Setup mocks
        mock_primary = Mock()
        mock_primary.calculate_profit.return_value = primary_result
        
        mock_comparison = Mock()
        mock_comparison.calculate_profit.return_value = primary_result
        
        mock_factory.create_engine.side_effect = [mock_primary, mock_comparison]
        
        # Create engine
        engine = ValidationEngine()
        
        # Generate report
        report = engine.generate_validation_report(inputs)
        
        # Verify report structure
        self.assertEqual(report['total_inputs'], 3)
        self.assertEqual(len(report['results']), 3)
        self.assertEqual(report['summary']['valid_count'], 3)
        self.assertEqual(report['summary']['invalid_count'], 0)
        self.assertEqual(report['summary']['validation_rate'], 100.0)


if __name__ == '__main__':
    unittest.main()