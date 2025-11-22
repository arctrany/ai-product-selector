# Browser Service Specification

## ADDED Requirements

### Requirement: 浏览器启动策略
系统 SHALL 支持智能浏览器启动策略，根据运行状态自动选择连接或启动模式。

**Previous Behavior**:
- 检测到没有运行中的浏览器时直接报错退出
- 强制要求用户手动启动浏览器

**New Behavior**:
- 优先级 1：启动模式（浏览器未运行）- 自动启动新浏览器
- 优先级 2：连接模式（浏览器已运行）- 连接到现有浏览器

#### Scenario: 连接到已运行的浏览器
- **WHEN** 检测到浏览器已运行且开启调试端口 9222
- **THEN** 系统应连接到已运行的浏览器
- **AND** 完全保留扩展和登录态
- **AND** 输出日志 "🔗 检测到现有浏览器，将连接到端口 9222"

#### Scenario: 自动启动新浏览器
- **WHEN** 检测到没有运行中的浏览器
- **THEN** 系统应自动启动新浏览器
- **AND** 使用有登录态的 Profile
- **AND** 自动开启 CDP 调试端口 9222
- **AND** 输出日志 "🚀 未检测到浏览器，将自动启动"

#### Scenario: 浏览器启动失败
- **WHEN** 浏览器启动失败（如可执行文件不存在）
- **THEN** 系统应输出详细错误信息
- **AND** 提供解决方案
- **AND** 退出程序

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
