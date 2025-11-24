# Change: Create Independent Task Manager

## Why

基于深度调研发现，当前任务管理功能分散在多个模块中，缺乏统一的职责分离架构，导致维护困难和扩展性差：

1. **任务管理功能分散**：任务控制功能分布在 `cli/task_controller.py`、`cli/task_control.py`、`cli/models.py`、`good_store_selector.py` 等多个文件中，缺乏清晰的职责边界
2. **职责耦合严重**：`TaskController` 直接依赖 `UIStateManager`，业务逻辑与UI状态紧密耦合，违背了职责分离原则
3. **缺乏统一抽象**：没有统一的任务管理接口，各模块直接依赖具体实现，导致代码重复和维护困难

需要按照职责分离原则，创建独立的 `task_manager` 模块，提供统一、模块化的任务管理架构。

## What Changes

按照职责分离原则，创建独立的 `task_manager` 模块，重构现有分散的任务管理功能：

- **创建独立task_manager模块**：按职责分离原则组织任务管理功能，建立清晰的模块边界
- **重构现有任务控制功能**：将分散在多个文件中的任务管理功能统一到新模块中
- **提供向后兼容接口**：通过适配器模式保证现有代码正常工作，支持渐进式迁移
- **建立标准化接口**：提供统一的任务管理API，解除模块间的紧耦合

### 核心模块架构

**独立的task_manager模块结构**：
```
task_manager/
├── __init__.py         # 模块入口
├── models.py           # 任务状态、进度等数据模型  
├── exceptions.py       # 任务管理异常定义
├── controllers.py      # 任务控制器实现
├── interfaces.py       # 任务管理接口定义
├── mixins.py          # 任务控制混入类
├── utils.py           # 任务管理工具函数
└── config.py          # 任务管理配置
```

**职责分离设计**：
- **models.py**：负责任务状态、进度信息的数据模型定义
- **controllers.py**：负责任务生命周期管理和控制逻辑
- **interfaces.py**：负责定义标准化的任务管理接口
- **mixins.py**：负责为现有类提供任务控制能力
- **exceptions.py**：负责任务管理相关的异常处理
- **config.py**：负责任务管理的配置管理

### 重构映射关系

**现有功能重构映射**：
```
cli/task_controller.py    → task_manager/controllers.py
cli/task_control.py       → task_manager/mixins.py + task_manager/interfaces.py  
cli/models.py (部分)      → task_manager/models.py
分散的状态管理           → task_manager/models.py (统一管理)
```

**适配器兼容层**：
```python
# 保持现有API不变，内部调用新的task_manager
from task_manager import TaskManager

class TaskControllerAdapter:
    """适配器类，保证现有代码正常工作"""
    def __init__(self):
        self._task_manager = TaskManager()
    
    # 现有方法保持不变，内部委托给新的TaskManager
```

## Impact

### 受影响的规范
- **ADDED**: `task-manager` - 新增独立的任务管理器规范，定义职责分离的模块架构
- **MODIFIED**: `cli` - 更新CLI模块以使用新的task_manager接口
- **MODIFIED**: `common` - 更新通用模块的任务控制部分以使用新架构

### 受影响的代码
- **ADDED**: 独立的task_manager模块
  - `task_manager/__init__.py` - 模块入口和API导出
  - `task_manager/models.py` - 任务状态、进度数据模型
  - `task_manager/controllers.py` - 任务生命周期控制器
  - `task_manager/interfaces.py` - 标准化任务管理接口
  - `task_manager/mixins.py` - 任务控制混入类
  - `task_manager/exceptions.py` - 任务管理异常定义
  - `task_manager/utils.py` - 任务管理工具函数
  - `task_manager/config.py` - 任务管理配置
- **MODIFIED**: 现有模块适配新架构
  - `cli/task_controller.py` - 重构为使用新的TaskManager接口
  - `cli/task_control.py` - 创建适配器保持向后兼容
  - `cli/models.py` - 移除任务相关状态管理，委托给task_manager
  - `good_store_selector.py` - 使用新的TaskControlMixin
- **ADDED**: 完整测试覆盖
  - `tests/task_manager/` - 新模块的完整测试套件

### 核心改进效果
- **职责分离实现**：任务管理功能按职责清晰分离，每个子模块职责单一
- **架构解耦**：消除UI状态与任务控制的紧耦合关系
- **标准化接口**：提供统一的任务管理API，便于扩展和维护
- **向后兼容**：通过适配器模式确保现有代码无缝工作
- **可扩展性增强**：新架构支持更灵活的任务类型和控制模式

### 风险评估
- **架构重构风险**: 中 - 涉及多个模块的重构，但通过适配器确保兼容性
- **测试覆盖风险**: 低 - 新模块从设计之初就考虑测试，测试覆盖完整
- **迁移风险**: 低 - 支持渐进式迁移，不强制一次性改变所有代码

### 成功指标
- 独立task_manager模块成功创建，职责清晰分离
- 现有所有任务控制功能正常工作，向后兼容100%
- 新模块测试覆盖率达到90%以上
- 代码架构评审通过，符合职责分离原则
- 性能测试通过，新架构不引入性能回退
