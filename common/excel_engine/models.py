"""
Engine-specific models and configurations

This module contains non-business models that are specific to the engine implementation,
such as engine configurations and internal states.
Business models have been moved to common.models.profit_calc_models.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class EngineState:
    """Engine internal state"""
    is_initialized: bool = False
    excel_workbook_path: Optional[str] = None
    last_calculation_time: Optional[float] = None
    cache_enabled: bool = True
    
    def reset(self):
        """Reset engine state"""
        self.is_initialized = False
        self.excel_workbook_path = None
        self.last_calculation_time = None