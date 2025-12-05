"""
XlWings calculation engine

This engine uses Excel directly via xlwings for 100% accurate calculations.
Only available on Windows and macOS with Excel installed.
"""

import logging
import time
import platform
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import atexit

from .base import CalculationEngine
from ..models import ProfitCalculatorInput, ProfitCalculatorResult, EngineError

# Import xlwings only if available
try:
    import xlwings as xw
    XLWINGS_AVAILABLE = True
except ImportError:
    XLWINGS_AVAILABLE = False
    xw = None


class XlwingsEngine(CalculationEngine):
    """Excel-based calculation engine using xlwings"""
    
    # Class-level app instance for connection pooling
    _app_instance: Optional['xw.App'] = None
    _instance_count: int = 0
    
    def __init__(self, excel_file_path: str):
        """
        Initialize xlwings engine with Excel file
        
        Args:
            excel_file_path: Path to Excel calculator file
        """
        self.logger = logging.getLogger(f"{__name__}.XlwingsEngine")
        
        # Check platform support
        system = platform.system()
        if system not in ["Windows", "Darwin"]:
            raise EngineError(f"xlwings is not supported on {system}")
            
        if not XLWINGS_AVAILABLE:
            raise EngineError("xlwings not installed. Please install with: pip install xlwings")
            
        self.excel_file_path = Path(excel_file_path)
        if not self.excel_file_path.exists():
            raise EngineError(f"Excel file not found: {excel_file_path}")
            
        self.app = None
        self.workbook = None
        self._initialized = False
        
        # Register cleanup on exit
        atexit.register(self._cleanup_on_exit)
        
    def _get_or_create_app(self) -> 'xw.App':
        """Get or create shared Excel app instance"""
        if XlwingsEngine._app_instance is None or not XlwingsEngine._app_instance.books:
            self.logger.info("Creating new Excel app instance")
            XlwingsEngine._app_instance = xw.App(visible=False, add_book=False)
            XlwingsEngine._app_instance.display_alerts = False
            XlwingsEngine._app_instance.screen_updating = False
            
        XlwingsEngine._instance_count += 1
        return XlwingsEngine._app_instance
        
    def _initialize(self):
        """Initialize Excel connection"""
        if self._initialized:
            return

        try:
            # Get or create app
            self.app = self._get_or_create_app()

            # Open workbook
            self.logger.info(f"Opening workbook: {self.excel_file_path}")
            self.workbook = self.app.books.open(str(self.excel_file_path))

            # Get reference to calculation sheet (利润计算表)
            if "利润计算表" in [sheet.name for sheet in self.workbook.sheets]:
                self.calc_sheet = self.workbook.sheets["利润计算表"]
            else:
                # Fallback to first sheet
                self.calc_sheet = self.workbook.sheets[0]

            # Get reference to shipping sheet (UNI运费)
            if "UNI运费" in [sheet.name for sheet in self.workbook.sheets]:
                self.shipping_sheet = self.workbook.sheets["UNI运费"]
            else:
                self.shipping_sheet = None
                self.logger.warning("UNI运费 sheet not found, shipping calculations may be inaccurate")

            self._initialized = True
            self.logger.info("XlWings engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize xlwings engine: {e}")
            self._cleanup()
            raise EngineError(f"Failed to initialize xlwings: {e}")
            
    def calculate_profit(self, inputs: ProfitCalculatorInput) -> ProfitCalculatorResult:
        """
        Calculate profit using Excel

        Args:
            inputs: Calculation inputs

        Returns:
            Calculation results
        """
        self._initialize()

        start_time = time.time()

        try:
            # =================================================================
            # Map inputs to Excel cells (利润计算表 Sheet)
            # Based on actual Excel structure analyzed via openpyxl:
            # =================================================================
            # A4: 重量(g), A5: 长(cm), A6: 宽(cm), A7: 高(cm)
            # A11: 定价 (list_price), B11: 采购成本 (purchase_price)
            # C11: 运费(自动计算), D11: 贴单费, E11: 平台佣金, F11: 杂费
            # G11: 利润 = A11-B11-C11-D11-E11-F11
            # =================================================================

            # Set product dimensions in 利润计算表
            self.calc_sheet.range('A4').value = inputs.weight
            self.calc_sheet.range('A5').value = inputs.length
            self.calc_sheet.range('A6').value = inputs.width
            self.calc_sheet.range('A7').value = inputs.height

            # Set pricing
            self.calc_sheet.range('A11').value = inputs.list_price
            self.calc_sheet.range('B11').value = inputs.purchase_price

            # =================================================================
            # Map inputs to UNI运费 Sheet (M列 - 运费计算输入)
            # M3: 重量(g), M4: 长(cm), M5: 宽(cm), M6: 高(cm)
            # M7: 销售价格(卢布), M8: 送货方式 ("自提点"/"送货上门")
            # =================================================================
            if self.shipping_sheet:
                self.shipping_sheet.range('M3').value = inputs.weight
                self.shipping_sheet.range('M4').value = inputs.length
                self.shipping_sheet.range('M5').value = inputs.width
                self.shipping_sheet.range('M6').value = inputs.height
                self.shipping_sheet.range('M7').value = inputs.list_price  # 销售价格(卢布)

                # Set delivery type: "自提点" or "送货上门"
                delivery_type = getattr(inputs, 'delivery_type', 'pickup')
                if delivery_type == 'pickup' or delivery_type == '自提点':
                    self.shipping_sheet.range('M8').value = "自提点"
                else:
                    self.shipping_sheet.range('M8').value = "送货上门"

            # Force Excel to recalculate
            self.app.calculate()

            # =================================================================
            # Read results from 利润计算表
            # =================================================================
            profit_amount = self.calc_sheet.range('G11').value or 0.0
            shipping_cost = self.calc_sheet.range('C11').value or 0.0
            label_fee = self.calc_sheet.range('D11').value or 0.0
            commission_amount = self.calc_sheet.range('E11').value or 0.0
            misc_fee = self.calc_sheet.range('F11').value or 0.0

            # Calculate profit rate
            if inputs.purchase_price > 0:
                profit_rate = (profit_amount / inputs.purchase_price) * 100
            else:
                profit_rate = 0.0

            calculation_time = time.time() - start_time

            return ProfitCalculatorResult(
                profit_amount=float(profit_amount),
                profit_rate=float(profit_rate),
                is_loss=profit_amount < 0,
                shipping_cost=float(shipping_cost),
                commission_amount=float(commission_amount),
                engine_used="xlwings",
                input_summary=inputs.to_dict(),
                calculation_time=calculation_time,
                log_info={
                    'engine': 'xlwings',
                    'excel_file': str(self.excel_file_path),
                    'breakdown': {
                        'list_price': inputs.list_price,
                        'purchase_price': inputs.purchase_price,
                        'shipping_cost': shipping_cost,
                        'label_fee': label_fee,
                        'commission_amount': commission_amount,
                        'misc_fee': misc_fee
                    }
                }
            )

        except Exception as e:
            self.logger.error(f"Calculation failed: {e}")
            raise EngineError(f"Excel calculation failed: {e}")
            
    def calculate_shipping(self,
                         weight: float,
                         dimensions: Tuple[float, float, float],
                         price: float,
                         delivery_type: str = "pickup") -> float:
        """
        Calculate shipping cost using Excel

        Args:
            weight: Weight in grams
            dimensions: (length, width, height) in cm
            price: Product price in RMB
            delivery_type: "pickup" or "delivery"

        Returns:
            Shipping cost in RMB
        """
        self._initialize()

        try:
            length, width, height = dimensions

            # Set inputs in 利润计算表
            self.calc_sheet.range('A4').value = weight
            self.calc_sheet.range('A5').value = length
            self.calc_sheet.range('A6').value = width
            self.calc_sheet.range('A7').value = height
            self.calc_sheet.range('A11').value = price

            # Set inputs in UNI运费 Sheet
            if self.shipping_sheet:
                self.shipping_sheet.range('M3').value = weight
                self.shipping_sheet.range('M4').value = length
                self.shipping_sheet.range('M5').value = width
                self.shipping_sheet.range('M6').value = height
                self.shipping_sheet.range('M7').value = price

                # Set delivery type
                if delivery_type == 'pickup' or delivery_type == '自提点':
                    self.shipping_sheet.range('M8').value = "自提点"
                else:
                    self.shipping_sheet.range('M8').value = "送货上门"

            # Force recalculation
            self.app.calculate()

            # Read shipping cost result from C11
            shipping_cost = self.calc_sheet.range('C11').value or 0.0

            return float(shipping_cost)

        except Exception as e:
            self.logger.error(f"Shipping calculation failed: {e}")
            raise EngineError(f"Shipping calculation failed: {e}")
            
    def validate_connection(self) -> bool:
        """
        Validate that the engine is properly configured and ready
        
        Returns:
            True if engine is ready
        """
        try:
            self._initialize()
            # Test by reading a cell
            test_value = self.calc_sheet.range('A1').value
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
            "name": "XlWings Excel Engine",
            "type": "xlwings",
            "version": xw.__version__ if XLWINGS_AVAILABLE else "not available",
            "status": "initialized" if self._initialized else "not initialized",
            "description": "Direct Excel automation via xlwings",
            "platform_support": "Windows, macOS",
            "excel_file": str(self.excel_file_path) if hasattr(self, 'excel_file_path') else "not set",
            "excel_app_running": self.app is not None,
        }
        
    def close(self) -> None:
        """
        Clean up Excel resources
        """
        self._cleanup()
        self.logger.info("XlWings engine closed")
        
    def _cleanup(self):
        """Internal cleanup method"""
        if self.workbook:
            try:
                self.workbook.close()
            except Exception as e:
                self.logger.warning(f"Error closing workbook: {e}")
            self.workbook = None
            
        # Decrement instance count
        if self.app:
            XlwingsEngine._instance_count = max(0, XlwingsEngine._instance_count - 1)
            
            # Only quit app if no other instances are using it
            if XlwingsEngine._instance_count == 0 and XlwingsEngine._app_instance:
                try:
                    XlwingsEngine._app_instance.quit()
                except Exception as e:
                    self.logger.warning(f"Error quitting Excel app: {e}")
                XlwingsEngine._app_instance = None
                
        self.app = None
        self._initialized = False
        
    def _cleanup_on_exit(self):
        """Cleanup on program exit"""
        if hasattr(self, '_initialized') and self._initialized:
            self._cleanup()
            
    def batch_calculate(self, inputs_list: list) -> list:
        """
        Perform batch calculations for better performance
        
        Args:
            inputs_list: List of ProfitCalculatorInput objects
            
        Returns:
            List of ProfitCalculatorResult objects
        """
        self._initialize()
        
        results = []
        for inputs in inputs_list:
            try:
                result = self.calculate_profit(inputs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Batch calculation failed for input: {e}")
                # Add error result
                results.append(ProfitCalculatorResult(
                    profit_amount=0.0,
                    profit_rate=0.0,
                    is_loss=True,
                    engine_used="xlwings",
                    input_summary=inputs.to_dict(),
                    calculation_time=0.0,
                    log_info={'error': str(e)}
                ))
                
        return results