"""
OZON选择器配置模块

提供OZON网站抓取所需的各种配置信息，包括：
- CSS选择器配置
- 货币符号和价格前缀词配置
- 特殊字符配置
- 浏览器配置等
"""

from .ozon_selectors_config import (
    get_ozon_selectors_config,
    OzonSelectorsConfig
)

# 导入好店筛选配置
import sys
import os
# 添加父目录到路径以导入 config.py
parent_dir = os.path.dirname(os.path.dirname(__file__))
config_file_path = os.path.join(parent_dir, 'config.py')
spec = __import__('importlib.util').util.spec_from_file_location("config_module", config_file_path)
config_module = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(config_module)
GoodStoreSelectorConfig = config_module.GoodStoreSelectorConfig
get_config = config_module.get_config

__all__ = [
    # OZON选择器配置
    'get_ozon_selectors_config',
    'OzonSelectorsConfig',
    # 好店筛选配置
    'GoodStoreSelectorConfig',
    'get_config'
]