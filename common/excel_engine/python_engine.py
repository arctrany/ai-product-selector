"""
Python calculation engine

This engine uses pre-compiled Python rules generated from Excel files
to perform calculations without requiring Excel or external dependencies.
"""

import logging
import time
from typing import Dict, Any, Tuple
from pathlib import Path

from .base import CalculationEngine
from ..models import ProfitCalculatorInput, ProfitCalculatorResult, EngineError
from .compiled_rules import CompiledExcelRules


class PythonEngine(CalculationEngine):
    """Python-based calculation engine using pre-compiled rules"""
    
    def __init__(self):
        """Initialize Python engine with compiled rules"""
        self.logger = logging.getLogger(f"{__name__}.PythonEngine")
        self.compiled_rules = CompiledExcelRules()
        self._initialized = False
        
        try:
            # Verify compiled rules are available
            test_result = self.compiled_rules.calculate_profit({
                'list_price': 100,
                'purchase_price': 50,
                'commission_rate': 10,
                'weight': 500,
                'length': 10,
                'width': 10,
                'height': 10,
            })
            self._initialized = True
            self.logger.info("Python engine initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Python engine: {e}")
            raise EngineError(f"Python engine initialization failed: {e}")
            
    def calculate_profit(self, inputs: ProfitCalculatorInput) -> ProfitCalculatorResult:
        """
        Calculate profit using pre-compiled Python rules
        
        Args:
            inputs: Calculation inputs
            
        Returns:
            Calculation results
        """
        if not self._initialized:
            raise EngineError("Python engine not initialized")
            
        start_time = time.time()
        
        try:
            # Validate inputs first
            inputs.validate()
            
            # Convert inputs to dictionary for compiled rules
            input_dict = {
                'list_price': inputs.list_price,
                'purchase_price': inputs.purchase_price,
                'commission_rate': inputs.commission_rate,
                'weight': inputs.weight,
                'length': inputs.length,
                'width': inputs.width,
                'height': inputs.height,
                'green_price': inputs.green_price,
                'black_price': inputs.black_price,
                'delivery_type': 'pickup',  # Default to pickup
            }
            
            # Calculate using compiled rules
            result = self.compiled_rules.calculate_profit(input_dict)
            
            # Build response
            calculation_time = time.time() - start_time
            
            return ProfitCalculatorResult(
                profit_amount=result['profit_amount'],
                profit_rate=result['profit_rate'],
                is_loss=result['is_loss'],
                shipping_cost=result['shipping_cost'],
                commission_amount=result['commission_amount'],
                engine_used="python",
                input_summary=inputs.to_dict(),
                calculation_time=calculation_time,
                log_info={
                    'engine': 'python',
                    'breakdown': result['breakdown'],
                    'compiled_rules_version': '1.0'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Calculation failed: {e}")
            raise EngineError(f"Python engine calculation failed: {e}")
            
    def calculate_shipping(self, 
                         weight: float, 
                         dimensions: Tuple[float, float, float], 
                         price: float,
                         delivery_type: str = "pickup") -> float:
        """
        Calculate shipping cost
        
        Args:
            weight: Weight in grams
            dimensions: (length, width, height) in cm
            price: Product price in RMB
            delivery_type: "pickup" or "delivery"
            
        Returns:
            Shipping cost in RMB
        """
        if not self._initialized:
            raise EngineError("Python engine not initialized")
            
        try:
            return self.compiled_rules._calculate_shipping(
                weight, dimensions, price, delivery_type
            )
        except Exception as e:
            self.logger.error(f"Shipping calculation failed: {e}")
            raise EngineError(f"Shipping calculation failed: {e}")
            
    def validate_connection(self) -> bool:
        """
        Validate that the engine is properly configured and ready
        
        Returns:
            True if engine is ready
        """
        return self._initialized
        
    def get_engine_info(self) -> Dict[str, str]:
        """
        Get information about the engine
        
        Returns:
            Dict containing engine name, version, type, etc.
        """
        return {
            "name": "Python Calculation Engine",
            "type": "python",
            "version": "1.0",
            "status": "initialized" if self._initialized else "not initialized",
            "description": "Pre-compiled Python rules from Excel",
            "platform_support": "all",
            "compiled_rules_available": hasattr(self, 'compiled_rules'),
        }
        
    def close(self) -> None:
        """
        Clean up any resources used by the engine
        """
        # Python engine doesn't need cleanup
        self.logger.info("Python engine closed")
        
    def reload_rules(self) -> None:
        """
        Reload compiled rules (useful for development)
        """
        self.logger.info("Reloading compiled rules")
        try:
            # Reload the compiled rules module
            import importlib
            from . import compiled_rules
            importlib.reload(compiled_rules)
            self.compiled_rules = compiled_rules.CompiledExcelRules()
            self.logger.info("Compiled rules reloaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to reload rules: {e}")
            raise EngineError(f"Failed to reload rules: {e}")