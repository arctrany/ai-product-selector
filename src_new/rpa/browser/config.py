"""
Configuration Module - RPA配置管理

这个模块提供了RPA系统的配置管理功能。
"""

from typing import Dict, Any, Optional, Union
import json
import os
from pathlib import Path


class RPAConfig:
    """
    RPA配置管理类
    
    提供统一的配置管理接口，支持多种配置源和动态配置更新。
    """
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None, overrides: Optional[Dict[str, Any]] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
            overrides: 覆盖配置字典
        """
        self._config: Dict[str, Any] = {}
        self._default_config = self._get_default_config()
        
        # 加载默认配置
        self._config.update(self._default_config)
        
        # 加载配置文件
        if config_file:
            self._load_config_file(config_file)
        
        # 应用覆盖配置
        if overrides:
            self._config.update(overrides)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {
            # 浏览器配置
            'backend': 'playwright',
            'browser_type': 'chromium',
            'headless': True,
            'viewport': {
                'width': 1920,
                'height': 1080
            },
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # 超时配置
            'timeout': {
                'default': 30000,
                'navigation': 30000,
                'element_wait': 10000
            },
            
            # 日志配置
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': None
            },
            
            # 截图配置
            'screenshot': {
                'full_page': False,
                'quality': 90,
                'format': 'png'
            },
            
            # 调试配置
            'debug': {
                'enabled': False,
                'port': 9222,
                'slow_mo': 0
            },
            
            # 性能配置
            'performance': {
                'enable_tracing': False,
                'enable_metrics': False,
                'memory_limit': None
            },
            
            # 网络配置
            'network': {
                'offline': False,
                'download_path': None,
                'proxy': None
            },
            
            # 安全配置
            'security': {
                'ignore_https_errors': False,
                'bypass_csp': False
            }
        }
    
    def _load_config_file(self, config_file: Union[str, Path]):
        """
        从文件加载配置
        
        Args:
            config_file: 配置文件路径
        """
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    if config_path.suffix.lower() == '.json':
                        file_config = json.load(f)
                    else:
                        # 支持其他格式的配置文件
                        raise ValueError(f"Unsupported config file format: {config_path.suffix}")
                    
                    self._config.update(file_config)
        except Exception as e:
            raise ValueError(f"Failed to load config file {config_file}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置最终值
        config[keys[-1]] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """
        批量更新配置
        
        Args:
            config_dict: 配置字典
        """
        self._deep_update(self._config, config_dict)
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """
        深度更新字典
        
        Args:
            base_dict: 基础字典
            update_dict: 更新字典
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            Dict[str, Any]: 完整配置字典
        """
        return self._config.copy()
    
    def has(self, key: str) -> bool:
        """
        检查配置键是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否存在
        """
        return self.get(key) is not None
    
    def remove(self, key: str) -> bool:
        """
        删除配置键
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否成功删除
        """
        try:
            keys = key.split('.')
            config = self._config
            
            # 导航到最后一级的父级
            for k in keys[:-1]:
                if k not in config:
                    return False
                config = config[k]
            
            # 删除最终键
            if keys[-1] in config:
                del config[keys[-1]]
                return True
            
            return False
        except Exception:
            return False
    
    def save_to_file(self, file_path: Union[str, Path]):
        """
        保存配置到文件
        
        Args:
            file_path: 文件路径
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Failed to save config to {file_path}: {e}")
    
    def load_from_env(self, prefix: str = 'RPA_'):
        """
        从环境变量加载配置
        
        Args:
            prefix: 环境变量前缀
        """
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower().replace('_', '.')
                
                # 尝试转换值类型
                try:
                    # 尝试解析为JSON
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    # 尝试解析为布尔值
                    if value.lower() in ('true', 'false'):
                        parsed_value = value.lower() == 'true'
                    # 尝试解析为数字
                    elif value.isdigit():
                        parsed_value = int(value)
                    elif '.' in value and value.replace('.', '').isdigit():
                        parsed_value = float(value)
                    else:
                        parsed_value = value
                
                self.set(config_key, parsed_value)
    
    def validate(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 验证必需的配置项
            required_keys = ['backend', 'browser_type']
            for key in required_keys:
                if not self.has(key):
                    return False
            
            # 验证配置值的有效性
            backend = self.get('backend')
            if backend not in ['playwright', 'selenium']:
                return False
            
            browser_type = self.get('browser_type')
            if browser_type not in ['chromium', 'firefox', 'webkit', 'chrome', 'edge']:
                return False
            
            # 验证超时配置
            timeout_config = self.get('timeout', {})
            for timeout_key, timeout_value in timeout_config.items():
                if not isinstance(timeout_value, (int, float)) or timeout_value <= 0:
                    return False
            
            return True
        except Exception:
            return False
    
    def reset_to_defaults(self):
        """重置配置为默认值"""
        self._config = self._get_default_config().copy()
    
    def merge_with_defaults(self):
        """将当前配置与默认配置合并"""
        default_config = self._get_default_config()
        merged_config = default_config.copy()
        self._deep_update(merged_config, self._config)
        self._config = merged_config
    
    def __str__(self) -> str:
        """字符串表示"""
        return json.dumps(self._config, indent=2, ensure_ascii=False)
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"RPAConfig({len(self._config)} keys)"
    
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """支持字典式设置"""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.has(key)