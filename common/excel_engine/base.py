"""
Base classes and interfaces for calculation engines

This module defines the protocol that all calculation engines must implement.
"""

from typing import Protocol, Dict, Any, Tuple
from ..models import ProfitCalculatorInput, ProfitCalculatorResult


class CalculationEngine(Protocol):
    """Protocol for all calculation engines"""
    
    def calculate_profit(self, inputs: ProfitCalculatorInput) -> ProfitCalculatorResult:
        """
        Calculate profit based on input parameters
        
        Args:
            inputs: Input parameters for calculation
            
        Returns:
            ProfitCalculatorResult: Calculation results
        """
        ...
    
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
            float: Shipping cost in RMB
        """
        ...
    
    def validate_connection(self) -> bool:
        """
        Validate that the engine is properly configured and ready
        
        Returns:
            bool: True if engine is ready
        """
        ...
    
    def get_engine_info(self) -> Dict[str, str]:
        """
        Get information about the engine
        
        Returns:
            Dict containing engine name, version, type, etc.
        """
        ...
    
    def close(self) -> None:
        """
        Clean up any resources used by the engine
        """
        ...