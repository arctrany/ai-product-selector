"""
Excel利润计算器模块（重构版）

使用新的引擎架构实现Excel利润计算功能，支持多种计算引擎。
"""

import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import models from common.models
from ..models import ProfitCalculatorInput, ProfitCalculatorResult, ExcelCalculatorError
from ..excel_engine import EngineFactory, CalculationEngine
from ..config.excel_engine_config import get_engine_config


class ExcelProfitCalculator:
    """
    Excel利润计算器主类
    
    使用新的引擎架构实现利润计算功能，支持：
    - 多种计算引擎（xlwings, Python, formulas）
    - 自动引擎选择
    - 跨平台兼容性
    - 高性能计算
    """
    
    def __init__(self, engine_config: Optional[Dict[str, Any]] = None):
        """
        初始化Excel利润计算器
        
        Args:
            engine_config: 引擎配置，可选。默认使用系统配置
        """
        self.logger = logging.getLogger(__name__)
        self.engine_config = engine_config or get_engine_config()
        
        # 创建计算引擎
        try:
            self.engine = EngineFactory.create_engine(engine_config)
            self.logger.info(f"Initialized with engine: {self.engine.get_engine_info()['type']}")
        except Exception as e:
            self.logger.error(f"Failed to create calculation engine: {e}")
            raise ExcelCalculatorError(f"Failed to initialize calculator: {e}")
            
        # 统计信息
        self._calculation_count = 0
        self._total_calculation_time = 0.0
        
    def calculate_profit(self, calculator_input: ProfitCalculatorInput) -> ProfitCalculatorResult:
        """
        执行利润计算
        
        Args:
            calculator_input: 利润计算输入参数
            
        Returns:
            ProfitCalculatorResult: 计算结果
            
        Raises:
            ExcelCalculatorError: 计算失败
        """
        try:
            # 验证输入
            calculator_input.validate()
            
            # 使用引擎计算
            result = self.engine.calculate_profit(calculator_input)
            
            # 更新统计
            self._calculation_count += 1
            self._total_calculation_time += result.calculation_time
            
            # 记录日志
            self.logger.info(
                f"计算完成: 利润={result.profit_amount:.2f}, "
                f"利润率={result.profit_rate:.2f}%, "
                f"耗时={result.calculation_time:.3f}s, "
                f"引擎={result.engine_used}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"利润计算失败: {e}")
            if isinstance(e, ExcelCalculatorError):
                raise
            raise ExcelCalculatorError(f"利润计算失败: {e}")
            
    def batch_calculate(self, inputs_list: List[ProfitCalculatorInput]) -> List[ProfitCalculatorResult]:
        """
        批量计算利润
        
        Args:
            inputs_list: 输入参数列表
            
        Returns:
            计算结果列表
        """
        results = []
        
        # Check if engine supports batch calculation
        if hasattr(self.engine, 'batch_calculate'):
            self.logger.info(f"Using batch calculation for {len(inputs_list)} items")
            return self.engine.batch_calculate(inputs_list)
            
        # Fallback to sequential calculation
        for inputs in inputs_list:
            try:
                result = self.calculate_profit(inputs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Batch calculation failed for item: {e}")
                # Add error result
                results.append(ProfitCalculatorResult(
                    profit_amount=0.0,
                    profit_rate=0.0,
                    is_loss=True,
                    engine_used=self.engine.get_engine_info()['type'],
                    input_summary=inputs.to_dict(),
                    calculation_time=0.0,
                    log_info={'error': str(e)}
                ))
                
        return results
        
    def calculate_shipping(self, weight: float, dimensions: tuple, 
                         price: float, delivery_type: str = "pickup") -> float:
        """
        计算运费
        
        Args:
            weight: 重量（克）
            dimensions: 尺寸元组 (长, 宽, 高)，单位厘米
            price: 商品价格
            delivery_type: 配送类型，"pickup" 或 "delivery"
            
        Returns:
            运费金额
        """
        try:
            return self.engine.calculate_shipping(weight, dimensions, price, delivery_type)
        except Exception as e:
            self.logger.error(f"运费计算失败: {e}")
            raise ExcelCalculatorError(f"运费计算失败: {e}")
            
    def get_engine_info(self) -> Dict[str, Any]:
        """获取当前引擎信息"""
        return self.engine.get_engine_info()
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取计算统计信息"""
        avg_time = (self._total_calculation_time / self._calculation_count 
                   if self._calculation_count > 0 else 0)
        
        return {
            "calculation_count": self._calculation_count,
            "total_calculation_time": self._total_calculation_time,
            "average_calculation_time": avg_time,
            "engine_info": self.engine.get_engine_info()
        }
        
    def switch_engine(self, engine_type: str) -> None:
        """
        切换计算引擎
        
        Args:
            engine_type: 引擎类型 ("xlwings", "python", "formulas", "auto")
        """
        self.logger.info(f"Switching engine from {self.engine.get_engine_info()['type']} to {engine_type}")
        
        # Close current engine
        self.close()
        
        # Create new engine
        config = {"engine": engine_type}
        self.engine = EngineFactory.create_engine(config)
        
        self.logger.info(f"Switched to engine: {self.engine.get_engine_info()['type']}")
        
    def validate_connection(self) -> bool:
        """验证引擎连接状态"""
        return self.engine.validate_connection()
        
    def close(self):
        """关闭计算器，释放资源"""
        if hasattr(self, 'engine') and self.engine:
            self.engine.close()
            self.logger.info("Calculator closed")
            
    def __enter__(self):
        """上下文管理器入口"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
        
    def __del__(self):
        """析构函数"""
        self.close()


# 保持向后兼容的函数式接口
def calculate_profit_simple(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    简单的利润计算接口（向后兼容）
    
    Args:
        inputs: 包含计算参数的字典
        
    Returns:
        计算结果字典
    """
    # Convert dict to ProfitCalculatorInput
    calc_input = ProfitCalculatorInput(
        black_price=inputs.get('black_price', 0),
        green_price=inputs.get('green_price', 0),
        list_price=inputs.get('list_price', 0),
        purchase_price=inputs.get('purchase_price', 0),
        commission_rate=inputs.get('commission_rate', 0),
        weight=inputs.get('weight', 0),
        length=inputs.get('length', 0),
        width=inputs.get('width', 0),
        height=inputs.get('height', 0),
    )
    
    # Use default calculator
    with ExcelProfitCalculator() as calculator:
        result = calculator.calculate_profit(calc_input)
        return result.to_dict()