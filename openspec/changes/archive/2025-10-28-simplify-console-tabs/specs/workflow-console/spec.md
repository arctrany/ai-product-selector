## ADDED Requirements

### Requirement: Console Interface Layout
工作流控制台界面SHALL提供简洁直观的用户体验，专注于核心的工作流监控和控制功能。

#### Scenario: 用户访问控制台页面
- **WHEN** 用户访问工作流控制台页面
- **THEN** 系统SHALL显示单一的执行日志界面
- **AND** 界面SHALL包含工作流控制按钮（开始任务、停止流程）
- **AND** 界面SHALL包含输入参数配置区域
- **AND** 界面SHALL包含执行状态显示区域

#### Scenario: 实时日志显示
- **WHEN** 工作流正在执行
- **THEN** 系统SHALL在执行日志区域实时显示日志信息
- **AND** 日志SHALL包含时间戳、级别和消息内容
- **AND** 日志区域SHALL自动滚动到最新消息

#### Scenario: 工作流控制操作
- **WHEN** 用户点击工作流控制按钮
- **THEN** 系统SHALL执行相应的工作流操作（启动、暂停、停止）
- **AND** 操作结果SHALL在日志中显示
- **AND** 按钮状态SHALL根据工作流状态动态更新