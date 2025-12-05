"""
Excel calculation engine package

This package provides an abstraction layer for profit calculations,
supporting multiple calculation engines including xlwings, Python, and formulas.
"""

from .base import CalculationEngine
from .engine_factory import EngineFactory, create_engine
from ..models import ProfitCalculatorInput, ProfitCalculatorResult

__all__ = [
    'CalculationEngine',
    'EngineFactory',
    'create_engine',
    'ProfitCalculatorInput',
    'ProfitCalculatorResult',
]