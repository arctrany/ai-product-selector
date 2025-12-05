"""
Excel engine configuration

This module provides configuration for the Excel calculation engine system,
including engine selection, performance settings, and validation options.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import yaml

from .paths import get_path_config


class EngineConfig:
    """Engine configuration management"""
    
    DEFAULT_CONFIG = {
        'engine': {
            'default': 'auto',  # auto|xlwings|python|formulas
            'fallback_order': ['xlwings', 'formulas', 'python'],
            'cache_enabled': True,
            'batch_size': 50,
            'connection_timeout': 30,  # seconds
        },
        'validation': {
            'enabled': False,
            'engines': ['xlwings', 'python'],
            'tolerance': 0.01,  # Acceptable difference in results
            'log_discrepancies': True,
        },
        'paths': {
            'calculator_identifier': 'default',
            'compiled_rules_path': 'common/excel_engine/compiled_rules.py',
        },
        'security': {
            'log_path_access': True,
            'restrict_identifiers': True,
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.path_config = get_path_config()
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        # Start with defaults
        config = self.DEFAULT_CONFIG.copy()
        
        # Try to load from file
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        file_config = yaml.safe_load(f)
                    else:
                        import json
                        file_config = json.load(f)
                
                # Deep merge with defaults
                config = self._deep_merge(config, file_config)
                self.logger.info(f"Loaded configuration from {config_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to load config from {config_path}: {e}")
        
        # Environment variable overrides
        config = self._apply_env_overrides(config)
        
        return config
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _apply_env_overrides(self, config: Dict) -> Dict:
        """Apply environment variable overrides"""
        # ENGINE_DEFAULT -> engine.default
        if 'ENGINE_DEFAULT' in os.environ:
            config['engine']['default'] = os.environ['ENGINE_DEFAULT']
            
        # ENGINE_CACHE_ENABLED -> engine.cache_enabled
        if 'ENGINE_CACHE_ENABLED' in os.environ:
            config['engine']['cache_enabled'] = os.environ['ENGINE_CACHE_ENABLED'].lower() == 'true'
            
        # VALIDATION_ENABLED -> validation.enabled
        if 'VALIDATION_ENABLED' in os.environ:
            config['validation']['enabled'] = os.environ['VALIDATION_ENABLED'].lower() == 'true'
            
        # CALCULATOR_IDENTIFIER -> paths.calculator_identifier
        if 'CALCULATOR_IDENTIFIER' in os.environ:
            config['paths']['calculator_identifier'] = os.environ['CALCULATOR_IDENTIFIER']
            
        return config
    
    def get_engine_type(self) -> str:
        """Get configured engine type"""
        return self.config['engine']['default']
    
    def get_fallback_order(self) -> list:
        """Get engine fallback order"""
        return self.config['engine']['fallback_order']
    
    def is_cache_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self.config['engine']['cache_enabled']
    
    def get_batch_size(self) -> int:
        """Get batch operation size"""
        return self.config['engine']['batch_size']
    
    def is_validation_enabled(self) -> bool:
        """Check if validation mode is enabled"""
        return self.config['validation']['enabled']
    
    def get_validation_engines(self) -> list:
        """Get engines to use for validation"""
        return self.config['validation']['engines']
    
    def get_calculator_path(self) -> Path:
        """Get path to calculator file using secure resolution"""
        identifier = self.config['paths']['calculator_identifier']
        
        # Log access if configured
        if self.config['security']['log_path_access']:
            self.logger.info(f"Resolving calculator path for identifier: {identifier}")
        
        return self.path_config.get_calculator_path(identifier)
    
    def get_compiled_rules_path(self) -> Path:
        """Get path to compiled rules file"""
        return Path(self.config['paths']['compiled_rules_path'])
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        try:
            # Validate engine type
            valid_engines = ['auto', 'xlwings', 'python', 'formulas']
            if self.config['engine']['default'] not in valid_engines:
                raise ValueError(f"Invalid engine type: {self.config['engine']['default']}")
            
            # Validate batch size
            if self.config['engine']['batch_size'] < 1:
                raise ValueError("Batch size must be at least 1")
            
            # Validate calculator identifier
            if self.config['security']['restrict_identifiers']:
                identifier = self.config['paths']['calculator_identifier']
                if identifier not in self.path_config.CALCULATOR_MAP:
                    raise ValueError(f"Invalid calculator identifier: {identifier}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return self.config.copy()

    @classmethod
    def from_file(cls, config_path: str) -> 'EngineConfig':
        """
        Create EngineConfig instance from a configuration file.

        Args:
            config_path: Path to YAML or JSON configuration file

        Returns:
            EngineConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file format is invalid
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        return cls(config_path=config_path)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'EngineConfig':
        """
        Create EngineConfig instance from a dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            EngineConfig instance
        """
        instance = cls()
        instance.config = instance._deep_merge(instance.DEFAULT_CONFIG.copy(), config_dict)
        return instance


# Global instance
_engine_config = None


def get_engine_config(config_path: Optional[str] = None) -> EngineConfig:
    """Get global engine configuration instance"""
    global _engine_config
    if _engine_config is None:
        _engine_config = EngineConfig(config_path)
    return _engine_config