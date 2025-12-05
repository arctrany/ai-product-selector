"""
Secure path configuration for calculator files

This module provides secure path resolution for Excel calculator files,
preventing path traversal attacks and unauthorized file access.
"""

import os
import logging
from pathlib import Path
from typing import Dict


class SecurePathConfig:
    """Secure path configuration with validation"""
    
    # Allowed base directories for calculator files
    ALLOWED_DIRS = [
        '/app/data/calculators/',
        '/opt/ai-product-selector/calculators/',
        # For development/testing
        os.path.join(os.path.dirname(__file__), '../../docs/'),
        os.path.join(os.path.dirname(__file__), '../../tests/resources/'),
    ]
    
    # Calculator identifier mapping
    CALCULATOR_MAP = {
        'default': 'profits_calculator.xlsx',
        'test': 'test_calculator.xlsx',
        'v4': '利润表V4版本.xlsx',
    }
    
    @staticmethod
    def get_calculator_filename(identifier: str) -> str:
        """Get calculator filename by identifier"""
        if identifier not in SecurePathConfig.CALCULATOR_MAP:
            from ..models.exceptions import ConfigurationError
            raise ConfigurationError(f"Unknown calculator identifier: {identifier}")
        return SecurePathConfig.CALCULATOR_MAP[identifier]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._resolved_paths: Dict[str, Path] = {}
        self._validate_allowed_dirs()
    
    def _validate_allowed_dirs(self):
        """Validate and normalize allowed directories"""
        normalized_dirs = []
        for dir_path in self.ALLOWED_DIRS:
            try:
                # Resolve to absolute path
                abs_path = Path(dir_path).resolve()
                if abs_path.exists() and abs_path.is_dir():
                    normalized_dirs.append(abs_path)
                    self.logger.debug(f"Allowed directory validated: {abs_path}")
            except Exception as e:
                self.logger.warning(f"Failed to validate directory {dir_path}: {e}")
        
        self.ALLOWED_DIRS = normalized_dirs
    
    def get_calculator_path(self, identifier: str) -> Path:
        """
        Get calculator path by secure identifier

        Args:
            identifier: Calculator identifier (e.g., 'default', 'test')

        Returns:
            Path: Validated path to calculator file

        Raises:
            ConfigurationError: If identifier is invalid or path is not secure
        """
        from ..models.exceptions import ConfigurationError

        # Check cache
        if identifier in self._resolved_paths:
            return self._resolved_paths[identifier]

        # Validate identifier
        if identifier not in self.CALCULATOR_MAP:
            raise ConfigurationError(f"Unknown calculator identifier: {identifier}")
        
        filename = self.CALCULATOR_MAP[identifier]
        
        # Search for file in allowed directories
        for base_dir in self.ALLOWED_DIRS:
            file_path = base_dir / filename
            if file_path.exists():
                # Validate security
                if self._validate_path_security(file_path):
                    self._resolved_paths[identifier] = file_path
                    self.logger.info(f"Resolved calculator '{identifier}' to {file_path}")
                    return file_path
        
        raise ConfigurationError(f"Calculator file not found for identifier: {identifier}")
    
    def _validate_path_security(self, file_path: Path) -> bool:
        """
        Validate that path is secure and within allowed directories
        
        Args:
            file_path: Path to validate
            
        Returns:
            bool: True if path is secure
        """
        try:
            # Resolve to absolute path
            abs_path = file_path.resolve()
            
            # Check if path is within allowed directories
            for allowed_dir in self.ALLOWED_DIRS:
                try:
                    abs_path.relative_to(allowed_dir)
                    return True
                except ValueError:
                    continue
            
            self.logger.warning(f"Path {abs_path} is not within allowed directories")
            return False
            
        except Exception as e:
            self.logger.error(f"Path validation failed: {e}")
            return False
    
    def validate_path(self, path_str: str) -> Path:
        """
        Validate an arbitrary path string

        Args:
            path_str: Path string to validate

        Returns:
            Path if valid

        Raises:
            ConfigurationError: If path is invalid or insecure
        """
        from ..models.exceptions import ConfigurationError

        # Detect potential path traversal attempts
        if '..' in path_str or path_str.startswith('/') or '\\' in path_str:
            self.logger.warning(f"Potential path traversal attempt: {path_str}")
            raise ConfigurationError(f"Invalid path: {path_str}")

        # Validate file extension - only Excel files allowed
        valid_extensions = {'.xlsx', '.xls', '.xlsm'}
        path = Path(path_str)
        if path.suffix.lower() not in valid_extensions:
            self.logger.warning(f"Invalid file extension: {path_str}")
            raise ConfigurationError(f"Invalid file extension: {path_str}. Only Excel files (.xlsx, .xls, .xlsm) are allowed.")

        # Try to resolve as identifier first
        if path_str in self.CALCULATOR_MAP:
            return self.get_calculator_path(path_str)

        # Otherwise validate as path within allowed directories
        if self._validate_path_security(path):
            return path

        raise ConfigurationError(f"Path not within allowed directories: {path_str}")
    
    def add_calculator_mapping(self, identifier: str, filename: str):
        """
        Add a new calculator mapping (for testing/development)
        
        Args:
            identifier: New identifier
            filename: Calculator filename
        """
        if identifier in self.CALCULATOR_MAP:
            raise ValueError(f"Identifier {identifier} already exists")
        
        self.CALCULATOR_MAP[identifier] = filename
        self.logger.info(f"Added calculator mapping: {identifier} -> {filename}")


# Global instance
_path_config = None


def get_path_config() -> SecurePathConfig:
    """Get global path configuration instance"""
    global _path_config
    if _path_config is None:
        _path_config = SecurePathConfig()
    return _path_config