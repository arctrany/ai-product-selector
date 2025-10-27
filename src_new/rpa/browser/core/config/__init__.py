"""
配置管理模块

提供统一的配置管理功能，包括：
- 统一配置管理器
- 配置修复器
- 配置验证器
"""

from .unified_config_manager import (
    UnifiedConfigManager,
    ConfigPriority,
    ConfigSource,
    create_unified_config_manager
)

from .config_fixer import (
    ConfigFixer,
    fix_config_dict,
    validate_and_fix_config,
    create_config_fixer
)

__all__ = [
    'UnifiedConfigManager',
    'ConfigPriority', 
    'ConfigSource',
    'create_unified_config_manager',
    'ConfigFixer',
    'fix_config_dict',
    'validate_and_fix_config',
    'create_config_fixer'
]