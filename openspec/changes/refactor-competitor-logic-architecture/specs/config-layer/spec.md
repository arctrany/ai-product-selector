# Spec: 配置层统一管理

## Summary

建立统一的配置层管理系统，完善 `BaseSelectorConfig` 基类，确保所有 Selectors（OzonSelectors、SeerfarSelectors 等）统一继承和管理，提高配置的一致性和可维护性。

## Motivation

### 当前问题
- **配置管理分散**: OzonSelectors 和其他 Selectors 配置管理分散，缺乏统一的继承体系
- **配置不一致**: 不同 Selectors 的配置格式和接口不统一，增加维护难度
- **缺乏验证**: 配置加载缺乏统一的验证机制，容易出现配置错误

### 预期收益
- **统一管理**: 建立完整的配置继承体系，便于维护和扩展
- **降低风险**: 统一配置验证和错误处理机制，降低配置错误风险
- **提高效率**: 配置复用和覆盖机制，提高开发效率

## Detailed Design

### 核心接口设计

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class BaseSelectorConfig(ABC):
    """选择器配置基类"""
    
    @abstractmethod
    def get_selector(self, category: str, key: str) -> Optional[str]:
        """获取单个选择器"""
        pass
    
    @abstractmethod  
    def validate_config(self) -> List[str]:
        """验证配置有效性，返回错误列表"""
        pass
    
    @abstractmethod
    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        """批量获取选择器"""
        pass
    
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return len(self.validate_config()) == 0
```

### 继承实现

```python
class OzonSelectorsConfig(BaseSelectorConfig):
    """OZON平台选择器配置"""
    
    def __init__(self):
        self._selector_map = self._load_selectors()
    
    def get_selector(self, category: str, key: str) -> Optional[str]:
        return self._selector_map.get(category, {}).get(key)
    
    def validate_config(self) -> List[str]:
        errors = []
        if not self._selector_map:
            errors.append("Selector map is empty")
        return errors
    
    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        return self._selector_map.get(category)
    
    def _load_selectors(self) -> Dict[str, Dict[str, str]]:
        # 实现选择器加载逻辑
        pass

class SeerfarSelectorsConfig(BaseSelectorConfig):
    """Seerfar平台选择器配置"""
    
    def __init__(self):
        self._selector_map = self._load_selectors()
    
    def get_selector(self, category: str, key: str) -> Optional[str]:
        return self._selector_map.get(category, {}).get(key)
    
    def validate_config(self) -> List[str]:
        errors = []
        if not self._selector_map:
            errors.append("Selector map is empty")
        return errors
    
    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        return self._selector_map.get(category)
    
    def _load_selectors(self) -> Dict[str, Dict[str, str]]:
        # 实现选择器加载逻辑
        pass
```

### 配置管理策略

#### 配置优先级
1. **环境变量** (最高优先级)
2. **配置文件**
3. **默认值** (最低优先级)

#### 配置加载流程
```python
class ConfigManager:
    def load_config(self, config_class: type) -> BaseSelectorConfig:
        # 1. 加载默认配置
        config = config_class()
        
        # 2. 覆盖配置文件设置
        self._apply_file_config(config)
        
        # 3. 覆盖环境变量设置
        self._apply_env_config(config)
        
        # 4. 验证最终配置
        errors = config.validate_config()
        if errors:
            raise ConfigValidationError(errors)
        
        return config
```

## Requirements

### ADDED

#### REQ-001: 基类接口统一
**Status**: ADDED  
**Description**: 完善 `BaseSelectorConfig` 基类设计，定义统一的配置接口
- 实现 `get_selector()` 方法获取单个选择器
- 实现 `validate_config()` 方法验证配置有效性
- 实现 `get_selectors()` 方法批量获取选择器
- 添加 `is_valid()` 便捷方法检查配置状态

#### REQ-002: 继承关系标准化
**Status**: ADDED  
**Description**: 确保所有 Selectors 配置类继承 `BaseSelectorConfig`
- `OzonSelectorsConfig` 继承统一接口
- `SeerfarSelectorsConfig` 继承统一接口
- 其他未来的 Selectors 配置必须继承基类

#### REQ-003: 配置验证体系
**Status**: ADDED  
**Description**: 建立统一配置验证和错误处理机制
- 配置加载时自动验证
- 标准化错误信息格式
- 配置验证失败时提供详细错误信息

#### REQ-004: 配置优先级管理
**Status**: ADDED  
**Description**: 实现配置优先级管理系统
- 环境变量 > 配置文件 > 默认值
- 支持配置热更新和动态加载
- 配置覆盖机制的完整实现

#### REQ-005: 跨平台兼容性
**Status**: ADDED  
**Description**: 确保配置系统跨平台兼容
- Windows、Linux、macOS 平台兼容
- 路径分隔符适配
- 环境变量名称规范化

## Testing Strategy

### 单元测试
- 基类接口测试
- 各继承类功能测试
- 配置验证逻辑测试
- 优先级加载测试

### 集成测试
- 多平台配置加载测试
- 配置错误处理测试
- 热更新机制测试

### 测试覆盖率目标
- 单元测试覆盖率 ≥ 95%
- 配置验证逻辑覆盖率 = 100%
- 错误处理路径覆盖率 ≥ 90%

## Rollout Plan

### 阶段1: 基础设施 (1周)
- 完善 `BaseSelectorConfig` 基类
- 实现配置管理器 `ConfigManager`
- 建立配置验证框架

### 阶段2: 迁移现有配置 (1周)  
- 重构 `OzonSelectorsConfig` 继承基类
- 重构 `SeerfarSelectorsConfig` 继承基类
- 更新所有配置使用方式

### 阶段3: 测试验证 (3天)
- 全面单元测试和集成测试
- 跨平台兼容性验证
- 性能测试和优化

### 风险缓解
- 保持向后兼容性，分阶段迁移
- 详细的回滚计划
- 充分的测试验证

## Metrics

### 成功指标
- ✅ 所有 Selectors 配置继承 `BaseSelectorConfig`
- ✅ 配置验证错误率 < 1%
- ✅ 配置加载性能提升 ≥ 20%
- ✅ 代码重复率降低 ≥ 30%

### 监控指标
- 配置加载成功率
- 配置验证失败次数
- 配置更新频率
- 配置相关错误日志
