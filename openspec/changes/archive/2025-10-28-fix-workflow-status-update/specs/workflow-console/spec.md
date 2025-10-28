## MODIFIED Requirements

### Requirement: Console Interface Layout
工作流控制台界面SHALL提供简洁直观的用户体验，专注于核心的工作流监控和控制功能，并通过WebSocket实现实时状态更新。

#### Scenario: 用户访问控制台页面
- **WHEN** 用户访问工作流控制台页面
- **THEN** 系统SHALL显示单一的执行日志界面
- **AND** 界面SHALL包含工作流控制按钮（开始任务、停止流程）
- **AND** 界面SHALL包含输入参数配置区域
- **AND** 界面SHALL包含执行状态显示区域
- **AND** 系统SHALL建立WebSocket连接以接收实时状态更新

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

#### Scenario: WebSocket连接建立
- **WHEN** 用户访问控制台页面
- **THEN** 系统SHALL自动建立WebSocket连接到 `/api/ws/runs/{thread_id}/events`
- **AND** 连接建立后SHALL立即请求当前工作流状态
- **AND** 如果WebSocket连接失败SHALL降级到HTTP轮询模式

#### Scenario: 实时状态更新
- **WHEN** 工作流状态发生变化（启动、运行中、完成、失败）
- **THEN** 工作流引擎SHALL通过WebSocket推送状态更新消息
- **AND** 前端SHALL接收状态更新并立即更新UI显示
- **AND** 状态显示区域SHALL反映最新的工作流状态

#### Scenario: WebSocket重连机制
- **WHEN** WebSocket连接意外断开
- **THEN** 系统SHALL自动尝试重新连接
- **AND** 重连成功后SHALL重新请求当前状态
- **AND** 重连失败时SHALL显示连接状态提示

## ADDED Requirements

### Requirement: WebSocket状态推送机制
工作流引擎SHALL在关键状态变更时主动推送状态更新到WebSocket连接。

#### Scenario: 工作流启动状态推送
- **WHEN** 工作流成功启动
- **THEN** 工作流引擎SHALL推送包含thread_id和状态"running"的消息
- **AND** 消息SHALL包含时间戳和状态详情

#### Scenario: 工作流完成状态推送
- **WHEN** 工作流执行完成
- **THEN** 工作流引擎SHALL推送包含最终状态的消息
- **AND** 消息SHALL包含执行结果和完成时间

#### Scenario: 工作流错误状态推送
- **WHEN** 工作流执行过程中发生错误
- **THEN** 工作流引擎SHALL推送包含错误信息的状态消息
- **AND** 消息SHALL包含错误类型和错误详情