## MODIFIED Requirements

### Requirement: Console Interface Layout
工作流控制台界面SHALL提供简洁直观的用户体验，专注于核心的工作流监控和控制功能。

#### Scenario: 用户访问控制台页面
- **WHEN** 用户访问工作流控制台页面
- **THEN** 系统SHALL显示单一的执行日志界面
- **AND** 界面SHALL包含工作流控制按钮（开始任务、停止流程）
- **AND** 界面SHALL在页面右上角显示紧凑的执行状态卡片
- **AND** 界面SHALL不包含输入数据配置区域

#### Scenario: 实时日志显示
- **WHEN** 工作流正在执行
- **THEN** 系统SHALL在执行日志区域实时显示日志信息
- **AND** 日志SHALL包含时间戳、级别和消息内容
- **AND** 日志区域SHALL自动滚动到最新消息

#### Scenario: 工作流控制操作
- **WHEN** 用户点击工作流控制按钮
- **THEN** 系统SHALL执行相应的工作流操作（启动、暂停、停止）
- **AND** 操作结果SHALL在日志中显示
- **AND** 按钮状态SHALL根据工作流状态动态更新，无闪烁或异常行为

## ADDED Requirements

### Requirement: Button State Management
工作流控制按钮SHALL提供流畅的状态切换体验，确保用户操作的直观性和一致性。

#### Scenario: 开始任务按钮切换
- **WHEN** 用户点击"开始任务"按钮且工作流成功启动
- **THEN** 按钮SHALL平滑切换为"暂停任务"状态
- **AND** 切换过程SHALL无闪烁或视觉异常
- **AND** 按钮颜色SHALL从绿色变为橙色

#### Scenario: 暂停任务按钮切换
- **WHEN** 用户点击"暂停任务"按钮且工作流成功暂停
- **THEN** 按钮SHALL平滑切换为"开始任务"状态
- **AND** 切换过程SHALL无闪烁或视觉异常
- **AND** 按钮颜色SHALL从橙色变为绿色

### Requirement: Real-time Status Display
执行状态区域SHALL提供实时准确的工作流状态信息，采用现代化的视觉设计。

#### Scenario: 状态实时更新
- **WHEN** 在flow级别的控制态页面中，点击“开始任务”，工作流状态发生变化
- **THEN** 执行状态区域SHALL立即反映最新状态, 当任务开始了，SHAL立即更新为"运行中"，执行完毕SHAL"已完成"，如果错误"SHALL更新为"失败"
- **AND** 状态更新SHALL通过WebSocket连接实现
- **AND** 连接断开时SHALL显示连接状态指示

#### Scenario: 状态卡片布局
- **WHEN** 用户查看控制台页面
- **THEN** 执行状态SHALL实时显示
- **AND** 状态卡片SHALL采用现代化的视觉布局
- **AND** 状态卡片SHALL包含当前状态、最后执行时间和连接状态

### Requirement: Simplified Control Interface
控制界面SHALL保持简洁性，移除不必要的功能元素，专注于核心工作流操作。

#### Scenario: 简化按钮组
- **WHEN** 用户查看控制按钮区域
- **THEN** 界面SHALL仅显示"开始任务/暂停任务"和"停止流程"按钮
- **AND** 界面SHALL不包含"触发流程"按钮
- **AND** 按钮布局SHALL紧凑且易于操作

#### Scenario: 移除输入区域
- **WHEN** 用户查看控制台页面
- **THEN** 界面SHALL不包含输入数据配置区域
- **AND** 页面布局SHALL更加简洁
- **AND** 所有空间SHALL专注于日志显示和核心控制功能