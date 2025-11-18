# Browser Service Specification

## Overview
浏览器服务规范定义了浏览器启动、连接、管理的核心行为。

---

## MODIFIED Requirements

### REQ-BS-001: 浏览器启动策略
**Priority**: P0  
**Status**: Modified

**Description**:
系统应支持智能浏览器启动策略，根据运行状态自动选择连接或启动。

**Previous Behavior**:
- 检测到没有运行中的浏览器 → 报错退出
- 要求用户手动启动浏览器

**New Behavior**:
- 检测到有运行中的浏览器 → 连接
- 检测到没有运行中的浏览器 → 自动启动

**Scenarios**:

#### Scenario 1: 有运行中的浏览器
```
GIVEN 用户已手动启动浏览器并开启调试端口 9222
WHEN 系统初始化浏览器服务
THEN 系统应连接到已运行的浏览器
AND 保留用户的登录态和会话
AND 输出日志 "✅ 检测到现有浏览器实例在端口 9222"
```

#### Scenario 2: 没有运行中的浏览器
```
GIVEN 没有运行中的浏览器
WHEN 系统初始化浏览器服务
THEN 系统应自动启动浏览器
AND 使用智能选择的 Profile
AND 开启调试端口
AND 输出日志 "🚀 自动启动浏览器: Profile=xxx, Port=9222"
```

#### Scenario 3: 启动失败
```
GIVEN 没有运行中的浏览器
AND 浏览器可执行文件不存在
WHEN 系统尝试启动浏览器
THEN 系统应输出详细错误信息
AND 提供解决方案
AND 退出程序（不重试）
```

---

### REQ-BS-002: Profile 智能选择
**Priority**: P0  
**Status**: Modified

**Description**:
系统应根据登录态和使用历史智能选择最佳 Profile。

**Previous Behavior**:
- 使用固定的 Profile（通常是 Default）
- 不检查登录态

**New Behavior**:
- 扫描所有 Profile
- 检查登录态
- 选择最佳 Profile（最近使用 + 满足登录态）

**Scenarios**:

#### Scenario 1: 有满足登录态的 Profile
```
GIVEN 配置要求登录 ["seerfar.cn", "www.maozierp.com"]
AND Profile 1 满足所有登录态要求
AND Profile 2 只满足部分登录态要求
AND Profile 1 是最近使用的
WHEN 系统选择 Profile
THEN 系统应选择 Profile 1
AND 输出日志 "✅ 选择 Profile: Profile 1 (满足所有登录态要求)"
```

#### Scenario 2: 无满足登录态的 Profile
```
GIVEN 配置要求登录 ["seerfar.cn", "www.maozierp.com"]
AND 所有 Profile 都不满足登录态要求
AND Default 是最近使用的
WHEN 系统选择 Profile
THEN 系统应选择 Default
AND 输出警告日志 "⚠️ 未找到满足登录态要求的 Profile，使用 Default"
AND 输出提示 "💡 请登录以下域名: seerfar.cn, www.maozierp.com"
```

#### Scenario 3: 多个 Profile 都满足登录态
```
GIVEN 配置要求登录 ["seerfar.cn"]
AND Profile 1 和 Profile 2 都满足登录态要求
AND Profile 2 是最近使用的
WHEN 系统选择 Profile
THEN 系统应选择 Profile 2（最近使用优先）
```

---

### REQ-BS-003: 浏览器配置管理
**Priority**: P0  
**Status**: Modified

**Description**:
系统应从统一的配置中读取浏览器启动参数。

**Previous Behavior**:
- 配置分散在多处
- 缺少启动相关配置

**New Behavior**:
- 从 `config.browser` 读取所有配置
- 支持完整的启动参数

**Configuration Schema**:
```json
{
  "browser": {
    "browser_type": "edge",           // 浏览器类型
    "headless": false,                // 是否无头模式
    "window_width": 1920,             // 窗口宽度
    "window_height": 1080,            // 窗口高度
    "timeout_seconds": 30,            // 超时时间
    "max_retries": 3,                 // 最大重试次数
    "required_login_domains": [       // 必需登录的域名
      "seerfar.cn",
      "www.maozierp.com"
    ],
    "debug_port": 9222                // CDP 调试端口
  }
}
```

**Scenarios**:

#### Scenario 1: 读取完整配置
```
GIVEN 配置文件包含完整的 browser 配置
WHEN 系统初始化浏览器服务
THEN 系统应读取所有配置项
AND 使用配置的值启动浏览器
```

#### Scenario 2: 使用默认配置
```
GIVEN 配置文件缺少某些 browser 配置项
WHEN 系统初始化浏览器服务
THEN 系统应使用默认值填充缺失项
AND 输出日志说明使用了默认值
```

---

## ADDED Requirements

### REQ-BS-004: 浏览器进程管理
**Priority**: P1  
**Status**: New

**Description**:
系统应正确管理启动的浏览器进程生命周期。

**Scenarios**:

#### Scenario 1: 启动的浏览器应被记录
```
GIVEN 系统自动启动了浏览器
WHEN 浏览器启动成功
THEN 系统应记录浏览器进程 PID
AND 记录是否为自己启动的浏览器
```

#### Scenario 2: 关闭自己启动的浏览器
```
GIVEN 系统自动启动了浏览器
WHEN 系统关闭浏览器服务
THEN 系统应终止浏览器进程
AND 清理相关资源
```

#### Scenario 3: 不关闭连接的浏览器
```
GIVEN 系统连接到已运行的浏览器
WHEN 系统关闭浏览器服务
THEN 系统应只断开连接
AND 不终止浏览器进程
```

---

### REQ-BS-005: 跨平台支持
**Priority**: P0  
**Status**: New

**Description**:
系统应支持在 macOS、Windows、Linux 上启动浏览器。

**Scenarios**:

#### Scenario 1: macOS 平台
```
GIVEN 系统运行在 macOS 上
AND 浏览器类型为 edge
WHEN 系统启动浏览器
THEN 系统应使用路径 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
AND 使用 macOS 特定的启动参数
```

#### Scenario 2: Windows 平台
```
GIVEN 系统运行在 Windows 上
AND 浏览器类型为 edge
WHEN 系统启动浏览器
THEN 系统应使用路径 "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
AND 使用 Windows 特定的启动参数
```

#### Scenario 3: Linux 平台
```
GIVEN 系统运行在 Linux 上
AND 浏览器类型为 edge
WHEN 系统启动浏览器
THEN 系统应使用路径 "/usr/bin/microsoft-edge"
AND 使用 Linux 特定的启动参数
```

---

### REQ-BS-006: 启动后验证
**Priority**: P1  
**Status**: New

**Description**:
系统应在浏览器启动后验证登录态并提供友好提示。

**Scenarios**:

#### Scenario 1: 登录态满足要求
```
GIVEN 浏览器启动成功
AND 选择的 Profile 满足所有登录态要求
WHEN 系统验证登录态
THEN 系统应输出日志 "✅ 登录态验证通过"
AND 继续执行
```

#### Scenario 2: 登录态不满足要求
```
GIVEN 浏览器启动成功
AND 选择的 Profile 不满足登录态要求
WHEN 系统验证登录态
THEN 系统应输出警告 "⚠️ 部分域名未登录"
AND 列出需要登录的域名
AND 继续执行（不中断）
```

---

### REQ-BS-007: 错误处理和提示
**Priority**: P1  
**Status**: New

**Description**:
系统应提供清晰的错误信息和解决方案。

**Scenarios**:

#### Scenario 1: 浏览器可执行文件不存在
```
GIVEN 浏览器可执行文件不存在
WHEN 系统尝试启动浏览器
THEN 系统应输出错误 "❌ 浏览器可执行文件不存在"
AND 输出文件路径
AND 提供解决方案 "💡 请安装 Microsoft Edge 浏览器"
AND 退出程序
```

#### Scenario 2: Profile 被占用
```
GIVEN 选择的 Profile 正被其他进程使用
WHEN 系统尝试启动浏览器
THEN 系统应输出错误 "❌ Profile 被占用"
AND 提供解决方案 "💡 请关闭其他使用该 Profile 的浏览器实例"
AND 退出程序
```

#### Scenario 3: CDP 连接超时
```
GIVEN 浏览器启动成功
AND CDP 端口在 30 秒内未响应
WHEN 系统尝试连接 CDP
THEN 系统应输出错误 "❌ CDP 连接超时"
AND 提供解决方案 "💡 请检查防火墙设置或增加超时时间"
AND 退出程序
```

---

## Implementation Notes

### Profile 登录态检查方法
1. 读取 Profile 目录下的 Cookies 文件
2. 检查是否存在 required_login_domains 的 Cookie
3. 验证 Cookie 是否过期

### 浏览器启动参数
```bash
# 基础参数
--remote-debugging-port=9222
--user-data-dir=/path/to/profile
--profile-directory=Profile 1

# headless 模式
--headless=new

# 窗口大小
--window-size=1920,1080

# 禁用扩展（可选）
--disable-extensions

# 其他优化参数
--no-first-run
--no-default-browser-check
--disable-background-networking
```

### 跨平台路径处理
- 使用 `pathlib.Path` 处理路径
- 使用 `platform.system()` 检测操作系统
- 使用字典映射浏览器可执行文件路径

### 进程管理
- 使用 `subprocess.Popen()` 启动进程
- 记录进程 PID
- 使用 `process.terminate()` 或 `process.kill()` 终止进程
- 使用 `atexit` 注册清理函数

---

## Testing Requirements

### Unit Tests
- Profile 扫描和选择逻辑
- 登录态检查逻辑
- 启动命令生成逻辑
- 配置读取和验证

### Integration Tests
- 完整的启动流程
- 连接流程
- 错误处理流程
- 跨平台兼容性

### Manual Tests
- 不同操作系统上的实际启动
- 不同浏览器的支持
- 各种错误场景的提示

---

## Migration Guide

### For Users
无需任何操作，系统会自动处理：
- 有运行中的浏览器 → 自动连接（原有行为）
- 没有运行中的浏览器 → 自动启动（新功能）

### For Developers
如果有自定义的浏览器启动逻辑，需要：
1. 移除手动启动浏览器的代码
2. 依赖系统的自动启动功能
3. 配置 `required_login_domains` 以启用智能 Profile 选择

---

## Related Specifications
- [Config Management](../config-management/spec.md) - 配置管理规范
- [Browser Service](../../specs/browser-service/spec.md) - 浏览器服务规范（原有）
