# CLI 任务控制规范

## MODIFIED Requirements

### Requirement: 统一任务控制器
TaskController SHALL 整合TaskExecutionController的功能，提供统一的任务控制接口，去除架构冗余。

#### Scenario: 整合控制信号管理
- **WHEN** EnhancedTaskController接收暂停信号
- **THEN** 通过ui_state_manager统一管理状态
- **AND** 所有控制点检查都响应统一的控制信号

#### Scenario: 整合进度回调机制
- **WHEN** 任务报告进度更新
- **THEN** 通过EnhancedTaskController统一处理进度回调
- **AND** 避免TaskController和TaskExecutionController的重复回调机制

#### Scenario: 删除冗余状态管理
- **WHEN** 系统启动后
- **THEN** 只保留ui_state_manager作为唯一状态管理机制
- **AND** TaskExecutionController的状态信号机制和TaskControlInterface的状态文件机制被移除

### Requirement: 细粒度循环控制
CLI层SHALL支持店铺级和商品级的细粒度循环控制，允许在任意循环层级进行暂停、恢复、停止操作。

#### Scenario: 店铺循环控制点
- **WHEN** GoodStoreSelector在处理店铺循环时调用_check_task_control("处理店铺_{i+1}_{store_id}")
- **THEN** 系统检查当前控制状态并响应暂停/恢复/停止信号
- **AND** 可以在任意店铺处理前暂停整个任务

#### Scenario: 商品循环控制点
- **WHEN** 在处理商品循环时调用_check_task_control("处理商品_{j+1}_{product_id}")
- **THEN** 系统检查控制状态并响应控制信号
- **AND** 可以在任意商品处理前暂停任务
