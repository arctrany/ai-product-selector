"""
Validation Engine

This engine wraps other engines and provides validation capabilities
by comparing results across multiple engines.
"""

import logging
import time
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

from .base import CalculationEngine
from ..models import ProfitCalculatorInput, ProfitCalculatorResult, EngineError
from .engine_factory import EngineFactory


@dataclass
class ValidationResult:
    """Validation result for cross-engine comparison"""
    is_valid: bool
    discrepancies: List[Dict[str, Any]]
    engine_results: Dict[str, ProfitCalculatorResult]
    summary: str


class ValidationEngine(CalculationEngine):
    """Validation engine that compares results across multiple engines"""
    
    def __init__(self, primary_engine: str = "xlwings", 
                 comparison_engines: Optional[List[str]] = None,
                 tolerance: float = 0.01):
        """
        Initialize validation engine
        
        Args:
            primary_engine: Primary engine to use for results
            comparison_engines: List of engines to compare against
            tolerance: Acceptable difference tolerance (0.01 = 1%)
        """
        self.logger = logging.getLogger(f"{__name__}.ValidationEngine")
        self.primary_engine_type = primary_engine
        self.comparison_engine_types = comparison_engines or ["python"]
        self.tolerance = tolerance
        
        # Create engines
        try:
            self.primary_engine = EngineFactory.create_engine({"engine": primary_engine})
            self.comparison_engines = {}
            
            for engine_type in self.comparison_engine_types:
                try:
                    engine = EngineFactory.create_engine({"engine": engine_type})
                    self.comparison_engines[engine_type] = engine
                except Exception as e:
                    self.logger.warning(f"Failed to create {engine_type} engine: {e}")
                    
            if not self.comparison_engines:
                raise EngineError("No comparison engines available")
                
            self.logger.info(
                f"Validation engine initialized with primary={primary_engine}, "
                f"comparison={list(self.comparison_engines.keys())}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize validation engine: {e}")
            raise EngineError(f"Validation engine initialization failed: {e}")
            
    def calculate_profit(self, inputs: ProfitCalculatorInput) -> ProfitCalculatorResult:
        """
        Calculate profit using primary engine and validate with comparison engines
        
        Args:
            inputs: Calculation inputs
            
        Returns:
            Primary engine result (with validation info in log_info)
        """
        start_time = time.time()
        
        # Get primary result
        primary_result = self.primary_engine.calculate_profit(inputs)
        
        # Run comparison engines
        comparison_results = {}
        for engine_type, engine in self.comparison_engines.items():
            try:
                result = engine.calculate_profit(inputs)
                comparison_results[engine_type] = result
            except Exception as e:
                self.logger.error(f"Comparison engine {engine_type} failed: {e}")
                
        # Validate results
        validation = self._validate_results(primary_result, comparison_results)
        
        # Add validation info to primary result
        primary_result.log_info['validation'] = {
            'is_valid': validation.is_valid,
            'discrepancies': validation.discrepancies,
            'summary': validation.summary,
            'engines_compared': list(comparison_results.keys())
        }
        
        # Update calculation time
        total_time = time.time() - start_time
        primary_result.calculation_time = total_time
        
        # Log validation results
        if not validation.is_valid:
            self.logger.warning(f"Validation failed: {validation.summary}")
            for discrepancy in validation.discrepancies:
                self.logger.warning(f"  {discrepancy}")
                
        return primary_result
        
    def _validate_results(self, primary: ProfitCalculatorResult, 
                         comparisons: Dict[str, ProfitCalculatorResult]) -> ValidationResult:
        """
        Validate results across engines
        
        Args:
            primary: Primary engine result
            comparisons: Comparison engine results
            
        Returns:
            ValidationResult
        """
        discrepancies = []
        
        for engine_type, result in comparisons.items():
            # Check profit amount
            profit_diff = abs(primary.profit_amount - result.profit_amount)
            profit_diff_pct = (profit_diff / max(abs(primary.profit_amount), 0.01)) * 100
            
            if profit_diff_pct > self.tolerance * 100:
                discrepancies.append({
                    'field': 'profit_amount',
                    'engine': engine_type,
                    'primary_value': primary.profit_amount,
                    'comparison_value': result.profit_amount,
                    'difference': profit_diff,
                    'difference_pct': profit_diff_pct
                })
                
            # Check profit rate
            rate_diff = abs(primary.profit_rate - result.profit_rate)
            if rate_diff > self.tolerance * 100:
                discrepancies.append({
                    'field': 'profit_rate',
                    'engine': engine_type,
                    'primary_value': primary.profit_rate,
                    'comparison_value': result.profit_rate,
                    'difference': rate_diff
                })
                
            # Check components if available
            if primary.shipping_cost is not None and result.shipping_cost is not None:
                shipping_diff = abs(primary.shipping_cost - result.shipping_cost)
                if shipping_diff > self.tolerance * max(primary.shipping_cost, 1.0):
                    discrepancies.append({
                        'field': 'shipping_cost',
                        'engine': engine_type,
                        'primary_value': primary.shipping_cost,
                        'comparison_value': result.shipping_cost,
                        'difference': shipping_diff
                    })
                    
        # Build summary
        is_valid = len(discrepancies) == 0
        if is_valid:
            summary = f"All engines agree within {self.tolerance * 100}% tolerance"
        else:
            summary = f"Found {len(discrepancies)} discrepancies across {len(comparisons)} engines"
            
        return ValidationResult(
            is_valid=is_valid,
            discrepancies=discrepancies,
            engine_results={self.primary_engine_type: primary, **comparisons},
            summary=summary
        )
        
    def generate_validation_report(self, inputs_list: List[ProfitCalculatorInput]) -> Dict[str, Any]:
        """
        Generate comprehensive validation report for multiple inputs
        
        Args:
            inputs_list: List of inputs to validate
            
        Returns:
            Validation report
        """
        report = {
            'total_inputs': len(inputs_list),
            'engines_tested': [self.primary_engine_type] + list(self.comparison_engines.keys()),
            'tolerance': self.tolerance,
            'results': [],
            'summary': {
                'valid_count': 0,
                'invalid_count': 0,
                'common_discrepancies': {}
            }
        }
        
        for i, inputs in enumerate(inputs_list):
            try:
                result = self.calculate_profit(inputs)
                validation_info = result.log_info.get('validation', {})
                
                report['results'].append({
                    'input_index': i,
                    'is_valid': validation_info.get('is_valid', False),
                    'discrepancies': validation_info.get('discrepancies', []),
                    'summary': validation_info.get('summary', '')
                })
                
                if validation_info.get('is_valid'):
                    report['summary']['valid_count'] += 1
                else:
                    report['summary']['invalid_count'] += 1
                    
                    # Track common discrepancies
                    for disc in validation_info.get('discrepancies', []):
                        field = disc.get('field')
                        if field not in report['summary']['common_discrepancies']:
                            report['summary']['common_discrepancies'][field] = 0
                        report['summary']['common_discrepancies'][field] += 1
                        
            except Exception as e:
                report['results'].append({
                    'input_index': i,
                    'error': str(e)
                })
                
        # Calculate summary statistics
        report['summary']['validation_rate'] = (
            report['summary']['valid_count'] / len(inputs_list) * 100
            if inputs_list else 0
        )
        
        return report
        
    def calculate_shipping(self, 
                         weight: float, 
                         dimensions: Tuple[float, float, float], 
                         price: float,
                         delivery_type: str = "pickup") -> float:
        """Calculate shipping using primary engine"""
        return self.primary_engine.calculate_shipping(weight, dimensions, price, delivery_type)
        
    def validate_connection(self) -> bool:
        """Validate all engines are ready"""
        if not self.primary_engine.validate_connection():
            return False
            
        for engine in self.comparison_engines.values():
            if not engine.validate_connection():
                return False
                
        return True
        
    def get_engine_info(self) -> Dict[str, str]:
        """Get validation engine information"""
        return {
            "name": "Validation Engine",
            "type": "validation",
            "version": "1.0",
            "description": "Cross-engine validation wrapper",
            "primary_engine": self.primary_engine_type,
            "comparison_engines": list(self.comparison_engines.keys()),
            "tolerance": f"{self.tolerance * 100}%",
            "status": "ready" if self.validate_connection() else "not ready"
        }
        
    def close(self) -> None:
        """Close all engines"""
        self.primary_engine.close()
        for engine in self.comparison_engines.values():
            engine.close()
        self.logger.info("Validation engine closed")