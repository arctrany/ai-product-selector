# CLI 模块适配任务管理器规范

## ADDED Requirements

### Requirement: CLI层使用独立TaskManager
CLI模块 SHALL 重构以使用新的独立 task_manager 模块，替代原有分散的任务控制功能，实现清晰的职责分离。

#### Scenario: TaskController重构适配
- **WHEN** CLI的TaskController初始化时
- **THEN** 创建并使用 task_manager.TaskManager 实例而非直接管理任务状态
- **AND** 通过统一接口进行任务创建、启动、暂停、恢复、停止操作

#### Scenario: 状态管理职责分离
- **WHEN** CLI需要获取任务状态时
- **THEN** 通过TaskManager接口查询任务状态，而非直接访问内部状态变量
- **AND** UI状态管理器专注于界面状态，任务状态由TaskManager统一管理

#### Scenario: 适配器兼容现有接口
- **WHEN** 现有CLI代码调用原TaskController方法时
- **THEN** 通过适配器模式保持接口兼容性，内部委托给新的TaskManager
- **AND** 现有CLI调用代码无需修改即可正常工作

### Requirement: 增强的CLI命令处理
CLI模块 SHALL 提供增强的命令处理能力，利用新TaskManager的丰富功能提升用户体验。

#### Scenario: 任务状态查询命令
- **WHEN** 用户执行任务状态查询命令时
- **THEN** 通过TaskManager获取详细的任务信息：状态、进度、预估时间、统计数据
- **AND** 以用户友好的格式展示任务状态和进度信息

#### Scenario: 批量任务控制命令
- **WHEN** 用户执行批量控制命令时
- **THEN** 支持同时控制多个任务的启动、暂停、恢复、停止操作
- **AND** 提供批量操作的进度反馈和结果汇总

#### Scenario: 任务历史和统计命令
- **WHEN** 用户查看任务历史时
- **THEN** 展示任务执行历史、成功率、平均执行时间等统计信息
- **AND** 支持按时间、状态、类型等条件过滤任务历史
