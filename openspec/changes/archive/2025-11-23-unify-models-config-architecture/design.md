# 技术设计文档 - 独立模块化版本

## Context

### 背景
当前系统的模型和配置管理存在严重的架构问题：
1. **模型层问题**: 重复定义、职责混乱，common/models.py文件过于庞大
2. **配置层问题**: 分散在多个文件中，缺乏统一管理和清晰边界
3. **模块化不足**: 缺乏独立模块的model和config支持，导致高耦合
4. **冲突风险**: 多个模块共用model和config存在命名冲突风险

**新需求**: 用户要求cli、task等独立模块可以持有独立的model.py、config.py以及config目录，但model和config绝对不能有冲突。同时要求RPA模块作为成熟稳定组件不做任何更改，并避免新旧架构并存。

### 约束
- **零冲突原则**: model和config绝对不能有冲突
- **最小改动**: 避免大量的改动，保持现有功能稳定
- **向后兼容**: 必须保持向后兼容性，不能破坏现有功能
- **渐进迁移**: 支持模块逐步迁移，不强制一次性全部重构

### 利益相关者
- **开发团队**: 需要独立模块开发能力和清晰的代码结构
- **架构团队**: 需要解耦的模块化架构和标准化规范
- **测试团队**: 需要稳定的接口和完整的测试覆盖
- **产品团队**: 需要功能稳定性和向后兼容性

## Goals / Non-Goals

### Goals
- **模块独立化**: 实现cli、task、common三模块的完全独立model和config
- **零冲突保证**: 确保model和config在各模块间绝对不发生命名冲突
- **彻底清除**: 完全移除旧架构，避免新旧两套并存维护负担
- **解耦架构**: 建立清晰的模块边界和依赖层级关系
- **统一规范**: 建立统一的命名规范和导入规范
- **RPA保护**: 确保RPA模块完全不受影响，保持稳定

### Non-Goals
- 不对RPA模块进行任何形式的更改或重构
- 不改变现有的业务逻辑和功能实现
- 不保留旧架构的向后兼容机制（彻底清除）
- 不引入复杂的配置管理框架
- 不进行大规模的性能重构

## Decisions

### 决策1: 独立模块化架构设计
**选择**: CLI、Task、Common三模块拥有独立的models.py、config.py、config/目录
```
cli/models.py, cli/config.py, cli/config/
task_manager/models.py, task_manager/config.py, task_manager/config/  
common/models.py, common/config.py, common/config/

注: RPA模块保持现有架构不变
```

**理由**: 
- 完全避免模块间model和config冲突
- 支持模块独立演进和维护
- 符合微服务化的模块化设计理念
- 最小化模块间耦合度

**替代方案**: 
- 继续共享model/config - 被拒绝，因为存在冲突风险
- 集中式管理 - 被拒绝，因为不符合独立化需求

### 决策2: 命名冲突避免策略
**选择**: 采用类名前缀 + 命名空间隔离的双重策略
```python
# 类名前缀策略
class CliConfig, class TaskConfig, class CommonConfig

# 命名空间导入策略  
from cli.models import CliConfig
from task_manager.models import TaskConfig
from common.models import CommonConfig

# RPA模块保持现有导入方式不变
from rpa.browser.core.models import BrowserConfig
```

**理由**:
- 双重保险机制确保绝对零冲突
- 即使在同一文件中导入也不会冲突
- 代码可读性好，一目了然知道来源模块

**替代方案**:
- 只使用命名空间隔离 - 被拒绝，存在同名导入冲突风险
- 只使用前缀 - 被拒绝，不够直观明确

### 决策3: 分层依赖管理  
**选择**: 建立3层依赖架构（RPA独立）
```
Level 1: common/ (基础层，无业务模块依赖)
Level 2: task_manager/ (中间层，可依赖common)
Level 3: cli/ (应用层，可依赖common和task_manager)

独立: rpa/ (成熟模块，独立维护，其他模块可依赖但不参与重构)
```

**理由**: 
- 避免循环依赖，依赖关系清晰
- 共享基础组件在底层，避免重复
- 支持模块独立演进

**替代方案**:
- 平级模块设计 - 被拒绝，因为存在循环依赖风险
- 更多层级 - 被拒绝，因为增加不必要的复杂度

### 决策4: 彻底清除旧架构
**选择**: 直接替换旧架构，彻底清除兼容机制
```python
# 直接移除旧架构文件
rm common/models.py common/config.py

# 更新所有导入语句
# 从: from common.models import StoreInfo  
# 到: from common.models import CommonStoreInfo

# 统一使用新命名空间，无兼容性代码
```

**理由**:
- 避免长期维护两套架构的复杂性
- 统一代码结构，提升可维护性
- 降低团队学习成本和维护负担

**替代方案**:
- 保持向后兼容 - 被拒绝，增加长期维护成本
- 渐进式迁移 - 被拒绝，导致新旧并存问题

## Migration Plan

### Phase 1: 创建独立模块化架构 (1-2周)
- 为每个模块创建独立的models.py、config.py、config/目录
- 实现命名前缀策略，确保零冲突
- 创建向后兼容的适配器
- 通过现有测试验证兼容性

### Phase 2: 集成验证 (1周)
- 验证分层依赖关系
- 运行完整的功能测试
- 性能基准测试

### Phase 3: 渐进式迁移支持 (按需)
- 团队可以选择性地将新代码使用新模块
- 现有代码继续使用适配器，无强制迁移
- 收集使用反馈并优化

### Phase 4: 长期优化 (可选)
- 基于使用反馈优化模块设计
- 逐步废弃不必要的适配器代码
- 性能优化和功能增强

## Implementation Notes

### 核心架构示例
```python
# cli/models.py
from dataclasses import dataclass

@dataclass
class CliAppState:
    current_view: str
    is_loading: bool

@dataclass 
class CliUIConfig:
    theme: str = "default"
    language: str = "zh-CN"

# task_manager/models.py
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"

@dataclass
class TaskInfo:
    task_id: str
    status: TaskStatus
    progress: float = 0.0

# 命名空间导入示例
from cli.models import CliAppState, CliUIConfig
from task_manager.models import TaskInfo, TaskStatus
from rpa.models import RpaBrowserConfig
from common.models import CommonStoreInfo
```

### 依赖关系管理
```python
# 分层依赖示例
# common/models.py - Level 1 基础层
@dataclass
class CommonStoreInfo:
    store_id: str
    store_name: str

# task_manager/models.py - Level 2 中间层  
from common.models import CommonStoreInfo

@dataclass
class TaskConfig:
    task_type: str
    target_stores: List[CommonStoreInfo]  # 可依赖common

# cli/models.py - Level 3 应用层
from common.models import CommonStoreInfo
from task_manager.models import TaskInfo

@dataclass  
class CliSession:
    current_stores: List[CommonStoreInfo]  # 可依赖common
    active_tasks: List[TaskInfo]  # 可依赖task_manager
```
