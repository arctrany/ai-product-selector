"""
配置管理器实现

基于IConfigManager接口的配置管理器实现
支持多种配置格式、作用域管理、配置验证和热更新
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from copy import deepcopy
import logging

from ..core.interfaces.config_manager import (
    IConfigManager,
    IConfigValidator,
    IConfigTransformer,
    IEnvironmentManager,
    ConfigFormat,
    ConfigScope
)
from ..core.exceptions.browser_exceptions import (
    BrowserError,
    ConfigurationError
)


class ConfigManager(IConfigManager):
    """配置管理器实现 - 支持多种配置格式和作用域管理"""
    
    def __init__(self, debug_mode: bool = False):
        """
        初始化配置管理器
        
        Args:
            debug_mode: 是否启用调试模式
        """
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        
        # 配置存储 - 按作用域分层存储
        self.configs = {
            ConfigScope.GLOBAL: {},
            ConfigScope.MODULE: {},
            ConfigScope.SESSION: {},
            ConfigScope.TEMPORARY: {}
        }
        
        # 配置文件路径记录
        self.config_files = {}
        
        # 配置格式映射
        self.format_handlers = {
            ConfigFormat.JSON: self._handle_json,
            ConfigFormat.YAML: self._handle_yaml,
            ConfigFormat.TOML: self._handle_toml,
            ConfigFormat.INI: self._handle_ini,
            ConfigFormat.ENV: self._handle_env
        }
        
        # 配置监听器
        self.watchers = []
        self.watch_callbacks = []
        
        print(f"🔧 配置管理器初始化完成")
        print(f"   调试模式: {'启用' if debug_mode else '禁用'}")

    async def initialize(self, config_paths: List[Union[str, Path]], format_type: ConfigFormat = ConfigFormat.JSON) -> bool:
        """
        初始化配置管理器
        
        Args:
            config_paths: 配置文件路径列表
            format_type: 配置文件格式
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            print(f"🚀 初始化配置管理器")
            print(f"   配置文件: {len(config_paths)} 个")
            print(f"   格式类型: {format_type.value}")
            
            success_count = 0
            for config_path in config_paths:
                try:
                    if await self.load_config(config_path, ConfigScope.GLOBAL):
                        success_count += 1
                        print(f"   ✅ 加载成功: {config_path}")
                    else:
                        print(f"   ⚠️ 加载失败: {config_path}")
                except Exception as e:
                    print(f"   ❌ 加载错误: {config_path} - {e}")
                    continue
            
            print(f"🎯 配置管理器初始化完成，成功加载 {success_count}/{len(config_paths)} 个配置文件")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ 配置管理器初始化失败: {e}")
            return False

    async def load_config(self, config_path: Union[str, Path], scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            scope: 配置作用域
            
        Returns:
            bool: 加载是否成功
        """
        try:
            config_path = Path(config_path)
            
            if not config_path.exists():
                if self.debug_mode:
                    print(f"⚠️ 配置文件不存在: {config_path}")
                return False
            
            # 根据文件扩展名确定格式
            format_type = self._detect_format(config_path)
            
            # 读取并解析配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            handler = self.format_handlers.get(format_type)
            if not handler:
                raise ConfigurationError(f"不支持的配置格式: {format_type}")
            
            config_data = handler(content, 'load')
            
            # 合并到指定作用域
            await self.merge_configs(config_data, scope)
            
            # 记录配置文件路径
            self.config_files[str(config_path)] = {
                'scope': scope,
                'format': format_type,
                'last_modified': config_path.stat().st_mtime
            }
            
            if self.debug_mode:
                print(f"✅ 配置文件加载成功: {config_path} -> {scope.value}")
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 配置文件加载失败: {config_path} - {e}")
            return False

    async def get_config(self, key: str = None, default: Any = None, scope: ConfigScope = ConfigScope.GLOBAL) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔的嵌套键。如果为None，返回整个配置
            default: 默认值
            scope: 配置作用域

        Returns:
            Any: 配置值
        """
        try:
            # 如果没有指定key，返回整个配置
            if key is None:
                return self.configs.get(scope, {})

            # 按优先级顺序查找配置
            search_scopes = [scope]
            if scope != ConfigScope.GLOBAL:
                search_scopes.append(ConfigScope.GLOBAL)
            
            for search_scope in search_scopes:
                config = self.configs.get(search_scope, {})
                value = self._get_nested_value(config, key)
                if value is not None:
                    return value
            
            return default
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 获取配置失败: {key} - {e}")
            return default

    async def set_config(self, key: str, value: Any, scope: ConfigScope = ConfigScope.GLOBAL, persist: bool = False) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            scope: 配置作用域
            persist: 是否持久化到文件
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if scope not in self.configs:
                self.configs[scope] = {}
            
            self._set_nested_value(self.configs[scope], key, value)
            
            if persist:
                # 查找对应的配置文件并保存
                for file_path, file_info in self.config_files.items():
                    if file_info['scope'] == scope:
                        await self.save_config(file_path, scope)
                        break
            
            if self.debug_mode:
                print(f"✅ 配置设置成功: {key} = {value} ({scope.value})")
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 配置设置失败: {key} - {e}")
            return False

    async def delete_config(self, key: str, scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        删除配置项
        
        Args:
            key: 配置键
            scope: 配置作用域
            
        Returns:
            bool: 删除是否成功
        """
        try:
            config = self.configs.get(scope, {})
            if self._delete_nested_value(config, key):
                if self.debug_mode:
                    print(f"✅ 配置删除成功: {key} ({scope.value})")
                return True
            else:
                if self.debug_mode:
                    print(f"⚠️ 配置不存在: {key} ({scope.value})")
                return False
                
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 配置删除失败: {key} - {e}")
            return False

    async def has_config(self, key: str, scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        检查配置项是否存在
        
        Args:
            key: 配置键
            scope: 配置作用域
            
        Returns:
            bool: 是否存在
        """
        try:
            config = self.configs.get(scope, {})
            return self._get_nested_value(config, key) is not None
        except:
            return False

    async def get_all_configs(self, scope: ConfigScope = ConfigScope.GLOBAL) -> Dict[str, Any]:
        """
        获取所有配置
        
        Args:
            scope: 配置作用域
            
        Returns:
            Dict[str, Any]: 所有配置
        """
        return deepcopy(self.configs.get(scope, {}))

    async def merge_configs(self, configs: Dict[str, Any], scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        合并配置
        
        Args:
            configs: 要合并的配置
            scope: 配置作用域
            
        Returns:
            bool: 合并是否成功
        """
        try:
            if scope not in self.configs:
                self.configs[scope] = {}
            
            self._deep_merge(self.configs[scope], configs)
            
            if self.debug_mode:
                print(f"✅ 配置合并成功: {len(configs)} 项 -> {scope.value}")
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 配置合并失败: {e}")
            return False

    async def validate_config(self, schema: Dict[str, Any], scope: ConfigScope = ConfigScope.GLOBAL) -> Dict[str, Any]:
        """
        验证配置
        
        Args:
            schema: 验证模式
            scope: 配置作用域
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            config = self.configs.get(scope, {})
            
            # 简单的配置验证实现
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            for key, expected_type in schema.items():
                if key in config:
                    actual_value = config[key]
                    if not isinstance(actual_value, expected_type):
                        validation_result['valid'] = False
                        validation_result['errors'].append(
                            f"配置项 '{key}' 类型错误: 期望 {expected_type.__name__}, 实际 {type(actual_value).__name__}"
                        )
                else:
                    validation_result['warnings'].append(f"配置项 '{key}' 不存在")
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"验证过程出错: {e}"],
                'warnings': []
            }

    async def save_config(self, config_path: Union[str, Path], scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径
            scope: 配置作用域
            
        Returns:
            bool: 保存是否成功
        """
        try:
            config_path = Path(config_path)
            config = self.configs.get(scope, {})
            
            # 根据文件扩展名确定格式
            format_type = self._detect_format(config_path)
            handler = self.format_handlers.get(format_type)
            
            if not handler:
                raise ConfigurationError(f"不支持的配置格式: {format_type}")
            
            # 转换配置为字符串
            content = handler(config, 'save')
            
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if self.debug_mode:
                print(f"✅ 配置保存成功: {config_path}")
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 配置保存失败: {config_path} - {e}")
            return False

    async def reload_config(self, config_path: Optional[Union[str, Path]] = None) -> bool:
        """
        重新加载配置
        
        Args:
            config_path: 配置文件路径，如果为None则重新加载所有配置
            
        Returns:
            bool: 重新加载是否成功
        """
        try:
            if config_path:
                # 重新加载指定配置文件
                file_info = self.config_files.get(str(config_path))
                if file_info:
                    return await self.load_config(config_path, file_info['scope'])
                else:
                    return await self.load_config(config_path, ConfigScope.GLOBAL)
            else:
                # 重新加载所有配置文件
                success_count = 0
                for file_path, file_info in self.config_files.items():
                    if await self.load_config(file_path, file_info['scope']):
                        success_count += 1
                
                print(f"🔄 配置重新加载完成: {success_count}/{len(self.config_files)} 个文件")
                return success_count > 0
                
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 配置重新加载失败: {e}")
            return False

    async def watch_config_changes(self, callback: callable) -> bool:
        """
        监听配置变化
        
        Args:
            callback: 变化回调函数
            
        Returns:
            bool: 监听是否成功
        """
        try:
            self.watch_callbacks.append(callback)
            
            # 简单实现：定期检查文件修改时间
            if not self.watchers:
                asyncio.create_task(self._watch_config_files())
            
            if self.debug_mode:
                print(f"✅ 配置监听启动成功")
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 配置监听启动失败: {e}")
            return False

    async def stop_watching(self) -> bool:
        """
        停止监听配置变化
        
        Returns:
            bool: 停止是否成功
        """
        try:
            self.watch_callbacks.clear()
            
            if self.debug_mode:
                print(f"✅ 配置监听停止成功")
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 配置监听停止失败: {e}")
            return False

    # ==================== 内部实现方法 ====================
    
    def _detect_format(self, config_path: Path) -> ConfigFormat:
        """根据文件扩展名检测配置格式"""
        suffix = config_path.suffix.lower()
        format_map = {
            '.json': ConfigFormat.JSON,
            '.yaml': ConfigFormat.YAML,
            '.yml': ConfigFormat.YAML,
            '.toml': ConfigFormat.TOML,
            '.ini': ConfigFormat.INI,
            '.env': ConfigFormat.ENV
        }
        return format_map.get(suffix, ConfigFormat.JSON)

    def _handle_json(self, content: Union[str, Dict], operation: str) -> Union[Dict, str]:
        """处理JSON格式配置"""
        if operation == 'load':
            return json.loads(content)
        else:  # save
            return json.dumps(content, indent=2, ensure_ascii=False)

    def _handle_yaml(self, content: Union[str, Dict], operation: str) -> Union[Dict, str]:
        """处理YAML格式配置"""
        try:
            import yaml
            if operation == 'load':
                return yaml.safe_load(content)
            else:  # save
                return yaml.dump(content, default_flow_style=False, allow_unicode=True)
        except ImportError:
            raise ConfigurationError("YAML支持需要安装PyYAML: pip install PyYAML")

    def _handle_toml(self, content: Union[str, Dict], operation: str) -> Union[Dict, str]:
        """处理TOML格式配置"""
        try:
            import toml
            if operation == 'load':
                return toml.loads(content)
            else:  # save
                return toml.dumps(content)
        except ImportError:
            raise ConfigurationError("TOML支持需要安装toml: pip install toml")

    def _handle_ini(self, content: Union[str, Dict], operation: str) -> Union[Dict, str]:
        """处理INI格式配置"""
        import configparser
        
        if operation == 'load':
            parser = configparser.ConfigParser()
            parser.read_string(content)
            result = {}
            for section in parser.sections():
                result[section] = dict(parser[section])
            return result
        else:  # save
            parser = configparser.ConfigParser()
            for section, values in content.items():
                parser[section] = values
            import io
            output = io.StringIO()
            parser.write(output)
            return output.getvalue()

    def _handle_env(self, content: Union[str, Dict], operation: str) -> Union[Dict, str]:
        """处理ENV格式配置"""
        if operation == 'load':
            result = {}
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    result[key.strip()] = value.strip()
            return result
        else:  # save
            lines = []
            for key, value in content.items():
                lines.append(f"{key}={value}")
            return '\n'.join(lines)

    def _get_nested_value(self, config: Dict, key: str) -> Any:
        """获取嵌套配置值"""
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current

    def _set_nested_value(self, config: Dict, key: str, value: Any):
        """设置嵌套配置值"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value

    def _delete_nested_value(self, config: Dict, key: str) -> bool:
        """删除嵌套配置值"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False
        
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            return True
        
        return False

    def _deep_merge(self, target: Dict, source: Dict):
        """深度合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = deepcopy(value)

    async def _watch_config_files(self):
        """监听配置文件变化"""
        while self.watch_callbacks:
            try:
                for file_path, file_info in self.config_files.items():
                    path = Path(file_path)
                    if path.exists():
                        current_mtime = path.stat().st_mtime
                        if current_mtime > file_info['last_modified']:
                            # 文件已修改，重新加载
                            await self.load_config(file_path, file_info['scope'])
                            file_info['last_modified'] = current_mtime
                            
                            # 通知回调函数
                            for callback in self.watch_callbacks:
                                try:
                                    await callback(file_path, file_info['scope'])
                                except Exception as e:
                                    if self.debug_mode:
                                        print(f"⚠️ 配置变化回调执行失败: {e}")
                
                # 每5秒检查一次
                await asyncio.sleep(5)
                
            except Exception as e:
                if self.debug_mode:
                    print(f"⚠️ 配置文件监听异常: {e}")
                await asyncio.sleep(5)


class EnvironmentManager(IEnvironmentManager):
    """环境变量管理器实现"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)

    async def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量"""
        return os.environ.get(key, default)

    async def set_env(self, key: str, value: str) -> bool:
        """设置环境变量"""
        try:
            os.environ[key] = value
            return True
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 设置环境变量失败: {key} - {e}")
            return False

    async def delete_env(self, key: str) -> bool:
        """删除环境变量"""
        try:
            if key in os.environ:
                del os.environ[key]
                return True
            return False
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 删除环境变量失败: {key} - {e}")
            return False

    async def load_env_file(self, env_file_path: Union[str, Path]) -> bool:
        """加载环境变量文件"""
        try:
            env_file_path = Path(env_file_path)
            if not env_file_path.exists():
                return False
            
            with open(env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            
            if self.debug_mode:
                print(f"✅ 环境变量文件加载成功: {env_file_path}")
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"❌ 环境变量文件加载失败: {env_file_path} - {e}")
            return False

    async def get_all_env(self, prefix: Optional[str] = None) -> Dict[str, str]:
        """获取所有环境变量"""
        if prefix:
            return {k: v for k, v in os.environ.items() if k.startswith(prefix)}
        return dict(os.environ)

    async def expand_variables(self, text: str) -> str:
        """展开环境变量"""
        return os.path.expandvars(text)