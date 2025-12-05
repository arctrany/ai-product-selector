"""
Engine factory for creating calculation engines

This module provides factory methods for creating appropriate calculation engines
based on configuration and environment.
"""

import logging
import platform
from typing import Dict, Any, Optional
from pathlib import Path

from .base import CalculationEngine
from ..models.exceptions import EngineError
from ..config.excel_engine_config import get_engine_config


class EngineFactory:
    """Factory class for creating calculation engines"""
    
    logger = logging.getLogger(__name__)
    
    # Engine instance cache
    _engine_cache: Dict[str, CalculationEngine] = {}
    
    @classmethod
    def create_engine(cls, 
                     engine_config: Optional[Dict[str, Any]] = None,
                     force_new: bool = False) -> CalculationEngine:
        """
        Create a calculation engine based on configuration
        
        Args:
            engine_config: Engine configuration override
            force_new: Force creation of new instance (ignore cache)
            
        Returns:
            CalculationEngine: Configured calculation engine
            
        Raises:
            EngineError: If engine creation fails
        """
        # Get configuration
        if engine_config is None:
            config = get_engine_config()
            engine_type = config.get_engine_type()
        else:
            engine_type = engine_config.get("engine", "auto")
            config = None
        
        # Check cache unless forced
        cache_key = f"{engine_type}_{id(engine_config)}"
        if not force_new and cache_key in cls._engine_cache:
            cls.logger.debug(f"Returning cached engine: {engine_type}")
            return cls._engine_cache[cache_key]
        
        # Create engine
        if engine_type == "auto":
            engine = cls._create_auto_engine(config or engine_config)
        elif engine_type == "python":
            engine = cls._create_python_engine()
        elif engine_type == "xlwings":
            engine = cls._create_xlwings_engine(config)
        elif engine_type == "formulas":
            engine = cls._create_formulas_engine(config)
        else:
            raise EngineError(f"Unknown engine type: {engine_type}")
        
        # Cache if enabled
        if config and config.is_cache_enabled():
            cls._engine_cache[cache_key] = engine
        
        cls.logger.info(f"Created engine: {engine.get_engine_info()}")
        return engine
    
    @classmethod
    def _create_auto_engine(cls, config: Any) -> CalculationEngine:
        """Auto-detect best available engine"""
        system = platform.system()
        
        # Linux - only Python engine available
        if system == "Linux":
            cls.logger.info("Linux detected, using Python engine")
            return cls._create_python_engine()
        
        # Windows/macOS - try xlwings first
        if system in ["Windows", "Darwin"]:
            try:
                return cls._create_xlwings_engine(config)
            except Exception as e:
                cls.logger.warning(f"Failed to create xlwings engine: {e}")
        
        # Fallback to Python engine
        cls.logger.info("Falling back to Python engine")
        return cls._create_python_engine()
    
    @classmethod
    def _create_python_engine(cls) -> CalculationEngine:
        """Create Python calculation engine"""
        try:
            from .python_engine import PythonEngine
            return PythonEngine()
        except ImportError as e:
            raise EngineError(f"Failed to import Python engine: {e}")
    
    @classmethod
    def _create_xlwings_engine(cls, config: Any) -> CalculationEngine:
        """Create xlwings calculation engine"""
        try:
            import xlwings  # Test import
            from .xlwings_engine import XlwingsEngine

            if config:
                calculator_path = config.get_calculator_path()
            else:
                # No fallback - require explicit configuration for security
                raise EngineError(
                    "Calculator path not configured. "
                    "Please configure calculator_identifier in EngineConfig "
                    "or set CALCULATOR_IDENTIFIER environment variable."
                )

            return XlwingsEngine(str(calculator_path))

        except ImportError:
            raise EngineError("xlwings not installed. Please install with: pip install xlwings")
        except Exception as e:
            raise EngineError(f"Failed to create xlwings engine: {e}")
    
    @classmethod
    def _create_formulas_engine(cls, config: Any) -> CalculationEngine:
        """Create formulas calculation engine"""
        try:
            import formulas  # Test import
            from .formulas_engine import FormulasEngine

            if config:
                calculator_path = config.get_calculator_path()
            else:
                # No fallback - require explicit configuration for security
                raise EngineError(
                    "Calculator path not configured. "
                    "Please configure calculator_identifier in EngineConfig "
                    "or set CALCULATOR_IDENTIFIER environment variable."
                )

            return FormulasEngine(str(calculator_path))

        except ImportError:
            raise EngineError("formulas not installed. Please install with: pip install formulas")
        except Exception as e:
            raise EngineError(f"Failed to create formulas engine: {e}")
    
    @classmethod
    def clear_cache(cls):
        """Clear engine cache"""
        count = len(cls._engine_cache)
        
        # Close cached engines
        for engine in cls._engine_cache.values():
            try:
                engine.close()
            except Exception as e:
                cls.logger.warning(f"Error closing cached engine: {e}")
        
        cls._engine_cache.clear()
        cls.logger.info(f"Cleared {count} cached engines")


# Module-level function for convenience
def create_engine(engine_type: Optional[str] = None) -> CalculationEngine:
    """
    Create a calculation engine
    
    Args:
        engine_type: Engine type override ("auto", "python", "xlwings", "formulas")
        
    Returns:
        CalculationEngine: Configured engine
    """
    config = {"engine": engine_type} if engine_type else None
    return EngineFactory.create_engine(config)