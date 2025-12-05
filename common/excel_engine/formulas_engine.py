"""
Formulas calculation engine

This engine uses the formulas library to parse and execute Excel formulas
without requiring Excel to be installed. Cross-platform compatible.
"""

import logging
import time
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

from .base import CalculationEngine
from ..models import ProfitCalculatorInput, ProfitCalculatorResult, EngineError

# Import formulas only if available
try:
    import formulas
    import openpyxl
    FORMULAS_AVAILABLE = True
except ImportError:
    FORMULAS_AVAILABLE = False
    formulas = None
    openpyxl = None


class FormulasEngine(CalculationEngine):
    """Formulas-based calculation engine"""
    
    def __init__(self, excel_file_path: str):
        """
        Initialize formulas engine with Excel file
        
        Args:
            excel_file_path: Path to Excel calculator file
        """
        self.logger = logging.getLogger(f"{__name__}.FormulasEngine")
        
        if not FORMULAS_AVAILABLE:
            raise EngineError("formulas library not installed. Please install with: pip install formulas openpyxl")
            
        self.excel_file_path = Path(excel_file_path)
        if not self.excel_file_path.exists():
            raise EngineError(f"Excel file not found: {excel_file_path}")
            
        self._initialized = False
        self.model = None
        self._initialize()
        
    def _initialize(self):
        """Initialize formulas model from Excel file"""
        try:
            self.logger.info(f"Loading Excel model: {self.excel_file_path}")
            
            # Load Excel file with formulas
            self.model = formulas.ExcelModel().loads(str(self.excel_file_path)).finish()
            
            # Get available sheets
            self.sheets = list(self.model.books[0].sheets.keys())
            self.logger.info(f"Loaded sheets: {self.sheets}")
            
            # Identify calculation sheet
            if "利润计算表" in self.sheets:
                self.calc_sheet = "利润计算表"
            else:
                self.calc_sheet = self.sheets[0] if self.sheets else None
                
            self._initialized = True
            self.logger.info("Formulas engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize formulas engine: {e}")
            raise EngineError(f"Failed to initialize formulas engine: {e}")
            
    def calculate_profit(self, inputs: ProfitCalculatorInput) -> ProfitCalculatorResult:
        """
        Calculate profit using formulas library
        
        Args:
            inputs: Calculation inputs
            
        Returns:
            Calculation results
        """
        if not self._initialized:
            raise EngineError("Formulas engine not initialized")
            
        start_time = time.time()
        
        try:
            # Set input values in the model
            sheet_name = f"'{self.calc_sheet}'"
            
            # Map inputs to cells (based on discovered Excel structure)
            self.model.set_value(f"{sheet_name}!A11", inputs.list_price)
            self.model.set_value(f"{sheet_name}!B11", inputs.purchase_price)
            
            # Set product attributes
            self.model.set_value(f"{sheet_name}!H2", inputs.weight)  # Weight cell
            self.model.set_value(f"{sheet_name}!H3", inputs.commission_rate)  # Commission rate
            
            # Calculate
            self.model.calculate()
            
            # Read results
            profit_amount = float(self.model.get_value(f"{sheet_name}!G11") or 0)
            shipping_cost = float(self.model.get_value(f"{sheet_name}!C11") or 0)
            label_fee = float(self.model.get_value(f"{sheet_name}!D11") or 0)
            commission_amount = float(self.model.get_value(f"{sheet_name}!E11") or 0)
            
            # Calculate profit rate
            if inputs.purchase_price > 0:
                profit_rate = (profit_amount / inputs.purchase_price) * 100
            else:
                profit_rate = 0.0
                
            calculation_time = time.time() - start_time
            
            return ProfitCalculatorResult(
                profit_amount=profit_amount,
                profit_rate=profit_rate,
                is_loss=profit_amount < 0,
                shipping_cost=shipping_cost,
                commission_amount=commission_amount,
                engine_used="formulas",
                input_summary=inputs.to_dict(),
                calculation_time=calculation_time,
                log_info={
                    'engine': 'formulas',
                    'excel_file': str(self.excel_file_path),
                    'sheet': self.calc_sheet,
                    'breakdown': {
                        'list_price': inputs.list_price,
                        'purchase_price': inputs.purchase_price,
                        'shipping_cost': shipping_cost,
                        'label_fee': label_fee,
                        'commission_amount': commission_amount
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Calculation failed: {e}")
            raise EngineError(f"Formulas calculation failed: {e}")
            
    def calculate_shipping(self, 
                         weight: float, 
                         dimensions: Tuple[float, float, float], 
                         price: float,
                         delivery_type: str = "pickup") -> float:
        """
        Calculate shipping cost using formulas
        
        Args:
            weight: Weight in grams
            dimensions: (length, width, height) in cm
            price: Product price in RMB
            delivery_type: "pickup" or "delivery"
            
        Returns:
            Shipping cost in RMB
        """
        if not self._initialized:
            raise EngineError("Formulas engine not initialized")
            
        try:
            sheet_name = f"'{self.calc_sheet}'"
            
            # Set inputs
            self.model.set_value(f"{sheet_name}!H2", weight)
            self.model.set_value(f"{sheet_name}!H4", delivery_type)
            
            # Calculate
            self.model.calculate()
            
            # Read shipping cost
            shipping_cost = float(self.model.get_value(f"{sheet_name}!C11") or 0)
            
            return shipping_cost
            
        except Exception as e:
            self.logger.error(f"Shipping calculation failed: {e}")
            raise EngineError(f"Shipping calculation failed: {e}")
            
    def validate_connection(self) -> bool:
        """
        Validate that the engine is properly configured and ready
        
        Returns:
            True if engine is ready
        """
        if not self._initialized or not self.model:
            return False
            
        try:
            # Test by getting a value
            sheet_name = f"'{self.calc_sheet}'"
            test_value = self.model.get_value(f"{sheet_name}!A1")
            return True
        except Exception:
            return False
            
    def get_engine_info(self) -> Dict[str, str]:
        """
        Get information about the engine
        
        Returns:
            Dict containing engine name, version, type, etc.
        """
        return {
            "name": "Formulas Calculation Engine",
            "type": "formulas",
            "version": formulas.__version__ if FORMULAS_AVAILABLE else "not available",
            "status": "initialized" if self._initialized else "not initialized",
            "description": "Excel formula parser and executor",
            "platform_support": "all",
            "excel_file": str(self.excel_file_path) if hasattr(self, 'excel_file_path') else "not set",
            "sheets_loaded": self.sheets if hasattr(self, 'sheets') else [],
        }
        
    def close(self) -> None:
        """
        Clean up formulas resources
        """
        self.model = None
        self._initialized = False
        self.logger.info("Formulas engine closed")
        
    def get_formula(self, cell_reference: str) -> Optional[str]:
        """
        Get the formula for a specific cell
        
        Args:
            cell_reference: Cell reference (e.g., "G11" or "'Sheet'!G11")
            
        Returns:
            Formula string or None if not found
        """
        if not self._initialized:
            return None
            
        try:
            # Ensure proper sheet reference
            if "!" not in cell_reference:
                cell_reference = f"'{self.calc_sheet}'!{cell_reference}"
                
            cell = self.model.get(cell_reference)
            if cell and hasattr(cell, 'formula'):
                return cell.formula
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get formula for {cell_reference}: {e}")
            return None