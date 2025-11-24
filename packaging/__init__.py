"""
打包工具模块

包含项目构建、发布和资源路径管理工具
"""

from .resource_path import (
    get_resource_path,
    ensure_resource_exists,
    get_config_path,
    get_selectors_config_path,
    get_data_directory,
    get_output_directory,
    create_user_config_template,
    list_available_resources,
    validate_packaging_resources
)

__all__ = [
    'get_resource_path',
    'ensure_resource_exists', 
    'get_config_path',
    'get_selectors_config_path',
    'get_data_directory',
    'get_output_directory',
    'create_user_config_template',
    'list_available_resources',
    'validate_packaging_resources'
]
