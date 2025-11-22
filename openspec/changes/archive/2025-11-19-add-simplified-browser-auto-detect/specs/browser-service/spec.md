# browser-service Spec Delta

## MODIFIED Requirements

### Requirement: 浏览器启动策略
系统 SHALL 支持智能浏览器启动策略，SimplifiedBrowserService 应具备自动检测能力。

**Previous Behavior**:
- SimplifiedBrowserService 被动接收配置
- 必须由上层服务（如 XuanpingBrowserService）决定启动/连接模式
- 直接使用 SimplifiedBrowserService 无法实现自动切换

**New Behavior**:
- SimplifiedBrowserService 主动检测浏览器状态
- 自动决定启动/连接模式
- 与 XuanpingBrowserService 行为一致

#### Scenario: SimplifiedBrowserService 自动检测浏览器
- **WHEN** SimplifiedBrowserService 初始化时
- **THEN** 系统应自动检测浏览器是否运行
- **AND** 根据检测结果自动设置 `connect_to_existing`
- **AND** 输出相应的日志信息

#### Scenario: 检测到浏览器运行
- **WHEN** 检测到浏览器在端口 9222 运行且 CDP 端点可用
- **THEN** 系统应设置 `connect_to_existing = "http://localhost:9222"`
- **AND** 输出日志 "🔗 检测到现有浏览器，将连接到端口 9222"
- **AND** 使用连接模式

#### Scenario: 未检测到浏览器
- **WHEN** 检测到浏览器未运行或 CDP 端点不可用
- **THEN** 系统应设置 `connect_to_existing = False`
- **AND** 输出日志 "🚀 未检测到浏览器，将自动启动"
- **AND** 使用启动模式

#### Scenario: 手动配置优先级
- **WHEN** 用户手动配置了 `connect_to_existing`
- **THEN** 系统应优先使用手动配置
- **AND** 不执行自动检测
- **AND** 保持向后兼容

---

## ADDED Requirements

### Requirement: 浏览器检测方法
SimplifiedBrowserService SHALL 提供浏览器检测方法，验证浏览器是否运行且 CDP 端点可用。

#### Scenario: 端口检查
- **WHEN** 调用 `_check_existing_browser(debug_port)`
- **THEN** 系统应检查指定端口是否被占用
- **AND** 使用 socket 连接测试端口可用性
- **AND** 设置 1 秒超时

#### Scenario: CDP 端点验证
- **WHEN** 端口被占用
- **THEN** 系统应访问 `/json/version` 端点
- **AND** 验证响应中包含 `webSocketDebuggerUrl` 字段
- **AND** 设置 2 秒超时
- **AND** 返回验证结果

#### Scenario: 检测失败处理
- **WHEN** 端口未被占用或 CDP 端点不可用
- **THEN** 系统应返回 `False`
- **AND** 记录 debug 级别日志
- **AND** 不抛出异常

---

### Requirement: 配置传递增强
SimplifiedBrowserService SHALL 确保 `debug_port` 配置正确传递。

#### Scenario: 传递调试端口配置
- **WHEN** 准备浏览器配置时
- **THEN** 系统应从 `browser_config` 中读取 `debug_port`
- **AND** 如果未配置则使用默认值 9222
- **AND** 将端口号传递给检测方法

#### Scenario: 配置默认值
- **WHEN** `browser_config` 中没有 `debug_port`
- **THEN** 系统应使用默认端口 9222
- **AND** 记录使用默认值的日志

---

### Requirement: 行为一致性
SimplifiedBrowserService 和 XuanpingBrowserService SHALL 具有一致的浏览器检测行为。

#### Scenario: 检测逻辑一致
- **WHEN** 两个服务检测同一浏览器实例
- **THEN** 检测结果应完全一致
- **AND** 使用相同的检测方法
- **AND** 使用相同的超时设置

#### Scenario: 日志输出一致
- **WHEN** 检测到浏览器或未检测到浏览器
- **THEN** 两个服务应输出相同格式的日志
- **AND** 使用相同的 emoji 标识
- **AND** 提供相同的信息内容
