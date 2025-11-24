# 技术设计文档

## Context

### 背景
当前系统的任务管理功能分散在`common/task_control.py`和`cli/task_controller.py`中，与业务逻辑高度耦合。随着系统功能扩展，这种设计导致了代码重复、维护困难、扩展性差等问题。

### 约束
- 必须保持向后兼容性，不能破坏现有功能
- 需要支持现有的暂停、恢复、停止等任务控制功能
- 必须支持跨进程的任务控制能力
- 需要考虑unify-models-config-architecture提案的配置管理架构

### 利益相关者
- **开发团队**：需要更清晰、易维护的任务管理代码
- **用户**：需要稳定、响应快速的任务控制体验
- **系统**：需要解耦、可扩展的架构设计

## Goals / Non-Goals

### Goals
- 创建独立、模块化的任务管理系统
- 实现任务管理与业务逻辑的解耦
- 提供标准化的任务控制接口
- 支持事件驱动的任务状态管理
- 保持100%向后兼容性

### Non-Goals
- 重写现有的所有业务逻辑（渐进式迁移）
- 改变现有的用户界面和交互方式
- 引入复杂的分布式任务调度系统
- 破坏现有的测试和部署流程

## Decisions

### 决策1: 模块化目录结构 --> 选择这个方案
**选择**: 按职责分离创建独立的`task_manager/`模块
```
task_manager/
├── models/          # 数据模型
├── exceptions/      # 异常定义
├── controllers/     # 控制器
├── interfaces/      # 接口定义
├── mixins/         # 混入类
├── utils/          # 工具类
└── config/         # 配置管理
```

**理由**: 
- 职责清晰，便于维护和扩展
- 符合unify-models-config-architecture的设计理念
- 支持按需导入，减少依赖

**替代方案**: 
- 单文件设计 - 被拒绝，因为功能复杂度高
- 平铺结构 - 被拒绝，因为缺乏组织性

### 决策2: 简化架构设计 -> 选择简单直接的方案
**选择**: 不使用复杂的事件驱动架构，采用简单直接的状态管理方式

**理由**:
- 事件驱动架构太复杂，增加维护成本
- 项目规模适中，简单的状态管理即可满足需求
- 职责分离已经提供了足够的解耦能力

**替代方案**:
- 事件驱动架构 - 被拒绝，因为复杂度过高
- 观察者模式 - 被拒绝，因为增加不必要的复杂性

### 决策3: 适配器模式实现向后兼容 
**选择**: 创建适配器类包装新的任务管理接口，保持现有API不变

**理由**:
- 零破坏性变更，确保现有代码正常工作
- 支持渐进式迁移
- 降低迁移风险

### 决策4: 状态机管理任务生命周期
**选择**: 使用明确的状态机管理任务状态转换

**状态定义**:
```python
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    PAUSED = "paused"       # 暂停
    STOPPING = "stopping"   # 停止中
    STOPPED = "stopped"     # 已停止
    COMPLETED = "completed" # 完成
    FAILED = "failed"       # 失败
```

**理由**:
- 状态转换逻辑清晰，便于理解和维护
- 支持复杂的任务控制场景
- 便于调试和监控

## Risks / Trade-offs

### 风险1: 模块复杂度增加
**风险**: 新模块可能引入过度工程化
**缓解策略**: 采用渐进式设计，先实现核心功能，后续按需扩展

### 风险2: 迁移成本
**风险**: 现有代码迁移到新架构需要时间成本
**缓解策略**: 通过适配器保持兼容性，支持渐进式迁移，不强制一次性迁移

### 风险3: 性能开销
**风险**: 事件驱动和状态机可能带来轻微性能开销
**缓解策略**: 
- 实现性能基准测试
- 优化关键路径的执行效率
- 提供配置选项控制功能开启/关闭

### Trade-off: 复杂度 vs 扩展性
**选择**: 接受适度的复杂度换取更好的扩展性和维护性
**理由**: 长期来看，清晰的架构设计带来的维护效率提升超过短期的学习成本

## Migration Plan

### Phase 1: 创建新模块 (1-2周)
- 实现核心的task_manager模块
- 创建向后兼容的适配器
- 通过现有测试验证兼容性

### Phase 2: 集成验证 (1周)
- 集成到ScrapingOrchestrator和GoodStoreSelector
- 运行完整的功能测试
- 性能基准测试

### Phase 3: 渐进式迁移 (按需)
- 团队可以选择性地将新代码使用新接口
- 现有代码继续使用适配器，无强制迁移
- 收集使用反馈并优化

### Phase 4: 长期优化 (可选)
- 基于使用反馈优化API设计
- 逐步废弃不必要的适配器代码
- 性能优化和功能增强

### 回滚策略
- 新模块与现有代码独立，可以随时禁用
- 适配器确保现有功能始终可用
- 通过配置开关控制新功能的启用

## Open Questions

1. **事件通知的性能影响**: 需要通过基准测试确定事件系统的性能开销
2. **配置管理集成**: 如何最佳地集成unify-models-config-architecture的配置管理设计
3. **监控和调试**: 需要设计什么样的监控和调试工具来支持新的任务管理系统
4. **并发控制**: 在高并发场景下，任务状态管理的线程安全策略

## Implementation Notes

### 关键接口设计
```python
from typing import Callable, Optional
from enum import Enum
from dataclasses import dataclass

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskConfig:
    """任务配置数据类"""
    timeout: Optional[int] = None
    retry_count: int = 0
    priority: int = 0

class TaskEventListener:
    """任务事件监听器接口"""
    def on_task_started(self, task_id: str) -> None:
        pass
    
    def on_task_completed(self, task_id: str) -> None:
        pass
    
    def on_task_failed(self, task_id: str, error: Exception) -> None:
        pass

class TaskManager:
    """核心任务管理器接口"""
    def create_task(self, task_func: Callable, config: TaskConfig) -> str:
        """创建任务并返回任务ID"""
        pass
    
    def start_task(self, task_id: str) -> bool:
        """启动任务"""
        pass
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        pass
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        pass
    
    def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        pass
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        pass
    
    def subscribe_to_events(self, listener: TaskEventListener) -> None:
        """订阅任务事件"""
        pass
```

### 与现有系统的集成点
- `TaskControlMixin` -> `task_manager.mixins.TaskControlMixin`
- `TaskExecutionController` -> `task_manager.controllers.ExecutionController`  
- `TaskController` -> `task_manager.controllers.TaskController`
