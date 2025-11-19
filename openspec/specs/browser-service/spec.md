# Browser Service Specification

## Purpose
浏览器服务提供统一的浏览器启动、连接和管理能力，支持自动启动和连接两种模式，确保扩展和登录态的完整保留。
## Requirements
### Requirement: 浏览器初始化
系统 SHALL 提供浏览器服务的初始化功能。

#### Scenario: 基础初始化
- **WHEN** 用户创建浏览器服务实例
- **THEN** 系统应成功初始化浏览器服务
- **AND** 准备好浏览器驱动

---

### Requirement: 浏览器管理
系统 SHALL 提供浏览器的启动和关闭功能。

#### Scenario: 启动浏览器
- **WHEN** 用户调用启动浏览器方法
- **THEN** 系统应成功启动浏览器
- **AND** 返回浏览器实例

#### Scenario: 关闭浏览器
- **WHEN** 用户调用关闭浏览器方法
- **THEN** 系统应成功关闭浏览器
- **AND** 释放相关资源

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

### Requirement: 配置管理
系统 SHALL 从统一配置中读取浏览器启动参数，支持启动模式和连接模式。

**Previous Behavior**:
- 强制要求 `connect_to_existing = True`
- 不支持启动模式配置

**New Behavior**:
- 自动设置 `connect_to_existing`（根据检测结果）
- 支持 `headless` 模式配置
- 支持 `browser_type` 配置（edge/chrome）
- 支持 `debug_port` 配置

#### Scenario: Headless 模式启动
- **WHEN** 配置文件设置 `headless: true`
- **THEN** 系统应以 headless 模式启动浏览器
- **AND** 不显示浏览器窗口

#### Scenario: 使用默认配置
- **WHEN** 配置文件未设置 headless
- **THEN** 系统应使用默认值 `headless=False`
- **AND** 以正常模式启动浏览器

---

### Requirement: 错误处理
系统 SHALL 提供清晰的错误信息和解决方案，不再要求用户手动启动浏览器。

**Previous Behavior**:
- 报错："未检测到运行中的浏览器，请手动启动"

**New Behavior**:
- 连接失败时提供解决方案
- 启动失败时提供解决方案
- 不再要求手动启动浏览器

#### Scenario: 连接失败
- **WHEN** 检测到浏览器运行但 CDP 端口不可用
- **THEN** 系统应输出连接失败错误
- **AND** 提供解决方案："确保浏览器的调试端口 9222 已开启"
- **AND** 退出程序

#### Scenario: 启动失败
- **WHEN** 浏览器启动失败
- **THEN** 系统应输出启动失败错误
- **AND** 提供解决方案："请检查浏览器是否已正确安装"
- **AND** 退出程序

---

### Requirement: Profile 锁定处理
系统 SHALL 检测 Profile 是否被占用，并提示用户关闭现有浏览器。

**Rationale**:
- Chromium 不允许同一个 Profile 被多个进程同时使用
- 必须使用正确的用户数据（有登录态的 Profile）
- 不使用其他 Profile 或临时 Profile，确保扩展和登录态完整

#### Scenario: Profile 被占用
- **WHEN** 检测到 Profile 正在被其他进程使用
- **THEN** 系统应提示用户："检测到浏览器 Profile 正在被使用，请关闭所有 Edge/Chrome 浏览器窗口，然后重新运行脚本"
- **AND** 退出程序

#### Scenario: Profile 可用
- **WHEN** 检测到 Profile 未被占用
- **THEN** 系统应使用该 Profile 启动浏览器
- **AND** 保留所有扩展和登录态

---

### Requirement: CDP 调试端口支持
系统 SHALL 在启动模式下自动开启 CDP 调试端口，方便后续连接和调试。

**Rationale**:
- 支持多个脚本连接同一浏览器实例
- 方便手动调试和检查
- 与连接模式保持一致

#### Scenario: 启动时开启 CDP 端口
- **WHEN** 系统以启动模式启动浏览器
- **THEN** 系统应自动添加参数 `--remote-debugging-port=9222`
- **AND** CDP 调试端口应可用于连接

#### Scenario: CDP 端口被占用
- **WHEN** 调试端口 9222 已被占用
- **THEN** 系统应输出错误："调试端口 9222 已被占用"
- **AND** 提供解决方案
- **AND** 退出程序

---

### Requirement: 浏览器类型支持
系统 SHALL 支持主流浏览器 Chrome 和 Edge。

**Supported Browsers**:
- Chrome: 通过 Chromium 内核
- Edge: 通过 `channel='msedge'` 参数

**Platform Support**:
- macOS: Chrome + Edge
- Windows: Chrome + Edge
- Linux: Chrome only

#### Scenario: 使用 Edge 浏览器
- **WHEN** 配置文件设置 `browser_type: "edge"`
- **THEN** 系统应启动 Microsoft Edge 浏览器
- **AND** 使用 `channel='msedge'` 参数

#### Scenario: 使用 Chrome 浏览器
- **WHEN** 配置文件设置 `browser_type: "chrome"`
- **THEN** 系统应启动 Google Chrome 浏览器
- **AND** 使用 Chromium 内核

#### Scenario: Linux 平台使用 Edge
- **WHEN** 在 Linux 平台配置 `browser_type: "edge"`
- **THEN** 系统应输出错误："Edge 不支持 Linux 平台"
- **AND** 提示使用 Chrome

---

### Requirement: 利用现有实现
系统 SHALL 利用现有的 `PlaywrightBrowserDriver._launch_browser()` 方法，不重复实现。

**Rationale**:
- `PlaywrightBrowserDriver._launch_browser()` 已实现所有必需功能
- 跨平台支持、多浏览器支持、Profile 处理、扩展支持、反检测
- 代码修改量 < 50 行

#### Scenario: 调用现有实现
- **WHEN** 配置 `connect_to_existing=False`
- **THEN** 系统应调用 `SimplifiedPlaywrightBrowserDriver.initialize()`
- **AND** `initialize()` 应调用 `_launch_browser()`
- **AND** 使用现有的成熟实现

#### Scenario: 不重复实现
- **WHEN** 需要启动浏览器
- **THEN** 系统不应创建新的启动逻辑
- **AND** 应移除阻止调用 `_launch_browser()` 的限制
- **AND** 让现有代码发挥作用

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

